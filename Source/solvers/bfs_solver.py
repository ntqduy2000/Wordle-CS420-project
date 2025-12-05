import sys
from pathlib import Path
from collections import deque

#IMPORT
sys.path.append(str(Path(__file__).parent.parent))

from game_logic import WORD_LIST, get_pattern, filter_words

def solve(target: str):
    candidates = WORD_LIST.copy()
    history = []

    first_guess = "crane"
    if first_guess not in candidates:
        first_guess = candidates[0]

    queue = deque([first_guess])
    attempts = 0
    max_attempts = 20
    
    while attempts < max_attempts:
        attempts += 1
        
        if not queue:
            if not candidates:
                break
            queue.extend(candidates)
            
        guess = queue.popleft()
        pattern = get_pattern(guess, target)
        history.append((guess, pattern))
        if pattern == (2, 2, 2, 2, 2):
            return history
            
        candidates = filter_words(candidates, guess, pattern)
        
        queue = deque(candidates)
        
    return history