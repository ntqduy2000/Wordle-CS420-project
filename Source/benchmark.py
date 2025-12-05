import sys
import time
import random
import csv
import tracemalloc
from pathlib import Path
from typing import List, Dict, Callable

# Import logic game
sys.path.append(str(Path(__file__).parent))

from game_logic import WORD_LIST, get_pattern
from solvers import bfs_solver, dfs_solver, ucs_solver, astar_solver

#BENCHMARK CONFIGURATION
SAMPLE_SIZE = 50 
OUTPUT_FILE = "benchmark_results.csv"

def run_single_test(solver_func: Callable, target: str, algo_name: str):

    tracemalloc.start()

    start_time = time.time()
    
    try:
        history = solver_func(target)
        success = False
        if history and history[-1][1] == (2, 2, 2, 2, 2):
            success = True
            
        guess_count = len(history)
    except Exception as e:
        print(f"  [!] Error running {algo_name} with word {target}: {e}")
        history = []
        success = False
        guess_count = 6 # Considered a loss
        
    # 3. Stop timing
    end_time = time.time()
    time_taken = end_time - start_time
    
    # 4. Stop memory measurement and get peak usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Convert memory to KB
    memory_peak_kb = peak / 1024
    
    return {
        "Algorithm": algo_name,
        "Target Word": target,
        "Success": success,
        "Guesses": guess_count,
        "Time (s)": round(time_taken, 4),
        "Memory (KB)": round(memory_peak_kb, 2)
    }

def main():
    print(f"--- STARTING BENCHMARK ---")
    print(f"Number of test words: {SAMPLE_SIZE}")
    print(f"Algorithms: BFS, DFS, UCS, A*")
    print("-" * 50)

    # 1. Randomly select test set
    # Optionally filter out very rare words for fairness
    test_set = random.sample(WORD_LIST, SAMPLE_SIZE)
    
    # 2. Define list of competitors
    solvers = {
        "BFS": bfs_solver.solve,
        "DFS": dfs_solver.solve,
        "UCS": ucs_solver.solve,
        "A*": astar_solver.solve
    }
    
    results = []

    for algo_name, solve_func in solvers.items():
        print(f"\n Running algorithm: {algo_name}...")
        
        wins = 0
        total_guesses = 0
        total_time = 0
        
        for i, target in enumerate(test_set):
            if i % 10 == 0:
                print(f"   Processed {i}/{SAMPLE_SIZE} words...", end="\r")
            
            data = run_single_test(solve_func, target, algo_name)
            results.append(data)
            
            if data["Success"]:
                wins += 1
            total_guesses += data["Guesses"]
            total_time += data["Time (s)"]

        # Print summary for this algorithm
        avg_guesses = round(total_guesses / SAMPLE_SIZE, 2)
        avg_time = round(total_time / SAMPLE_SIZE, 4)
        win_rate = round((wins / SAMPLE_SIZE) * 100, 1)
        
        print(f"   ✅ Completed {algo_name} | Win Rate: {win_rate}% | Avg Guesses: {avg_guesses} | Avg Time: {avg_time}s")

    # 4. Save results to CSV file
    print(f"\n Saving results to {OUTPUT_FILE}...")
    
    try:
        keys = results[0].keys()
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print("🎉 DONE!")
        
    except IOError as e:
        print(f"❌ Error writing file: {e}")

if __name__ == "__main__":
    main()