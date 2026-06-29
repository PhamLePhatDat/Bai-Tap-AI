import tkinter as tk
from tkinter import ttk
import threading

from tictactoe_logic import get_ai_move, check_winner, get_empty_cells

BG_DARK      = "#1E1E2E"
BG_PANEL     = "#181825"
BG_CELL      = "#313244"
BG_CELL_HVR  = "#45475A"
BG_CELL_WIN  = "#A6E3A1"  
BG_CELL_LOSE = "#F38BA8"  
BG_CELL_DRAW = "#FAB387"  

FG_WHITE  = "#CDD6F4"
FG_MUTED  = "#6C7086"
FG_X      = "#89B4FA"  
FG_O      = "#F38BA8"   
FG_ACCENT = "#CBA6F7"  
FG_GREEN  = "#A6E3A1"
FG_YELLOW = "#F9E2AF"

FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_CELL   = ("Segoe UI", 40, "bold")
FONT_LABEL  = ("Segoe UI", 10)
FONT_STAT   = ("Segoe UI", 11, "bold")
FONT_BTN    = ("Segoe UI", 10, "bold")
FONT_ALGO   = ("Segoe UI", 10)

ALGO_INFO = {
    "minimax": (
        "Minimax",
        "Duyệt toàn bộ cây trò chơi, chọn nước đi tối ưu tuyệt đối.\n"
        "Máy không bao giờ thua nếu thuật toán chạy đúng."
    ),
    "alphabeta": (
        "Alpha-Beta Pruning",
        "Cải tiến Minimax: cắt tỉa nhánh không cần thiết (α-β cut-off).\n"
        "Kết quả giống Minimax nhưng nhanh hơn đáng kể."
    ),
    "expectimax": (
        "Expectimax",
        "Nút CHANCE thay thế nút MIN: mô hình người chơi ngẫu nhiên.\n"
        "AI mạnh nhưng đôi khi khai thác được nếu chơi bất ngờ."
    ),
}


class TicTacToeApp(tk.Frame):
    """Frame chính của game XO – nhúng vào Launcher."""

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._build_ui()
        self._new_game()

    def _build_ui(self):
        left = tk.Frame(self, bg=BG_DARK)
        left.pack(side="left", fill="both", expand=True, padx=(16, 8), pady=16)

        tk.Label(left, text="Cờ XO 3×3  –  Người vs Máy",
                 font=FONT_TITLE, bg=BG_DARK, fg=FG_ACCENT).pack(anchor="w", pady=(0, 10))

        # Trạng thái lượt
        self.status_var = tk.StringVar(value="Lượt của bạn (X)")
        tk.Label(left, textvariable=self.status_var,
                 font=("Segoe UI", 12, "bold"), bg=BG_DARK, fg=FG_YELLOW,
                 anchor="w").pack(anchor="w", pady=(0, 8))

        # Bảng 3×3
        board_outer = tk.Frame(left, bg=BG_PANEL, bd=0)
        board_outer.pack(anchor="w")
        self.cell_btns = []
        for i in range(9):
            btn = tk.Button(board_outer, text="", font=FONT_CELL,
                            width=3, height=1,
                            bg=BG_CELL, fg=FG_WHITE,
                            activebackground=BG_CELL_HVR,
                            relief="flat", bd=0,
                            cursor="hand2",
                            command=lambda idx=i: self._on_click(idx))
            btn.grid(row=i // 3, column=i % 3, padx=4, pady=4)
            self.cell_btns.append(btn)

        # Thống kê điểm
        score_frame = tk.Frame(left, bg=BG_DARK)
        score_frame.pack(anchor="w", pady=(14, 0), fill="x")

        labels = [("Bạn (X)", "win"), ("Hòa", "draw"), ("Máy (O)", "lose")]
        self.score_vars = {}
        for col, (lbl, key) in enumerate(labels):
            card = tk.Frame(score_frame, bg=BG_PANEL, padx=14, pady=8)
            card.grid(row=0, column=col, padx=4)
            v = tk.StringVar(value="0")
            self.score_vars[key] = v
            color = FG_X if key == "win" else (FG_O if key == "lose" else FG_YELLOW)
            tk.Label(card, textvariable=v, font=("Segoe UI", 22, "bold"),
                     bg=BG_PANEL, fg=color).pack()
            tk.Label(card, text=lbl, font=FONT_LABEL,
                     bg=BG_PANEL, fg=FG_MUTED).pack()

        self.scores = {"win": 0, "draw": 0, "lose": 0}

        # Nút Chơi lại
        tk.Button(left, text="⟳  Chơi lại", font=FONT_BTN,
                  bg=BG_PANEL, fg=FG_WHITE, activebackground=BG_CELL_HVR,
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._new_game).pack(anchor="w", pady=(14, 0))

        # Cột phải: cài đặt
        right = tk.Frame(self, bg=BG_PANEL, width=260)
        right.pack(side="right", fill="y", padx=(8, 16), pady=16)
        right.pack_propagate(False)

        tk.Label(right, text="Cài đặt", font=("Segoe UI", 12, "bold"),
                 bg=BG_PANEL, fg=FG_ACCENT).pack(anchor="w", padx=12, pady=(12, 8))

        # Chọn quân
        tk.Label(right, text="Bạn chơi quân:", font=FONT_LABEL,
                 bg=BG_PANEL, fg=FG_MUTED).pack(anchor="w", padx=12)
        self.side_var = tk.StringVar(value="X")
        side_frame = tk.Frame(right, bg=BG_PANEL)
        side_frame.pack(anchor="w", padx=12, pady=(4, 12))
        for s in ("X", "O"):
            rb = tk.Radiobutton(side_frame, text=f"{'✕' if s=='X' else '○'}  {s}",
                                variable=self.side_var, value=s,
                                font=FONT_ALGO, bg=BG_PANEL,
                                fg=FG_X if s == "X" else FG_O,
                                selectcolor=BG_DARK,
                                activebackground=BG_PANEL,
                                command=self._new_game)
            rb.pack(side="left", padx=(0, 12))

        # Separator
        tk.Frame(right, bg=FG_MUTED, height=1).pack(fill="x", padx=12, pady=4)

        # Chọn thuật toán
        tk.Label(right, text="Thuật toán AI:", font=FONT_LABEL,
                 bg=BG_PANEL, fg=FG_MUTED).pack(anchor="w", padx=12, pady=(8, 4))
        self.algo_var = tk.StringVar(value="minimax")
        for key, (name, _) in ALGO_INFO.items():
            rb = tk.Radiobutton(right, text=name,
                                variable=self.algo_var, value=key,
                                font=FONT_ALGO, bg=BG_PANEL, fg=FG_WHITE,
                                selectcolor=BG_DARK, activebackground=BG_PANEL,
                                command=self._on_algo_change)
            rb.pack(anchor="w", padx=16, pady=2)

        # Mô tả thuật toán
        self.algo_desc = tk.Label(right, text="", font=("Segoe UI", 9),
                                  bg=BG_PANEL, fg=FG_MUTED,
                                  wraplength=220, justify="left")
        self.algo_desc.pack(anchor="w", padx=12, pady=(6, 0))
        self._update_algo_desc()

        # Separator
        tk.Frame(right, bg=FG_MUTED, height=1).pack(fill="x", padx=12, pady=12)

        # Độ sâu Expectimax
        self.depth_frame = tk.Frame(right, bg=BG_PANEL)
        self.depth_frame.pack(anchor="w", padx=12, fill="x")
        tk.Label(self.depth_frame, text="Độ sâu Expectimax:", font=FONT_LABEL,
                 bg=BG_PANEL, fg=FG_MUTED).pack(anchor="w")
        depth_row = tk.Frame(self.depth_frame, bg=BG_PANEL)
        depth_row.pack(anchor="w", fill="x")
        self.depth_var = tk.IntVar(value=6)
        self.depth_label = tk.Label(depth_row, text="6", font=FONT_STAT,
                                    bg=BG_PANEL, fg=FG_WHITE, width=2)
        self.depth_label.pack(side="right")
        tk.Scale(depth_row, from_=1, to=9, orient="horizontal",
                 variable=self.depth_var, bg=BG_PANEL, fg=FG_WHITE,
                 highlightthickness=0, troughcolor=BG_DARK,
                 command=lambda v: self.depth_label.config(text=v)
                 ).pack(side="left", fill="x", expand=True)
        self.depth_frame.pack_forget()  # ẩn mặc định

        # Log di chuyển
        tk.Frame(right, bg=FG_MUTED, height=1).pack(fill="x", padx=12, pady=12)
        tk.Label(right, text="Lịch sử nước đi:", font=FONT_LABEL,
                 bg=BG_PANEL, fg=FG_MUTED).pack(anchor="w", padx=12)
        log_outer = tk.Frame(right, bg=BG_PANEL)
        log_outer.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.log_box = tk.Text(log_outer, font=("Consolas", 10),
                               bg=BG_DARK, fg=FG_WHITE,
                               relief="flat", state="disabled",
                               height=8, wrap="word")
        self.log_box.pack(fill="both", expand=True)


    def _new_game(self):
        self.board = [None] * 9
        self.game_over = False
        self.thinking = False
        self.human_side = self.side_var.get()
        self.ai_side = "O" if self.human_side == "X" else "X"
        self.current_player = "X"   # X luôn đi trước
        self._clear_log()
        self._render_board()
        self._update_status()

        if self.human_side == "O":
            self.after(200, self._ai_move)

    def _on_click(self, idx):
        if self.game_over or self.thinking:
            return
        if self.current_player != self.human_side:
            return
        if self.board[idx] is not None:
            return
        self.board[idx] = self.human_side
        self._log(f"Bạn  → ô {idx + 1}")
        result, line = check_winner(self.board)
        if result:
            self._end_game(result, line)
            return
        self.current_player = self.ai_side
        self._render_board()
        self._update_status()
        self.thinking = True
        threading.Thread(target=self._ai_move, daemon=True).start()

    def _ai_move(self):
        algo = self.algo_var.get()
        depth = self.depth_var.get()
        move = get_ai_move(self.board[:], self.ai_side, self.human_side,
                           algorithm=algo, depth=depth)
        self.after(0, lambda: self._apply_ai_move(move))

    def _apply_ai_move(self, move):
        self.thinking = False
        if self.game_over:
            return
        self.board[move] = self.ai_side
        algo_name = ALGO_INFO[self.algo_var.get()][0]
        self._log(f"Máy ({algo_name}) → ô {move + 1}")
        result, line = check_winner(self.board)
        self.current_player = self.human_side
        if result:
            self._end_game(result, line)
            return
        self._render_board()
        self._update_status()

    def _end_game(self, result, line):
        self.game_over = True
        highlight = BG_CELL_WIN
        if result == self.human_side:
            msg = "🎉  Bạn thắng!"
            color = FG_GREEN
            self.scores["win"] += 1
        elif result == self.ai_side:
            msg = "Máy thắng! Thử lại nhé."
            color = FG_O
            highlight = BG_CELL_LOSE
            self.scores["lose"] += 1
        else:
            msg = "Hòa nhau!"
            color = FG_YELLOW
            highlight = BG_CELL_DRAW
            self.scores["draw"] += 1

        self._render_board(win_line=line, highlight_color=highlight)
        self.status_var.set(msg)
        self._update_score_display()
        self._log(f"→ {msg}")

    def _render_board(self, win_line=(), highlight_color=BG_CELL_WIN):
        for i, btn in enumerate(self.cell_btns):
            val = self.board[i]
            if i in win_line:
                bg = highlight_color
                fg = "#1E1E2E"
            elif val is None:
                bg = BG_CELL
                fg = FG_WHITE
            else:
                bg = BG_CELL
                fg = FG_X if val == "X" else FG_O

            text = "✕" if val == "X" else ("○" if val == "O" else "")
            is_clickable = (
                val is None
                and not self.game_over
                and not self.thinking
                and self.current_player == self.human_side
            )
            btn.config(text=text, bg=bg, fg=fg,
                       state="normal" if is_clickable else "disabled",
                       disabledforeground=fg)

    def _update_status(self):
        if self.game_over:
            return
        if self.current_player == self.human_side:
            sym = "✕" if self.human_side == "X" else "○"
            self.status_var.set(f"Lượt của bạn ({sym})")
        else:
            self.status_var.set("Máy đang suy nghĩ…")

    def _update_score_display(self):
        for key, v in self.score_vars.items():
            v.set(str(self.scores[key]))

    def _on_algo_change(self):
        key = self.algo_var.get()
        if key == "expectimax":
            self.depth_frame.pack(anchor="w", padx=12, fill="x")
        else:
            self.depth_frame.pack_forget()
        self._update_algo_desc()
        self._new_game()

    def _update_algo_desc(self):
        key = self.algo_var.get()
        _, desc = ALGO_INFO[key]
        self.algo_desc.config(text=desc)

    def _log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")
