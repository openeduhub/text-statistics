{
  description = "Packaging for the text statistics service";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.05";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    openapi-checks.url = "/home/yusu/work/ITsJointly/projects/openapi-checks";
  };

  outputs = { self, nixpkgs, nixpkgs-unstable, flake-utils, ... }:
    {
      # define an overlay to add text-statistics to nixpkgs
      overlays.default = (final: prev: {
        inherit (self.packages.${final.system}) text-statistics;
      });
    } //
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" ] (system:
      let
        pkgs = import nixpkgs {inherit system;};
        pkgs-unstable = import nixpkgs-unstable {inherit system;};
        openapi-checks = self.inputs.openapi-checks.lib.${system};
        python = pkgs.python310;

        # declare the python packages used for building & developing
        python-packages-build = python-packages:
          with python-packages; [ pyphen
                                  nltk
                                  fastapi
                                  pydantic
                                  uvicorn
                                ];

        python-packages-devel = python-packages:
          with python-packages; [ black
                                  pyflakes
                                  isort
                                  ipython
                                ]
          ++ (python-packages-build python-packages);
        
        # download nltk-punkt, an external requirement for nltk
        nltk-punkt = pkgs.fetchzip {
          url = "https://github.com/nltk/nltk_data/raw/5db857e6f7df11eabb5e5665836db9ec8df07e28/packages/tokenizers/punkt.zip";
          hash = "sha256-SKZu26K17qMUg7iCFZey0GTECUZ+sTTrF/pqeEgJCos=";
        };

        # declare how the python package shall be built
        python-package = python.pkgs.buildPythonPackage rec {
          pname = "text-statistics";
          version = "1.0.4";
          src = self;
          propagatedBuildInputs = (python-packages-build python.pkgs);
          # put nltk-punkt into a directory
          preBuild = ''
            mkdir -p $out/lib/nltk_data/tokenizers/punkt
            cp -r ${nltk-punkt.out}/* $out/lib/nltk_data/tokenizers/punkt
          '';
          # make the created folder discoverable for NLTK
          makeWrapperArgs = ["--set NLTK_DATA $out/lib/nltk_data"];
        };

        # convert the package built above to an application
        # a python application is essentially identical to a python package,
        # but without the importable modules. as a result, it is smaller.
        python-app = python.pkgs.toPythonApplication python-package;

        # declare how the docker image shall be built
        docker-img = pkgs.dockerTools.buildImage rec {
          name = python-app.pname;
          tag = python-app.version;
          config = {
            Cmd = [ "${python-app}/bin/text-statistics" ];
          };
        };

      in {
        packages = rec {
          text-statistics = python-app;
          docker = docker-img;
          default = text-statistics;
        };
        devShells.default = pkgs.mkShell {
          buildInputs = [
            (python-packages-devel python.pkgs)
            # python language server
            pkgs.nodePackages.pyright
          ];
        };
        checks = {
          openapi-check = (
            openapi-checks.openapi-valid {
              serviceBin = "${self.packages.${system}.text-statistics}/bin/text-statistics";
            }
          );
        };
      }
    );
}
