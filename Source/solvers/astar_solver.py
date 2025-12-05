import sys
import math
import heapq
from collections import Counter
from pathlib import Path
from typing import List

# Import from game_logic
sys.path.append(str(Path(__file__).parent.parent))
from game_logic import WORD_LIST, get_pattern, filter_words


def calculate_entropy(guess: str, candidates: List[str]) -> float:
    pattern_counts = Counter()
    for word in candidates:
        pattern = get_pattern(guess, word)
        pattern_counts[pattern] += 1
        
    total = len(candidates)
    entropy = 0.0
    for count in pattern_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy

def find_best_guess_astar(candidates: List[str]) -> str:
    if len(candidates) <= 2:
        return candidates[0]

    guess_pool = candidates[:20]
    starters = ['slate', 'crane', 'trace', 'roate', 'raise']
    for s in starters:
        if s not in guess_pool and s in WORD_LIST:
            guess_pool.append(s)
            
    best_guess = guess_pool[0]
    best_score = -float('inf')
    
    for guess in guess_pool:
        # Calculate entropy
        entropy = calculate_entropy(guess, candidates)
        
        # Heuristic Bonus
        in_list_bonus = 0.5 if guess in candidates else 0
        
        score = entropy + in_list_bonus
        if score > best_score:
            best_score = score
            best_guess = guess
            
    return best_guess

#LOGIC FOR TESTING PURPOSES
def solve(target: str):

    candidates = WORD_LIST.copy()
    history = []
    
    for _ in range(6):
        if not candidates:
            break
            
        guess = find_best_guess_astar(candidates)
        
        pattern = get_pattern(guess, target)
        history.append((guess, pattern))
        
        if pattern == (2, 2, 2, 2, 2):
            return history
            
        candidates = filter_words(candidates, guess, pattern)
        
    return history