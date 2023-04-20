#!/usr/bin/env python3

import cherrypy
import reading_speed as rs
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

        score = rs.calculate_flesch_ease(text, dic=self.dic)
        classification = rs.classify_from_flesch_ease(score)
        reading_time = rs.predict_reading_time(
            text=text,
            func=rs.initial_adjust_func,
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
    cherrypy.quickstart(WebService(pyphen.Pyphen(lang="de_DE")))


if __name__ == "__main__":
    main()
