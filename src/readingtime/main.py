#!/usr/bin/env python3

import cherrypy
import readingtime.readingtime as rt
from readingtime.grab_content import grab_content
import pyphen


class WebService:
    def __init__(self, dic):
        self.dic = dic

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def analyze_text(self):
        target_language = "de"
        
        data = cherrypy.request.json

        if "text" in data:
            text = data["text"]
        elif "url" in data:
            url = data["url"]
            text = grab_content(
                url,
                favor_precision=True,
                target_language=target_language
            )
            # no content could be grabbed
            if text is None:
                return None
        else:
            return None

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
            "text": text,
        }


def main():
    cherrypy.server.socket_host = "0.0.0.0"
    cherrypy.quickstart(WebService(dic=pyphen.Pyphen(lang="de_DE")))


if __name__ == "__main__":
    main()
