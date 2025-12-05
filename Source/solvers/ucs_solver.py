import sys
import heapq
import time
import random
from pathlib import Path
from typing import List, Dict

# Import from game_logic
sys.path.append(str(Path(__file__).parent.parent))
from game_logic import WORD_LIST, get_pattern, filter_words

class UCSNode:
    def __init__(self, candidates: List[str], guess_history: List, path_cost: float):
        self.candidates = candidates
        self.guess_history = guess_history
        self.path_cost = path_cost

    def __lt__(self, other):
        return self.path_cost < other.path_cost

def find_guesses_pool(candidates: List[str]) -> List[str]:
    if len(candidates) <= 20:
        return list(candidates)
    
    # SELECT POOL OF 15 CANDIDATES + STRONG STARTERS
    pool = list(candidates[:15])

    starters = ['slate', 'crane', 'trace', 'roate', 'raise']
    for s in starters:
        if s in candidates and s not in pool:
            pool.append(s)
            
    return pool

def solve(target: str):

    start_time = time.time()

    root = UCSNode(candidates=WORD_LIST.copy(), guess_history=[], path_cost=0.0)

    frontier = []
    heapq.heappush(frontier, root)
    
    expanded_nodes = 0
    visited_states = set()

    while frontier:
        # Get node with lowest path cost
        node = heapq.heappop(frontier)
    
        if node.path_cost >= 6:
            continue

        state_key = tuple(sorted(node.candidates))
        if state_key in visited_states:
            continue
        visited_states.add(state_key)
        
        expanded_nodes += 1
        
        #GOAL TEST
        if len(node.candidates) == 1 and node.candidates[0] == target:
            final_guess = node.candidates[0]
            return node.guess_history + [(final_guess, (2, 2, 2, 2, 2))]
        
        if node.guess_history and node.guess_history[-1][0] == target:
            return node.guess_history

        #EXPAND NODE
        pool = find_guesses_pool(node.candidates)
        
        for guess in pool:
            if any(guess == g for g, _ in node.guess_history):
                continue
                
            # Get real pattern from Game (Environment)
            real_pattern = get_pattern(guess, target)
            
            # Filter new candidates list
            new_candidates = filter_words(node.candidates, guess, real_pattern)
            
            if not new_candidates:
                continue

            new_history = node.guess_history + [(guess, real_pattern)]
            new_cost = node.path_cost + 1
            
            child = UCSNode(new_candidates, new_history, new_cost)
            heapq.heappush(frontier, child)
            
    return []