{
  description = "Basic Python Environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-22.11";
    flake-utils = { url = "github:numtide/flake-utils"; };
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        local-python-packages = python-packages:
          with python-packages; [
            # supplements for programming
            black
            pyflakes
            isort
            # NLP
            pyphen
            nltk
            # web service
            cherrypy
          ];
        local-python = pkgs.python3.withPackages local-python-packages;

        pythonBuild = with local-python.pkgs;
          buildPythonPackage {
            pname = "readingtime";
            version = "1.0.2";

            propagatedBuildInputs = with local-python.pkgs; [
              pyphen
              nltk
              cherrypy
            ];

            src = ./.;
          };

        dockerImage = pkgs.dockerTools.buildImage {
          name = pythonBuild.pname;
          tag = pythonBuild.version;

          config = {
            Cmd = [
              "${pkgs.bash}/bin/sh"
              (pkgs.writeShellScript "runDocker.sh" ''
                ${pkgs.unzip}/bin/unzip /nltk_data/tokenizers/punkt.zip -d /nltk_data/tokenizers &
                /bin/readingtime
              '')
            ];
            WorkingDir = "/";
          };

          copyToRoot = pkgs.buildEnv {
            name = "image-root";
            paths = [ ./data pythonBuild ];
            pathsToLink = [ "/" ];
          };
        };

      in {
        packages = {
          pythonPackage = pythonBuild;
          docker = dockerImage;
        };
        defaultPackage = pythonBuild;
        devShell = pkgs.mkShell {
          buildInputs = [
            local-python
            # python language server
            pkgs.nodePackages.pyright
          ];
        };
      });
}
