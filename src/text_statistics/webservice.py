#!/usr/bin/env python3

import json
import argparse
from typing import Any

import pyphen
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import text_statistics.stats as stats
from text_statistics._version import __version__


class Data(BaseModel):
    text: str
    reading_speed: float = 200.0


class Result(BaseModel):
    flesch_ease: float
    classification: stats.Classification
    wiener_index: float
    reading_time: float
    version: str = __version__


def create_app(lang: str) -> FastAPI:
    pyphen_dic = pyphen.Pyphen(lang=lang)

    app = FastAPI()

    ### basic ping end point
    @app.get("/_ping")
    def _ping():
        pass

    ### the primary end point for text statistics
    # docs
    summary = "Compute text statistics on the given text"
    description = f"""
    Note: Only German language is supported right now.
    
    Parameters
    ----------
    text : str
        The text to be analyzed.
    reading_speed : float, optional
        The reading speed in characters per minute to use as a base-line.
        Default: 200
    
    Returns
    -------
    flesch_ease : float
        The readability score of the text,
        according to the Flesch reading ease.
    flesch_classification : str
        Interpretation of the Flesch readability score,
        from 'Sehr leicht' to 'Sehr schwer'.
    wiener_index : float
        The appropriate school grade of the text, based on its readability,
        according to the Wiener index.
    reading_time : float
        The predicted time to read the text, in seconds.
        This is adjusted for the readability of the text,
        according to the following formula:
        reading_speed / 2 * exp(log(4) * flesch_ease / 121.5).
        Thus, reading speed is doubled at the maximum readability
        (121.5) and halved at readability 0.
    version : str
        The version of the text statistics service.
    """

    # definition of the end point
    @app.post("/analyze-text", summary=summary, description=description)
    async def text_stats(data: Data) -> Result:
        """
        Compute various statistical properties on the given text or URL.
        """
        # only support german language for now
        target_language = "de"

        flesch_ease = stats.calculate_flesch_ease(data.text, pyphen_dic=pyphen_dic)
        wiener_index = stats.calculate_wiener_index(data.text, pyphen_dic=pyphen_dic)
        classification = stats.classify_from_flesch_ease(flesch_ease)
        reading_time = stats.predict_reading_time(
            text=data.text,
            func=stats.initial_adjust_func,
            dic=pyphen_dic,
            reading_speed=data.reading_speed,
            score=flesch_ease,
        )

        return Result(
            flesch_ease=flesch_ease,
            wiener_index=wiener_index,
            classification=classification,
            reading_time=reading_time * 60,
        )

    return app


def main():
    # define CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", action="store", default=8080, help="Port to listen on", type=int
    )
    parser.add_argument(
        "--host", action="store", default="0.0.0.0", help="Hosts to listen on", type=str
    )
    parser.add_argument(
        "--lang",
        action="store",
        default="de_DE",
        help="The language of the input text",
        type=str,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )

    # read passed CLI arguments
    args = parser.parse_args()

    # create and run the web service
    app = create_app(lang=args.lang)
    uvicorn.run(app, host=args.host, port=args.port, reload=False)


def print_openapi_schema():
    print(json.dumps(create_app(lang="de_DE").openapi()))


if __name__ == "__main__":
    main()
