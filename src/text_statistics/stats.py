#!/usr/bin/env python3

import argparse
import math
import string
from collections import defaultdict
from collections.abc import Callable
from typing import Literal, Optional

import numpy as np
import its_prep.spacy as nlp
import pyphen
from its_prep import tokenize_documents

Classification = Literal[
    "Sehr leicht",
    "Leicht",
    "Mittelleicht",
    "Mittel",
    "Mittelschwer",
    "Schwer",
    "Sehr schwer",
]


def calculate_flesch_ease(text: str, pyphen_dic) -> float:
    # fragment the given text into sentences,
    # and sentences into words
    doc = list(tokenize_documents([text], tokenize_fun=nlp.tokenize_as_words))[0]
    words_by_sentences = nlp.into_sentences(doc)
    # sentences = nltk.sent_tokenize(text)
    # words_by_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]

    average_sentence_length = sum(len(words) for words in words_by_sentences) / len(
        words_by_sentences
    )

    # fragment each word into its syllables
    hyphenations = [
        pyphen_dic.inserted(word).split("-")
        for words in words_by_sentences
        for word in words
        if not word in string.punctuation
    ]

    # calculate the Flesch-ease for German
    average_hyphenation_length = sum(
        len(hyphenation) for hyphenation in hyphenations
    ) / len(hyphenations)
    return 180 - average_sentence_length - (58.5 * average_hyphenation_length)


def calculate_wiener_index(text: str, pyphen_dic) -> float:
    # average sentence length
    doc = list(tokenize_documents([text], tokenize_fun=nlp.tokenize_as_words))[0]
    words_by_sentences = nlp.into_sentences(doc)

    average_sent_len = sum(len(words) for words in words_by_sentences) / len(
        words_by_sentences
    )

    # words by number of syllables
    words = [word for words in words_by_sentences for word in words]
    hyphenations: list[list[str]] = [
        pyphen_dic.inserted(word).split("-")
        for word in words
        if not word in string.punctuation
    ]
    num_by_num_syls = defaultdict(lambda: 0)
    for hyphenation in hyphenations:
        num_by_num_syls[len(hyphenation)] += 1
    rate_many_syls = sum(
        num_by_num_syls[i] for i in num_by_num_syls.keys() if i >= 3
    ) / len(words)
    rate_one_syl = num_by_num_syls[1] / len(words)

    rate_long_words = sum(len(word) > 6 for word in words) / len(words)

    return (
        0.1935 * rate_many_syls * 100
        + 0.1672 * average_sent_len
        + 0.1297 * rate_long_words * 100
        - 0.0327 * rate_one_syl * 100
        - 0.875
    )


def classify_from_flesch_ease(score: float) -> Classification:
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


def predict_reading_time(
    text: str,
    func: Callable[[float, float], float],
    dic,
    reading_speed: float = 200.0,
    score: Optional[float] = None,
) -> float:
    """
    Predict the reading time by taking an assumed reading time,
    modifying it using the given function according to the Flesch-ease,
    and applying it to the number of words in the given text.
    """
    doc = list(tokenize_documents([text], tokenize_fun=nlp.tokenize_as_words))[0]
    num_words = len(doc)
    score = score if score else calculate_flesch_ease(text, dic)
    return num_words / func(reading_speed, score)


def initial_adjust_func(reading_speed: float, score: float) -> float:
    """
    An initial example of a possible relationship between Flesch-ease
    and reading speed
    """
    return reading_speed / 2 * math.exp(math.log(4) / 121.5 * score)


def get_embeddings(text: str) -> list[float]:
    doc = list(tokenize_documents([text], tokenize_fun=nlp.tokenize_as_words))[0]
    return np.array(nlp.get_word_vectors(doc)).sum(-2).tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    parser.add_argument("-v", "--reading_speed", default=200.0)
    parser.add_argument("-l", "--language", default="de_DE")

    args = parser.parse_args()

    dic = pyphen.Pyphen(lang=args.language)
    score = calculate_flesch_ease(args.text, pyphen_dic=dic)
    reading_time = predict_reading_time(
        args.text,
        initial_adjust_func,
        dic=dic,
        reading_speed=args.reading_speed,
        score=score,
    )

    print(f"Komplexität des Textes: {classify_from_flesch_ease(score)}")
    print(f"(Flesch-Lesbarkeits-Index: {score:.1f})")
    print(f"Ungefähre Lesezeit: {int(reading_time * 60)} Sekunden")


if __name__ == "__main__":
    main()
