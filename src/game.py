# game.py - daily puzzle generation and scoring
#
# Deterministic from the date: everyone (well, both of your devices)
# gets the same honeycomb on the same day, fully offline. A pangram
# base word is chosen from a curated common-words list, a center letter
# is picked, and the answer set is computed against the big dictionary.
# Generation runs once per day and is cached in SQLite, so the 188k-word
# scan doesn't happen on every launch (matters on a phone).

import hashlib
import os
import random

WORDLIST_DIR = os.path.join(os.path.dirname(__file__), "..", "data",
                            "wordlists")
# When installed by meson, wordlists live next to the module:
if not os.path.isdir(WORDLIST_DIR):
    WORDLIST_DIR = os.path.join(os.path.dirname(__file__), "wordlists")

MIN_ANSWERS = 20
MAX_ANSWERS = 75

RANKS = [
    (0.00, "Larva"),
    (0.05, "Worker"),
    (0.15, "Drone"),
    (0.30, "Forager"),
    (0.45, "Architect"),
    (0.60, "Royal Jelly"),
    (0.75, "Genius"),
    (1.00, "Queen Bee"),
]


def _load(name):
    path = os.path.join(WORDLIST_DIR, name)
    with open(path) as f:
        return [w.strip() for w in f if w.strip()]


def word_score(word, letterset):
    if len(word) == 4:
        return 1
    score = len(word)
    if set(word) >= letterset:  # pangram
        score += 7
    return score


class Puzzle:
    def __init__(self, date_str, letters, answers):
        self.date = date_str
        self.letters = letters            # 7 chars, letters[0] is center
        self.center = letters[0]
        self.letterset = frozenset(letters)
        self.answers = frozenset(answers)
        self.max_score = sum(word_score(w, self.letterset)
                             for w in self.answers)
        self.pangrams = frozenset(w for w in self.answers
                                  if set(w) >= self.letterset)

    def check(self, word):
        """Returns (ok, reason-or-points)."""
        word = word.lower()
        if len(word) < 4:
            return False, "Too short"
        if self.center not in word:
            return False, "Missing center letter"
        if not set(word) <= self.letterset:
            return False, "Wrong letters"
        if word not in self.answers:
            return False, "Not in word list"
        return True, word_score(word, self.letterset)

    def rank(self, score):
        name = RANKS[0][1]
        for threshold, rname in RANKS:
            if self.max_score and score >= threshold * self.max_score:
                name = rname
        return name


def generate(date_str):
    """Deterministically build the puzzle for YYYY-MM-DD."""
    seed = int.from_bytes(
        hashlib.sha256(f"nectar:{date_str}".encode()).digest()[:8], "big"
    )
    rng = random.Random(seed)

    pangram_bases = _load("pangrams.txt")
    valid = _load("valid.txt")
    rng.shuffle(pangram_bases)

    for base in pangram_bases:
        letters = sorted(set(base))
        centers = letters[:]
        rng.shuffle(centers)
        letterset = set(letters)
        # One pass over the dictionary per base word, bucketed by letter
        candidates = [w for w in valid if set(w) <= letterset]
        for center in centers:
            answers = [w for w in candidates if center in w]
            if MIN_ANSWERS <= len(answers) <= MAX_ANSWERS:
                ordered = [center] + [l for l in letters if l != center]
                return Puzzle(date_str, "".join(ordered), answers)
    # Practically unreachable with 1400+ bases, but never crash the app:
    base = pangram_bases[0]
    letters = sorted(set(base))
    letterset = set(letters)
    answers = [w for w in valid if set(w) <= letterset and letters[0] in w]
    return Puzzle(date_str, "".join(letters), answers)
