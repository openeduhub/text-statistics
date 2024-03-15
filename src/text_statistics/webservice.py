#!/usr/bin/env python3

import argparse
import json
from typing import Optional

import pyphen
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field, conlist

import text_statistics.stats as stats
from text_statistics._version import __version__

EMBEDDINGS_LEN = len(stats.get_embeddings("Test"))
Embedding = conlist(float, min_length=EMBEDDINGS_LEN, max_length=EMBEDDINGS_LEN)


class InputData(BaseModel):
    text: str = Field(min_length=1)
    reading_speed: float = Field(default=200.0, ge=1.0)
    generate_embeddings: bool = Field(default=False)


class Result(BaseModel):
    flesch_ease: float | None
    classification: stats.Classification | None
    wiener_index: float | None
    reading_time: float | None
    embeddings: Optional[Embedding]
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
    generate_embeddings : bool, optional
        Whether to also generate a vectorized representation of the text using
        word embeddings.
        
    
    Returns
    -------
    flesch_ease : float or null
        The readability score of the text,
        according to the Flesch reading ease.
        null if undefined (i.e. text is empty).
    flesch_classification : str or null
        Interpretation of the Flesch readability score,
        from 'Sehr leicht' to 'Sehr schwer'.
        null if undefined (i.e. text is empty).
    wiener_index : float or null
        The appropriate school grade of the text, based on its readability,
        according to the Wiener index.
        null if undefined (i.e. text is empty).
    reading_time : float or null
        The predicted time to read the text, in seconds.
        This is adjusted for the readability of the text,
        according to the following formula:
        reading_speed / 2 * exp(log(4) * flesch_ease / 121.5).
        Thus, reading speed is doubled at the maximum readability
        (121.5) and halved at readability 0.
        null if undefined (i.e. text is empty).
    embeddings : list[float] or null
        If ``generate_embeddings`` was set to `True`, this will be the
        vectorized representation of the text. Otherwise, `null`.
    version : str
        The version of the text statistics service.
    """

    # definition of the end point
    @app.post("/analyze-text", summary=summary, description=description)
    async def text_stats(data: InputData) -> Result:
        """
        Compute various statistical properties on the given text or URL.
        """
        # only support german language for now
        target_language = "de"

        try:
            flesch_ease = stats.calculate_flesch_ease(data.text, pyphen_dic=pyphen_dic)
        except ZeroDivisionError:
            return Result(
                flesch_ease=None,
                wiener_index=None,
                classification=None,
                reading_time=None,
                embeddings=None,
            )

        wiener_index = stats.calculate_wiener_index(data.text, pyphen_dic=pyphen_dic)

        classification = stats.classify_from_flesch_ease(flesch_ease)

        reading_time = stats.predict_reading_time(
            text=data.text,
            func=stats.initial_adjust_func,
            dic=pyphen_dic,
            reading_speed=data.reading_speed,
            score=flesch_ease,
        )

        embeddings = None
        if data.generate_embeddings:
            embeddings = stats.get_embeddings(text=data.text)

        return Result(
            flesch_ease=flesch_ease,
            wiener_index=wiener_index,
            classification=classification,
            reading_time=reading_time * 60,
            embeddings=embeddings,
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
