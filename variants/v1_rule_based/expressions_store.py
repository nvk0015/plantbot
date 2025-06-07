# all the plant expressions are stored in this file.
# /home/nvk15697/plants_speak/poc/variants/v1_rule_based/expressions_store.py

import random

_mood_to_emojis = {
    "highly_stressed":     ["😱", "😩"],
    "moderately_stressed": ["😟"],
    "happy":               ["😄", "😊"],
    "mixed":               ["🤔", "😐"],
    "very_happy":          ["😁"],
    "very_moist":          ["💧", "🌊"],
    "very_dry":            ["🌵", "🍂"],
    "very_hot":            ["🔥", "☀️"],
    "very_cold":           ["❄️", "☃️"],
    "very_humid":          ["🌫️", "💧"],
    "very_dry_air":        ["🌬️", "🍃"],
    "light_deprived":      ["🌑", "🌒"],
    "very_dark":           ["🌑"],
    "lightly_dark":        ["🌘"],
    "ambient":             ["☁️", "🌥️"],
    "sunny":               ["☀️", "🌞"],
    "very_sunny":          ["🌞", "😎"],
    "person_interacting":  ["❤", "💕", "🤝"],
    "person_approaching":  ["👣", "👥", "👀"],
    "person_far_away":     ["👋", "🚶‍♂️"],
}

def get_emoji(mood):
    return random.choice(_mood_to_emojis.get(mood, ["❓"]))
