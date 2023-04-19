{
  description = "Basic Python Environment";

  inputs = { flake-utils = { url = "github:numtide/flake-utils"; }; };

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
            pandas-stubs
            # data structures
            numpy
            pandas
            # stats
            scipy
            pyphen
            nltk
          ];
        local-python = pkgs.python310.withPackages local-python-packages;

      in {
        devShell = pkgs.mkShell {
          buildInputs = [
            local-python
            # python language server
            pkgs.nodePackages.pyright
          ];
        };
      });
}
