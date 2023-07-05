{
  description = "Basic Python Environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils = { url = "github:numtide/flake-utils"; };
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # build required packages from pypi
        charset-normalizer = with pkgs.python3Packages;
          buildPythonPackage rec {
            pname = "charset-normalizer";
            version = "3.1.0";
            src = fetchPypi {
              inherit pname version;
              sha256 = "34e0a2f9c370eb95597aae63bf85eb5e96826d81e3dcf88b8886012906f509b5";
            };
            doCheck = false;
            propagatedBuildInputs = [
            ];
          };

        htmldate = with pkgs.python3Packages;
          buildPythonPackage rec {
            pname = "htmldate";
            version = "1.4.3";
            src = fetchPypi {
              inherit pname version;
              sha256 = "ec50f084b997fdf6b26f8c31447e5789f4deb71fe69342cda1d7af0c9f91e01b";
            };
            doCheck = false;
            propagatedBuildInputs = [
              lxml
              urllib3
              dateparser
              charset-normalizer
            ];
          };

        justext = with pkgs.python3Packages;
          buildPythonPackage rec {
            pname = "jusText";
            version = "3.0.0";
            src = fetchPypi {
              inherit pname version;
              sha256 = "7640e248218795f6be65f6c35fe697325a3280fcb4675d1525bcdff2b86faadf";
            };
            doCheck = false;
            propagatedBuildInputs = [
              lxml
            ];
          };

        courlan = with pkgs.python3Packages;
          buildPythonPackage rec {
            pname = "courlan";
            version = "0.9.2";
            src = fetchPypi {
              inherit pname version;
              sha256 = "c21ac0483a644610e1b706fe7b535503f0a85cfd846f3a42e0fa7061b016127f";
            };
            doCheck = false;
            propagatedBuildInputs = [
              langcodes
              tld
              urllib3
            ];
          };

        py3langid = with pkgs.python3Packages;
          buildPythonPackage rec {
            pname = "py3langid";
            version = "0.2.2";
            src = fetchPypi {
              inherit pname version;
              sha256 = "b4de01dad7e701f29d216a0935e85e096cc8675903d23ea8445b2bb5f090b96f";
            };
            doCheck = false;
            propagatedBuildInputs = [
              numpy
            ];
          };

        trafilatura = with pkgs.python3Packages;
          buildPythonPackage rec {
            pname = "trafilatura";
            version = "1.5.0";
            src = fetchPypi {
              inherit pname version;
              sha256 = "7a3e4f8dda70e3dc1f0ae0347fae97355d98233a53a253b6e483ae35681ee781";
            };
            doCheck = false;
            propagatedBuildInputs = [
              # required
              lxml
              urllib3
              htmldate
              justext
              certifi
              courlan
              # optional
              brotli
              cchardet
              py3langid
              pycurl
            ];
          };

        # declare the python packages used for building & developing
        python-packages-build = python-packages:
          with python-packages; [
            pyphen
            nltk
            cherrypy
            trafilatura
          ];

        python-packages-devel = python-packages:
          with python-packages; [
            black
            pyflakes
            isort
            ipython
          ] ++ (python-packages-build python-packages);

        python-build = pkgs.python3.withPackages python-packages-build;
        python-devel = pkgs.python3.withPackages python-packages-devel;

        # declare how the python package shall be built
        text_statistics = python-build.pkgs.buildPythonPackage {
          pname = "text_statistics";
          version = "1.0.3";

          propagatedBuildInputs = (python-packages-build python-build.pkgs);

          src = ./.;
        };

        # download nltk-punkt, an external requirement for nltk
        nltk-punkt = pkgs.fetchurl {
          url = "https://github.com/nltk/nltk_data/raw/5db857e6f7df11eabb5e5665836db9ec8df07e28/packages/tokenizers/punkt.zip";
          sha256 = "sha256-UcMHiZSur2UL/I4Ci+T7QrSg0XfUHAErapg5eWU2YOw=";
        };

        # declare how the docker image shall be built
        dockerImage = pkgs.dockerTools.buildImage {
          name = text_statistics.pname;
          tag = text_statistics.version;

          config = {
            Cmd = [
              "${pkgs.bash}/bin/sh" (pkgs.writeShellScript "runDocker.sh"
                ''${pkgs.coreutils}/bin/mkdir -p /nltk_data/tokenizers;
                  ${pkgs.unzip}/bin/unzip ${nltk-punkt} -d /nltk_data/tokenizers;
                  /bin/text_statistics
                '')
            ];
            WorkingDir = "/";
          };

          copyToRoot = pkgs.buildEnv {
            name = "image-root";
            paths = [ text_statistics ];
            pathsToLink = [ "/bin" ];
          };
        };

      in {
        packages = {
          pythonPackage = text_statistics;
          docker = dockerImage;
        };
        defaultPackage = text_statistics;
        devShell = pkgs.mkShell {
          buildInputs = [
            python-devel
            # python language server
            pkgs.nodePackages.pyright
          ];
        };
      }
    );
}
