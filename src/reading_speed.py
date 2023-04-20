#!/usr/bin/env python3

import argparse
import math
import string
from collections.abc import Callable
from typing import Optional

import nltk
import pyphen


def flesch_ease(text: str, dic) -> float:
    sentences = nltk.sent_tokenize(text)
    words_by_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
    average_sentence_length = sum(len(words) for words in words_by_sentences) / len(
        words_by_sentences
    )
    hyphenations = [
        dic.inserted(word).split("-")
        for words in words_by_sentences
        for word in words
        if not word in string.punctuation
    ]
    average_hyphenation_length = sum(
        len(hyphenation) for hyphenation in hyphenations
    ) / len(hyphenations)
    return 180 - average_sentence_length - (58.5 * average_hyphenation_length)


def classification_from_flesch_ease(score: float) -> str:
    if score <= 30:
        return "Sehr schwer"
    if score <= 50:
        return "Schwer"
    if score <= 60:
        return "Mittelschwer"
    if score <= 70:
        return "Mittel"
    if score <= 80:
        return "Mittelleicht"
    if score <= 90:
        return "Leicht"
    return "Sehr leicht"


def predicted_reading_time(
    text: str,
    func: Callable[[float, float], float],
    dic,
    reading_speed: float = 200.0,
    score: Optional[float] = None,
) -> float:
    num_words = len(nltk.word_tokenize(text))
    score = score if score else flesch_ease(text, dic)
    return num_words / func(reading_speed, score)


def initial_adjust_func(reading_speed: float, score: float) -> float:
    return reading_speed / 2 * math.exp(math.log(4) / 121.5 * score)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    parser.add_argument("-v", "--reading_speed", default=200.0)
    parser.add_argument("-l", "--language", default="de_DE")

    args = parser.parse_args()

    dic = pyphen.Pyphen(lang=args.language)
    score = flesch_ease(args.text, dic=dic)
    reading_time = predicted_reading_time(
        args.text,
        initial_adjust_func,
        dic=dic,
        reading_speed=args.reading_speed,
        score=score,
    )

    print(
        f"Komplexität des Textes: {classification_from_flesch_ease(score)} (Flesch-Lesbarkeits-Index: {score:.1f})"
    )
    print(f"Ungefähre Lesezeit: {int(reading_time * 60)} Sekunden")


if __name__ == "__main__":
    main()
