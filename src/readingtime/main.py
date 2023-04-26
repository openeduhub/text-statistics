#!/usr/bin/env python3

import cherrypy
import readingtime.readingtime as rt
import pyphen


class WebService:
    def __init__(self, dic):
        self.dic = dic

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def analyze_text(self):
        data = cherrypy.request.json

        text = data["text"]
        reading_speed = data.get("reading_speed", 200.0)

        score = rt.calculate_flesch_ease(text, dic=self.dic)
        classification = rt.classify_from_flesch_ease(score)
        reading_time = rt.predict_reading_time(
            text=text,
            func=rt.initial_adjust_func,
            dic=self.dic,
            reading_speed=reading_speed,
            score=score,
        )

        return {
            "flesh-ease": score,
            "classification": classification,
            "reading-time": reading_time * 60,
        }


def main():
    cherrypy.server.socket_host = "0.0.0.0"
    cherrypy.quickstart(WebService(pyphen.Pyphen(lang="de_DE")))


if __name__ == "__main__":
    main()
