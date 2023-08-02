{
  description = "Basic Python Environment";

  inputs = {
    nixpkgs.url = "github:joopitz/nixpkgs/trafilatura";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    {
      overlays.default = (final: prev: { inherit (self.packages.${final.system}) text-statistics; });
    } //
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {inherit system;};
        python = pkgs.python310;

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

        python-build = python.withPackages python-packages-build;
        python-devel = python.withPackages python-packages-devel;
        
        # download nltk-punkt, an external requirement for nltk
        nltk-punkt = pkgs.fetchzip {
          url = "https://github.com/nltk/nltk_data/raw/5db857e6f7df11eabb5e5665836db9ec8df07e28/packages/tokenizers/punkt.zip";
          hash = "sha256-SKZu26K17qMUg7iCFZey0GTECUZ+sTTrF/pqeEgJCos=";
        };

        # declare how the python package shall be built
        python-package = python-build.pkgs.buildPythonPackage rec {
          pname = "text-statistics";
          version = "1.0.4";
          src = self;
          propagatedBuildInputs = [ python-build ];
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
        python-app = python-build.pkgs.toPythonApplication python-package;

        # declare how the docker image shall be built
        docker-img = pkgs.dockerTools.buildImage rec {
          name = python-app.pname;
          tag = python-app.version;
          config = {
            Cmd = [ "${python-app}/bin/text-statistics" ];
          };
          copyToRoot = pkgs.buildEnv {
            name = "image-root";
            paths = [ python-app ];
            pathsToLink = [ "/bin" ];
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
            python-devel
            # python language server
            pkgs.nodePackages.pyright
            # nix lsp server
            pkgs.rnix-lsp
          ];
        };
      }
    );
}
