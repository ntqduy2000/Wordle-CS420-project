import argparse
import json
from datetime import datetime
import collections  # Added for solver logic
import time        # Added for animation delay

import matplotlib.pyplot as plt
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- NEW SOLVER HELPER FUNCTIONS ---

def get_feedback_pattern(guess, answer):
    """
    Pure logic version of get_colors. Returns a tuple of pattern strings
    ('G', 'Y', 'B') for Green, Yellow, Black/Gray.
    Used by the solver to check consistency.
    """
    pattern = ['B'] * 5
    answer_counts = collections.Counter(answer)
    
    # Pass 1: Green
    for i, char in enumerate(guess):
        if char == answer[i]:
            pattern[i] = 'G'
            answer_counts[char] -= 1
            
    # Pass 2: Yellow
    for i, char in enumerate(guess):
        if pattern[i] == 'B': # If not already Green
            if answer_counts[char] > 0:
                pattern[i] = 'Y'
                answer_counts[char] -= 1
    return tuple(pattern)

def matches_pattern(word, guess, pattern):
    """
    Pruning Step: Checks if 'word' could be the answer given that
    we guessed 'guess' and received 'pattern'.
    """
    return get_feedback_pattern(guess, word) == pattern

def get_best_guess(candidates):
    """
    Heuristic Step: Picks the word that eliminates the most options.
    For speed, we pick the word with the most unique frequent letters.
    """
    if not candidates:
        return None
    # Sort by number of unique characters (simple entropy heuristic)
    candidates.sort(key=lambda w: len(set(w)), reverse=True)
    return candidates[0]

# --- END SOLVER FUNCTIONS ---

def get_args():
    """Get command-line arguments"""
    parser = argparse.ArgumentParser(
        description="wordle clone",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    return parser.parse_args()

def char_input_box(value, location):
    """Creates a PySimpleGUI text input box"""
    return sg.Input(
        value,
        key=location,  # location: (row, column)
        font="Calibri 40",
        text_color="white",
        size=(2, 1),
        border_width=1,
        disabled_readonly_background_color="#1a1a1a",
        background_color="#1a1a1a",
        justification="center",
        pad=2,
        disabled=True,
        enable_events=True,
    )

def keyboard_text_box(letter):
    """Creates a PySimpleGUI text box for keyboard"""
    return sg.Text(
        text=letter,
        key=letter,
        font="Calibri 30",
        text_color="white",
        size=(2, 1),
        border_width=0,
        background_color="gray",
        justification="center",
        pad=2,
    )

def get_colors(answer, guess, keyboard):
    """Determines letter colors for guess and keyboard (GUI Visualization)"""
    colors = ["", "", "", "", ""]
    answer_copy = list(answer)
    guess_copy = list(guess)

    for i, letter in enumerate(guess_copy):  # 1st guess pass
        if guess_copy[i] == answer_copy[i]:
            colors[i] = "green"
            answer_copy[i] = "*"
            guess_copy[i] = "*"

    for i, letter in enumerate(guess_copy):  # 2nd guess pass
        if letter == "*":
            continue
        elif letter in answer_copy:
            colors[i] = "#C9B359"
            answer_copy.remove(letter)
        else:
            colors[i] = "#333333"

    answer_copy = list(answer)
    guess_copy = list(guess)

    for i, letter in enumerate(guess_copy):  # update keyboard
        if letter not in answer_copy:
            keyboard[letter] = "#333333"
        elif letter == answer_copy[i]:
            keyboard[letter] = "green"
        elif (letter in answer_copy) and (keyboard[letter] != "green"):
            keyboard[letter] = "#C9B359"

    return colors, keyboard

def update_stats_win(stats, guesses):
    """update game stats after win"""
    stats["tot_games_played"] += 1
    stats["tot_games_won"] += 1
    stats["win_percent"] = round(stats["tot_games_won"] / stats["tot_games_played"] * 100)
    if stats["max_streak"] == stats["current_streak"]:
        stats["max_streak"] += 1
    stats["current_streak"] += 1
    stats["guess_distro"][len(guesses) - 1] += 1
    with open("data_files/stats.txt", "w") as f:
        json.dump(stats, f)
    return stats

def update_stats_lose(stats, guesses):
    """update game stats after lose"""
    stats["tot_games_played"] += 1
    stats["win_percent"] = round(stats["tot_games_won"] / stats["tot_games_played"] * 100)
    stats["current_streak"] = 0
    with open("data_files/stats.txt", "w") as f:
        json.dump(stats, f)
    return stats

def display_stats(stats, message):
    """Display statistics in secondary window"""
    def create_bar_graph(stats):
        plt.figure(figsize=(3.5, 4), facecolor="#1a1a1a")
        plt.rc("axes", edgecolor="#1a1a1a")
        ax = plt.axes()
        ax.set_facecolor("#1a1a1a")
        plt.bar([1, 2, 3, 4, 5, 6], stats["guess_distro"], color="green", width=0.5)
        plt.title("GUESS DISTRIBUTION", fontsize=14, color="white", pad=20)
        plt.tick_params(bottom=False)
        plt.xticks(ticks=[1, 2, 3, 4, 5, 6], color="white")
        plt.yticks([])
        for i in range(0, 6):
            plt.text(i + 1, stats["guess_distro"][i], stats["guess_distro"][i], ha="center", color="white")
        return plt.gcf()

    def draw_figure(canvas, figure):
        figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=1)
        return figure_canvas_agg

    sg.theme("Default 1")
    sg.theme_background_color(color="#1a1a1a")
    sg.theme_element_background_color(color="#1a1a1a")
    sg.theme_text_element_background_color(color="#1a1a1a")

    first_column = [[sg.Text(stats["tot_games_played"], font="Calibri 20", text_color="white")], [sg.Text("Played", font="Calibri 16", text_color="white")]]
    second_column = [[sg.Text(stats["win_percent"], font="Calibri 20", text_color="white")], [sg.Text("Win %", font="Calibri 16", text_color="white")]]
    third_column = [[sg.Text(stats["current_streak"], font="Calibri 20", text_color="white")], [sg.Text("Current Streak", font="Calibri 16", text_color="white")]]
    fourth_column = [[sg.Text(stats["max_streak"], font="Calibri 20", text_color="white")], [sg.Text("Max Streak", font="Calibri 16", text_color="white")]]

    layout = [
        [sg.Text(message, font="Calibri 20", text_color="white", pad=20)],
        [sg.Column(first_column, element_justification="center"), sg.Column(second_column, element_justification="center"), sg.Column(third_column, element_justification="center"), sg.Column(fourth_column, element_justification="center")],
        [sg.Text("")],
        [sg.Canvas(size=(1000, 1000), key="-CANVAS-")],
        [sg.Exit()],
    ]

    window = sg.Window("", layout, finalize=True, background_color="#1a1a1a", element_justification="center", modal=True)
    window.move_to_center()
    draw_figure(window["-CANVAS-"].TKCanvas, create_bar_graph(stats))
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Exit":
            break
    window.close()

def main():
    args = get_args()
    try:
        with open("data_files/stats.txt", "r") as f:
            stats = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as error:
        with open("data_files/error-log.txt", "a") as f:
            date = datetime.now().strftime("%d-%b-%Y")
            f.write(f"{date}\nstats error: {str(error)}\n\n")
            stats = {"tot_games_played": 0, "tot_games_won": 0, "win_percent": 0, "current_streak": 0, "max_streak": 0, "guess_distro": [0, 0, 0, 0, 0, 0], "word_tracker": 0}
            with open("data_files/stats.txt", "w") as f:
                json.dump(stats, f)

    all_words = []
    try:
        with open("data_files/all_words.txt", "r") as f:
            all_words = list(set([line.upper().rstrip() for line in f]))
            all_words.sort()
    except FileNotFoundError:
        sg.popup_error("Error: 'data_files/all_words.txt' not found. Please create it!")
        return

    current_row = 0
    guesses = []
    keyboard = dict.fromkeys(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    
    if stats["word_tracker"] >= len(all_words):
        stats["word_tracker"] = 0
        
    answer = all_words[stats["word_tracker"]]
    stats["word_tracker"] += 1
    if stats["word_tracker"] >= len(all_words):
        stats["word_tracker"] = 0

    sg.theme("Default 1")
    layout = [
        [[char_input_box("", (row, col)) for col in range(0, 5)] for row in range(0, 6)],
        [sg.Text(background_color="#1a1a1a")],
        [keyboard_text_box(letter) for letter in "QWERTYUIOP"],
        [keyboard_text_box(letter) for letter in "ASDFGHJKL"],
        [keyboard_text_box(letter) for letter in "ZXCVBNM"],
        [sg.Text(background_color="#1a1a1a")],
        # --- MODIFIED BUTTON ROW ---
        [
            sg.B("Enter", visible=False, bind_return_key=True),
            sg.B("SOLVE (DFS)", key="-SOLVE-", button_color=("white", "firebrick"), font="Calibri 16")
        ],
    ]

    window = sg.Window("WORDLE CLONE v1.0", layout, margins=(20, 20), finalize=True, element_justification="center", background_color="#1a1a1a")
    window.move_to_center()
    [window[(0, col)].update(disabled=False) for col in range(0, 5)]
    window.bind("<BackSpace>", "-BACKSPACE-")

    # --- LIST OF CANDIDATES FOR SOLVER ---
    solver_candidates = list(all_words)

    while True:
        event, values = window.read()

        # --- SOLVER LOGIC ---
        if event == "-SOLVE-":
            # If game is already over (technically max rows), ignore
            if current_row > 5:
                continue

            # Run a loop to automate the remaining guesses
            while current_row < 6:
                # 1. Pick best guess from current candidates
                # If first guess, pick a good starter like "CRANE" or "SLATE" for speed
                if len(solver_candidates) == len(all_words):
                     guess = "CRANE" # Good starter
                else:
                    guess = get_best_guess(solver_candidates)

                if not guess:
                    sg.popup("Solver failed! No words left.")
                    break

                # 2. Visually update the Input Boxes
                for i, char in enumerate(guess):
                    window[(current_row, i)].update(char)
                window.refresh() # Force GUI to paint
                time.sleep(0.5)  # Small pause to see it happen

                # 3. Simulate Logic (Same as "Enter" key)
                guesses.append(guess)
                
                # Get colors for GUI
                colors, keyboard = get_colors(answer, guess, keyboard) 
                
                # Update GUI Colors
                [window[current_row, col].update(background_color=colors[col], text_color="white") for col in range(0, 5)]
                [window[letter.upper()].update(background_color=keyboard[letter]) for letter in keyboard]
                window.refresh()

                # 4. Check Win
                if guess == answer:
                    update_stats_win(stats, guesses)
                    display_stats(stats, "YOU WIN! (SOLVED)")
                    break # Break internal loop, then wait for window close

                # 5. Prune the search tree (DFS step)
                # Calculate what pattern we just got
                pattern_received = get_feedback_pattern(guess, answer)
                # Filter candidates that don't match that pattern
                solver_candidates = [w for w in solver_candidates if matches_pattern(w, guess, pattern_received)]

                # 6. Move to next row
                if current_row < 5:
                    current_row += 1
                    # Note: We don't need to enable/focus inputs for the solver, 
                    # but we do it to keep state consistent if user wants to take over
                    [window[(current_row, col)].update(disabled=False) for col in range(0, 5)]
                else:
                    # Loss condition
                    update_stats_lose(stats, guesses)
                    display_stats(stats, "YOU LOSE! The answer was: " + answer)
                    break
            
            # After solver finishes (win or lose), exit the main event loop
            break 

        # --- EXISTING LOGIC ---
        if isinstance(event, tuple):
            row, col = event
            if (values[row, col].isalpha()) and (col in range(0, 4)):
                window[row, col].update(values[row, col].upper())
                window[row, col + 1].set_focus()
            elif (values[row, col].isalpha()) and (col == 4):
                window[row, col].update(values[row, col][0].upper())
            elif not (values[row, col].isalpha()):
                window[row, col].update("")

        elif (event == "Enter") and (values[current_row, 4] != ""):
            guess = "".join(values[current_row, col] for col in range(0, 5))
            if guess not in all_words:
                [window[current_row, col].update("") for col in range(0, 5)]
                window[current_row, 0].set_focus()
                sg.popup("Word not recognized", font="Calibri 30", auto_close=True, auto_close_duration=1)
            elif guess == answer:
                guesses.append(guess)
                colors, keyboard = get_colors(answer, guess, keyboard)
                [window[current_row, col].update(background_color="green", text_color="white") for col in range(0, 5)]
                [window[letter.upper()].update(background_color=keyboard[letter]) for letter in keyboard]
                update_stats_win(stats, guesses)
                display_stats(stats, "YOU WIN!")
                break
            else:
                guesses.append(guess)
                # --- UPDATE SOLVER CANDIDATES IF USER PLAYS MANUALLY ---
                # This ensures if user plays 2 lines then hits Solve, solver knows history
                current_pattern = get_feedback_pattern(guess, answer)
                solver_candidates = [w for w in solver_candidates if matches_pattern(w, guess, current_pattern)]
                # --------------------------------------------------------
                colors, keyboard = get_colors(answer, guess, keyboard)
                [window[current_row, column].update(background_color=colors[column]) for column, color in enumerate(colors)]
                [window[letter.upper()].update(background_color=keyboard[letter]) for letter in keyboard]
                if current_row < 5:
                    current_row += 1
                    [window[(current_row, col)].update(disabled=False) for col in range(0, 5)]
                    window[current_row, 0].set_focus()
                else:
                    update_stats_lose(stats, guesses)
                    display_stats(stats, "YOU LOSE!  The answer was: " + answer)
                    break

        elif (event == "Enter") and (values[current_row, 4] == ""):
            sg.popup("Not enough letters", font="Calibri 25", auto_close=True, auto_close_duration=1)

        elif event == "-BACKSPACE-":
            [window[current_row, i].update("") for i in range(0, 5)]
            window[current_row, 0].set_focus()

        elif event == sg.WIN_CLOSED:
            break

    window.close()

if __name__ == "__main__":
    main()