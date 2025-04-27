# all the plant expressions are stored in this file.
# /home/nvk15697/plants_speak/poc/variants/v1_rule_based/expressions_store.py

import random

# Map plant overall mood to a small set of emojis
_mood_to_emojis = {
    "highly_stressed":     ["😱", "🥀"],
    "moderately_stressed": ["😟", "🍂"],
    "happy":               ["😄", "🌿"],
    "mixed":               ["🤔", "🌱"],
}


def get_emoji(mood: str) -> str:
    """
    Return a random emoji for the given mood, or ❓ if unknown.
    """
    return random.choice(_mood_to_emojis.get(mood, ["❓"]))