#!/usr/bin/env python3

import argparse

import pyphen
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import text_statistics.stats as stats
from text_statistics._version import __version__

app = FastAPI()


class Data(BaseModel):
    text: str
    reading_speed: float = 200.0


class Result(BaseModel):
    flesch_ease: float
    classification: stats.Classification
    reading_time: float
    version: str = __version__


@app.get("/_ping")
def _ping():
    pass


def get_service(pyphen_dic):
    async def fun(data: Data) -> Result:
        """
        Compute various statistical properties on the given text or URL.
        """
        # only support german language for now
        target_language = "de"

        score = stats.calculate_flesch_ease(data.text, pyphen_dic=pyphen_dic)
        classification = stats.classify_from_flesch_ease(score)
        reading_time = stats.predict_reading_time(
            text=data.text,
            func=stats.initial_adjust_func,
            dic=pyphen_dic,
            reading_speed=data.reading_speed,
            score=score,
        )

        return Result(
            flesch_ease=score,
            classification=classification,
            reading_time=reading_time * 60,
        )

    return fun


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
    pyphen_dic = pyphen.Pyphen(lang=args.lang)
    summary = "Compute text statistics on the given text"
    app.post(
        "/analyze-text",
        summary=summary,
        description=f"""
        {summary}

        Parameters
        ----------
        text : str
            The text to be analyzed.
        reading_speed : float, optional
            The reading speed in characters per minute to use as a base-line.
            Set to 200 by default.

        Returns
        -------
        flesch_ease : float
            The readability score of the text,
            calculated according to the Flesch reading ease.
        classification : str
            Interpretation of the readability score,
            from 'Sehr leicht' to 'Sehr schwer'.
        reading_time : float
            The predicted time to read the text, in seconds.
            This is adjusted for the readability of the text, using
            reading_speed / 2 * exp(log(4) / 121.5 * flesch_ease).
            Thus, reading speed is doubled at the maximum readability
            (121.5) and halved at readability 0.
        version : str
            The version of the text statistics service.
        """,
    )(get_service(pyphen_dic))
    uvicorn.run(
        "text_statistics.webservice:app", host=args.host, port=args.port, reload=False
    )


if __name__ == "__main__":
    main()
