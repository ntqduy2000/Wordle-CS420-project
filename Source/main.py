import tkinter as tk
from tkinter import ttk
import threading
import random
import time
from typing import List, Tuple, Optional

# Import module game_logic
from game_logic import ROWS, COLS, WORD_LIST, get_pattern, filter_words, \
                       COLOR_CORRECT, COLOR_PRESENT, COLOR_ABSENT, \
                       BG, EMPTY_BG, EMPTY_BORDER, EMPTY_TEXT, KEY_BG, KEY_ACTIVE_BG, COLOR_TEXT_FILLED

from solvers import bfs_solver, dfs_solver, ucs_solver, astar_solver

CELL_SIZE = 55
REVEAL_DELAY_MS = 200

class WordleGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Wordle AI Solver - Group Project")
        self.root.geometry("600x850")
        self.root.configure(bg=BG)
        
        # Center window on screen
        self.root.update_idletasks()
        width = 600
        height = 850
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.target_word: str = ""
        self.current_guess_num: int = 0
        self.current_guess_str: str = ""
        self.game_over: bool = False
        self.revealing: bool = False

        self.cells: List[List[tuple]] = []
        self.message_label: Optional[tk.Label] = None
        self.key_buttons: dict = {}

        self.setup_ui()
        self.start_new_game()
        
        # Bind physical keyboard
        self.root.bind("<Key>", self.on_key_press)

    def setup_ui(self):
        title_label = tk.Label(self.root, text="WORDLE AI", font=("Helvetica", 40, "bold"), bg=BG, fg="white")
        title_label.pack(pady=(20, 4))

        self.message_label = tk.Label(self.root, text="", font=("Helvetica", 14), bg=BG, fg=EMPTY_TEXT)
        self.message_label.pack(pady=(0, 6))

        # Grid
        self.grid_frame = tk.Frame(self.root, bg=BG)
        self.grid_frame.pack(pady=(6, 18))

        self.cells = []
        for row in range(ROWS):
            row_cells = []
            for col in range(COLS):
                cell_frame = tk.Frame(self.grid_frame, width=CELL_SIZE, height=CELL_SIZE, bg=EMPTY_BG,
                                      highlightbackground=EMPTY_BORDER, highlightthickness=2)
                cell_frame.grid(row=row, column=col, padx=5, pady=5)
                cell_frame.pack_propagate(False)
                lbl = tk.Label(cell_frame, text="", font=("Helvetica", 24, "bold"), bg=EMPTY_BG, fg=EMPTY_TEXT)
                lbl.pack(expand=True, fill="both")
                row_cells.append((cell_frame, lbl))
            self.cells.append(row_cells)

        #Control Panel
        control_frame = tk.Frame(self.root, bg=BG)
        control_frame.pack(pady=10)

        #New Game
        btn_new = tk.Button(control_frame, text="NEW GAME", command=self.start_new_game,
                            font=("Helvetica", 12, "bold"), bg="#538d4e", fg="white", width=12)
        btn_new.grid(row=0, column=0, padx=10)

        # Label "Select AI:"
        lbl_algo = tk.Label(control_frame, text="Algorithm:", font=("Helvetica", 12), bg=BG, fg="white")
        lbl_algo.grid(row=0, column=1, padx=5)

        # Algorithm Dropdown
        self.algo_var = tk.StringVar()
        self.algo_combo = ttk.Combobox(control_frame, textvariable=self.algo_var, 
                                       values=["BFS", "DFS", "UCS", "A*"], 
                                       state="readonly", font=("Helvetica", 11), width=8)
        self.algo_combo.current(3) # Default to A*
        self.algo_combo.grid(row=0, column=2, padx=5)

        #Auto Solve
        btn_solve = tk.Button(control_frame, text="AUTO SOLVE", command=self.run_auto_solve,
                              font=("Helvetica", 12, "bold"), bg="#b59f3b", fg="white", width=12)
        btn_solve.grid(row=0, column=3, padx=10)

        # Keyboard
        self.setup_keyboard()

    def setup_keyboard(self):
        kb_frame = tk.Frame(self.root, bg=BG)
        kb_frame.pack(pady=20)
        keys = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        
        for r, row_keys in enumerate(keys):
            row_frame = tk.Frame(kb_frame, bg=BG)
            row_frame.pack()
            for char in row_keys:
                btn = tk.Button(row_frame, text=char, font=("Helvetica", 10, "bold"), 
                                width=4, height=2, bg=KEY_BG, fg="white",
                                command=lambda c=char: self.handle_char(c))
                btn.pack(side="left", padx=2, pady=2)
                self.key_buttons[char] = btn
        
        # Add ENTER and BACKSPACE buttons
        bottom_frame = tk.Frame(kb_frame, bg=BG)
        bottom_frame.pack(pady=5)
        
        enter_btn = tk.Button(bottom_frame, text="ENTER", font=("Helvetica", 10, "bold"),
                             width=8, height=2, bg=KEY_BG, fg="white",
                             command=self.handle_enter)
        enter_btn.pack(side="left", padx=2)
        
        back_btn = tk.Button(bottom_frame, text="←", font=("Helvetica", 10, "bold"),
                            width=8, height=2, bg=KEY_BG, fg="white",
                            command=self.handle_backspace)
        back_btn.pack(side="left", padx=2)

    def start_new_game(self):
        self.target_word = random.choice(WORD_LIST)
        print(f"DEBUG: Secret Word is {self.target_word}")
        
        self.current_guess_num = 0
        self.current_guess_str = ""
        self.game_over = False
        self.revealing = False
        self.message_label.config(text="")

        # Reset
        for row in range(ROWS):
            for col in range(COLS):
                frame, lbl = self.cells[row][col]
                lbl.config(text="", bg=EMPTY_BG)
                frame.config(bg=EMPTY_BG, highlightbackground=EMPTY_BORDER)
        
        for btn in self.key_buttons.values():
            btn.config(bg=KEY_BG)

    def on_key_press(self, event):
        """Handle physical keyboard input"""
        if self.game_over or self.revealing:
            return
        
        key = event.char.upper()
        
        if event.keysym == "Return":
            self.handle_enter()
        elif event.keysym == "BackSpace":
            self.handle_backspace()
        elif key.isalpha() and len(key) == 1:
            self.handle_char(key)
    
    def handle_char(self, char):
        """Add character to current guess"""
        if self.game_over or self.revealing:
            return
        
        if len(self.current_guess_str) < COLS:
            self.current_guess_str += char
            self.update_current_row()
    
    def handle_backspace(self):
        """Remove last character from current guess"""
        if self.game_over or self.revealing:
            return
        
        if len(self.current_guess_str) > 0:
            self.current_guess_str = self.current_guess_str[:-1]
            self.update_current_row()
    
    def handle_enter(self):
        """Submit current guess"""
        if self.game_over or self.revealing:
            return
        
        if len(self.current_guess_str) != COLS:
            self.message_label.config(text="Word must be 5 letters!", fg="#ff6b6b")
            return
        
        guess_lower = self.current_guess_str.lower()
        if guess_lower not in WORD_LIST:
            self.message_label.config(text="Not in word list!", fg="#ff6b6b")
            return
        
        # Valid guess - reveal it
        self.message_label.config(text="")
        self.reveal_current_guess()
    
    def update_current_row(self):
        """Update display of current row being typed"""
        row = self.current_guess_num
        if row >= ROWS:
            return
        
        for col in range(COLS):
            frame, lbl = self.cells[row][col]
            if col < len(self.current_guess_str):
                lbl.config(text=self.current_guess_str[col], bg=EMPTY_BG, fg=COLOR_TEXT_FILLED)
                frame.config(highlightbackground="#565758")
            else:
                lbl.config(text="", bg=EMPTY_BG, fg=EMPTY_TEXT)
                frame.config(highlightbackground=EMPTY_BORDER)
    
    def reveal_current_guess(self):
        """Reveal the current guess with color animation"""
        row = self.current_guess_num
        if row >= ROWS:
            return
        
        self.revealing = True
        guess = self.current_guess_str.lower()
        pattern = get_pattern(guess, self.target_word)
        
        # Animate color reveal
        for col in range(COLS):
            color = COLOR_ABSENT
            if pattern[col] == 2:
                color = COLOR_CORRECT
            elif pattern[col] == 1:
                color = COLOR_PRESENT
            
            delay = col * REVEAL_DELAY_MS
            self.root.after(delay, lambda c=col, clr=color: self._reveal_cell(row, c, clr))
        
        # After all cells revealed, check win/loss
        self.root.after(COLS * REVEAL_DELAY_MS + 100, lambda: self._finish_guess(pattern))
    
    def _reveal_cell(self, row, col, color):
        """Reveal a single cell with color"""
        frame, lbl = self.cells[row][col]
        lbl.config(bg=color, fg=COLOR_TEXT_FILLED)
        frame.config(bg=color, highlightbackground=color)
        
        # Update keyboard
        char = self.current_guess_str[col]
        if char in self.key_buttons:
            current_color = self.key_buttons[char].cget("bg")
            # Only update if new color is "better" (green > yellow > gray)
            if color == COLOR_CORRECT or (color == COLOR_PRESENT and current_color != COLOR_CORRECT):
                self.key_buttons[char].config(bg=color)
            elif color == COLOR_ABSENT and current_color == KEY_BG:
                self.key_buttons[char].config(bg=color)
    
    def _finish_guess(self, pattern):
        """Finish the current guess and check game state"""
        self.revealing = False
        
        # Check win
        if pattern == (2, 2, 2, 2, 2):
            self.message_label.config(text=f"🎉 You won! The word was {self.target_word.upper()}!", fg=COLOR_CORRECT)
            self.game_over = True
            return
        
        # Move to next row
        self.current_guess_num += 1
        self.current_guess_str = ""
        
        # Check loss
        if self.current_guess_num >= ROWS:
            self.message_label.config(text=f"Game Over! The word was {self.target_word.upper()}", fg="#ff6b6b")
            self.game_over = True
    
    def run_auto_solve(self):
        if self.game_over or self.revealing: return
        
        algo_name = self.algo_var.get()
        self.message_label.config(text=f"AI is thinking ({algo_name})...", fg=COLOR_PRESENT)
        
        # Run algorithm in a separate thread to avoid freezing the UI
        threading.Thread(target=self._solve_in_background, args=(algo_name,), daemon=True).start()

    def _solve_in_background(self, algo_name):
        target = self.target_word
        history = []

        if algo_name == "BFS":
            history = bfs_solver.solve(target)
        elif algo_name == "DFS":
            history = dfs_solver.solve(target)
        elif algo_name == "UCS":
            history = ucs_solver.solve(target)
        elif algo_name == "A*":
            history = astar_solver.solve(target)

        if history:
            self.root.after(0, lambda: self._animate_solution(history))
        else:
            self.root.after(0, lambda: self.message_label.config(text="AI Failed to find word!", fg="red"))

    def _animate_solution(self, history):
        self.current_guess_num = 0
        
        delay_step = 0
        for guess, pattern in history:
            # Schedule each guess step
            self.root.after(delay_step, lambda g=guess, p=pattern: self._fill_and_color_row(g, p))
            delay_step += 1500

    def _fill_and_color_row(self, guess, pattern):
        row = self.current_guess_num
        if row >= ROWS: return

        guess = guess.upper()
    
        for col in range(COLS):
            _, lbl = self.cells[row][col]
            lbl.config(text=guess[col])

        for col in range(COLS):
            color = COLOR_ABSENT
            if pattern[col] == 2: color = COLOR_CORRECT
            elif pattern[col] == 1: color = COLOR_PRESENT
            
            frame, lbl = self.cells[row][col]
            lbl.config(bg=color, fg=COLOR_TEXT_FILLED)
            frame.config(bg=color, highlightbackground=color)
        
            if guess[col] in self.key_buttons:
                self.key_buttons[guess[col]].config(bg=color)

        self.current_guess_num += 1
        
        if pattern == (2, 2, 2, 2, 2):
            self.message_label.config(text=f"AI WON using {self.algo_var.get()}!", fg=COLOR_CORRECT)
            self.game_over = True

if __name__ == "__main__":
    root = tk.Tk()
    game = WordleGame(root)
    root.mainloop()