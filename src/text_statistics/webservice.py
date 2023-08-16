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
    flesh_ease: float
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
            flesh_ease=score,
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
    app.post("/analyze-text")(get_service(pyphen_dic))
    uvicorn.run(
        "text_statistics.webservice:app", host=args.host, port=args.port, reload=False
    )


if __name__ == "__main__":
    main()
