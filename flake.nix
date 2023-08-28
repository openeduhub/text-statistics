{
  description = "Packaging for the text statistics service";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.05";
    flake-utils.url = "github:numtide/flake-utils";
    nix-filter.url = "github:numtide/nix-filter";
    openapi-checks.url = "github:openeduhub/nix-openapi-checks";
    nltk-data = {
      url = "github:nltk/nltk_data";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    {
      # define an overlay to add text-statistics to nixpkgs
      overlays.default = (final: prev: {
        inherit (self.packages.${final.system}) text-statistics;
      });
    } // flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };
        nix-filter = self.inputs.nix-filter.lib;
        openapi-checks = self.inputs.openapi-checks.lib.${system};
        python = pkgs.python310;

        # declare the python packages used for building & developing
        python-packages-build = python-packages:
          with python-packages; [
            pyphen
            nltk
            fastapi
            pydantic
            uvicorn
          ];

        python-packages-devel = python-packages:
          with python-packages;
          [ black pyflakes isort ipython ]
          ++ (python-packages-build python-packages);

        # unzip nltk-punkt, an external requirement for nltk
        nltk-punkt = pkgs.runCommand "nltk-punkt" {
          outpath = "tokenizers";
        } ''
          mkdir -p $out/$outpath
          ${pkgs.unzip}/bin/unzip \
            ${self.inputs.nltk-data}/packages/tokenizers/punkt.zip \
            -d $out/$outpath
        '';

        # declare how the python package shall be built
        python-package = python.pkgs.buildPythonPackage rec {
          pname = "text-statistics";
          version = "1.0.4";
          src = nix-filter {
            root = self;
            include = [ "src" ./setup.py ./requirements.txt ];
            exclude = [ (nix-filter.matchExt "pyc") ];
          };
          propagatedBuildInputs = (python-packages-build python.pkgs);
          # make nltk data discoverable during build
          NLTK_DATA = nltk-punkt.out;
          # make nltk data discoverable during runtime
          makeWrapperArgs = [ "--set NLTK_DATA $NLTK_DATA" ];
          # check that the package can be imported
          pythonImportsCheck = [ "text_statistics" ];
        };

        # convert the package built above to an application
        # a python application is essentially identical to a python package,
        # but without the importable modules. as a result, it is smaller.
        python-app = python.pkgs.toPythonApplication python-package;

        openapi-schema = pkgs.stdenv.mkDerivation {
          pname = "${python-app.pname}-openapi-schema";
          version = python-app.version;
          src = nix-filter {
            root = self;
            include = [ ./src/text_statistics/webservice.py ];
          };
          nativeBuildInputs = [ pkgs.makeWrapper python-app ];
          installPhase = ''
            mkdir $out
            ${python-app}/bin/openapi-schema \
            | ${pkgs.nodePackages.json}/bin/json \
            > $out/schema.json
          '';
        };

        # declare how the docker image shall be built
        docker-img = pkgs.dockerTools.buildImage rec {
          name = python-app.pname;
          tag = python-app.version;
          config = { Cmd = [ "${python-app}/bin/text-statistics" ]; };
        };

      in {
        packages = rec {
          inherit openapi-schema nltk-punkt;
          text-statistics = python-app;
          docker = docker-img;
          default = text-statistics;
        };
        devShells.default = pkgs.mkShell {
          buildInputs = [
            (python.withPackages python-packages-devel)
            # python language server
            pkgs.nodePackages.pyright
          ];
        };
        checks = {
          test-service = (openapi-checks.test-service {
            service-bin = "${python-app}/bin/text-statistics";
            service-port = 8080;
            openapi-domain = "openapi.json";
          });
        };
      });
}
