import random
from collections import Counter
from pathlib import Path
from typing import List, Tuple

BG = "#121213"
EMPTY_BG = BG
EMPTY_BORDER = "#3a3a3c"
EMPTY_TEXT = "#d7dadc"
KEY_BG = "#818384"
KEY_ACTIVE_BG = "#6e6f70"
COLOR_TEXT_FILLED = "#ffffff"
ROWS = 6
COLS = 5
COLOR_CORRECT = "#6aaa64"
COLOR_PRESENT = "#c9b458"
COLOR_ABSENT = "#3a3a3c"

#Handle data

def load_word_list() -> List[str]:

    base_path = Path(__file__).parent
    dict_path = base_path / "data" / "dictionary.txt"

    if not dict_path.exists():
        print(f"ERROR: Cannot find out file at {dict_path}")
        return ["apple", "beach", "crane", "stare", "stone", "world"]

    with dict_path.open("r", encoding="utf-8") as fh:
        # Read file, strip whitespace, convert to lowercase
        raw = [line.strip().lower() for line in fh if line.strip()]
    
    # Filter only 5-letter words that are alphabetic
    filtered = [w for w in raw if len(w) == 5 and w.isalpha()]
    
    # Remove duplicates but keep order
    seen = set()
    out = []
    for w in filtered:
        if w not in seen:
            seen.add(w)
            out.append(w)
            
    return out

# Global variable containing the word list (so other files can import and use it directly)
WORD_LIST = load_word_list()

#CORE LOGIC

def get_pattern(guess: str, target: str) -> Tuple[int, ...]:
    guess = guess.lower()
    target = target.lower()
    
    pattern = [0] * 5
    target_counts = Counter(target)
    used = [False] * 5
    for i in range(5):
        if guess[i] == target[i]:
            pattern[i] = 2
            target_counts[guess[i]] -= 1
            used[i] = True

    for i in range(5):
        if not used[i]:
            char = guess[i]
            # If character is in target and there are still counts left to match
            if char in target_counts and target_counts[char] > 0:
                pattern[i] = 1
                target_counts[char] -= 1
            else:
                pattern[i] = 0
                
    return tuple(pattern)


def filter_words(words: List[str], guess: str, pattern: Tuple[int, ...]) -> List[str]:
    return [word for word in words if get_pattern(guess, word) == pattern]