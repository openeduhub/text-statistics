
# Table of Contents

1.  [Installation](#org8fd6db6)
    1.  [As Python Package](#orga2b564c)
    2.  [As Nix Flake](#orgc5fdb85)
    3.  [As Docker Image](#org7324381)
2.  [Usage](#org123aa60)

The `Python` script <src/readingtime/readingtime.py> estimates the reading time of a given text, using the following model:

-   It assumes a base-line reading speed of 200 WPM.
-   This reading speed is adjusted w.r.t. the Flesch-Reading-Ease of the given text.

In particular, we set that the &ldquo;real&rdquo; reading speed of the text is equal to $200 \cdot (\frac{1}{2} \exp^{\ln 4 / 121.5 \cdot s})$, where $s$ is the Flesch-Reading-Ease.
Thus, the reading-speed is halved at a reading ease of $0$ (very difficult) and double at a reading ease of $121.5$ (the highest possible value).

<src/readingtime/main.py> provides a microservice, see [2](#org123aa60).


<a id="org8fd6db6"></a>

# Installation


<a id="orga2b564c"></a>

## As Python Package

This package can be installed as a Python package by cloning this repository and running

    pip install .


<a id="orgc5fdb85"></a>

## As Nix Flake

Alternatively, with `nix` installed (and the `flakes` feature enabled), one can run the microservice through

    nix run git+https://codeberg.org/joka/readingtime.py


<a id="org7324381"></a>

## As Docker Image

A docker image can be built through

    nix build git+https://codeberg.org/joka/readingtime.py#docker

The resulting image has to be loaded and executed via

    docker load < /path/to/result
    docker run -p 8080:8080 readingtime:1.0.2


<a id="org123aa60"></a>

# Usage

Once the microservice is running, text can be supplied through `json` queries on the `analyze-text` subdomain.
For example:

    curl -d '{"text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. This is another sentence."}' -H "Content-Type: application/json" -X POST localhost:8080/analyze-text

The result contains the Flesch-ease, the corresponding classification, and the predicted reading time (in seconds):

    {"flesh-ease": 43.39452054794519, "classification": "Schwer", "reading-time": 29.987166756508653}

