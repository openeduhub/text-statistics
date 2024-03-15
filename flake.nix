{
  description = "Packaging for the text statistics service";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    nix-filter.url = "github:numtide/nix-filter";
    openapi-checks.url = "github:openeduhub/nix-openapi-checks";
    nlprep.url = "github:openeduhub/nlprep";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    let
      nix-filter = self.inputs.nix-filter.lib;

      # declare the python packages used for building & developing
      python-packages-build = py-pkgs:
        with py-pkgs; [
          pyphen
          fastapi
          pydantic
          uvicorn
          (self.inputs.nlprep.lib.nlprep py-pkgs)
        ];

      python-packages-devel = py-pkgs:
        with py-pkgs; [
          black
          pyflakes
          isort
          ipython
        ]
        ++ (python-packages-build py-pkgs);

      # declare how the python package shall be built
      get-python-package = py-pkgs: py-pkgs.buildPythonPackage rec {
        pname = "text-statistics";
        version = "1.1.0";
        src = nix-filter {
          root = self;
          include = [ "src" ./setup.py ./requirements.txt ];
          exclude = [ (nix-filter.matchExt "pyc") ];
        };
        propagatedBuildInputs = (python-packages-build py-pkgs);
        # check that the package can be imported
        pythonImportsCheck = [ "text_statistics" ];
        # the package does not have any tests
        doCheck = false;
        doInstallCheck = false;
      };

      # convert the package built above to an application
      # a python application is essentially identical to a python package,
      # but without the importable modules. as a result, it is smaller.
      get-python-app = py-pkgs: py-pkgs.toPythonApplication (get-python-package py-pkgs);
    in
    {
      # define an overlay to add text-statistics to nixpkgs
      overlays.default = (final: prev: {
        inherit (self.packages.${final.system}) text-statistics;
      });
      lib = {
        text-statistics = get-python-package;
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        # a specific build for a specific system
        pkgs = nixpkgs.legacyPackages.${system};
        openapi-checks = self.inputs.openapi-checks.lib.${system};
        python = pkgs.python3;
        python-app = get-python-app python.pkgs;

        # export the openapi schema
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

      in
      {
        packages = {
          inherit openapi-schema;
          text-statistics = python-app;
          docker = docker-img;
          default = python-app;
        } // (nixpkgs.lib.optionalAttrs
          # only build docker images on linux systems
          (system == "x86_64-linux" || system == "aarch64-linux")
          {
            docker = docker-img;
          });
        devShells.default = pkgs.mkShell {
          buildInputs = [
            (python.withPackages python-packages-devel)
            # python language server
            pkgs.nodePackages.pyright
          ];
        };
        checks = { } // (nixpkgs.lib.optionalAttrs
          # only run the VM checks on linux systems
          (system == "x86_64-linux" || system == "aarch64-linux")
          {
            test-service = (openapi-checks.test-service {
              service-bin = "${python-app}/bin/${python-app.pname}";
              service-port = 8080;
              openapi-domain = "/openapi.json";
              memory-size = 2 * 1024;
            });
          });
      });
}
