WINS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # hàng ngang
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # hàng dọc
    (0, 4, 8), (2, 4, 6),              # đường chéo
]


def check_winner(board):
    """
    Kiểm tra người thắng.
    Trả về (winner, win_line) trong đó winner là 'X', 'O', 'draw', hoặc None.
    """
    for a, b, c in WINS:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], (a, b, c)
    if all(cell is not None for cell in board):
        return 'draw', ()
    return None, ()


def get_empty_cells(board):
    return [i for i, v in enumerate(board) if v is None]

def _minimax(board, is_maximizing, ai_side, human_side):
    winner, _ = check_winner(board)
    if winner == ai_side:
        return 10 - (9 - len(get_empty_cells(board)))
    if winner == human_side:
        return -10 + (9 - len(get_empty_cells(board)))
    if winner == 'draw':
        return 0

    moves = get_empty_cells(board)
    if is_maximizing:
        best = -999
        for m in moves:
            board[m] = ai_side
            best = max(best, _minimax(board, False, ai_side, human_side))
            board[m] = None
        return best
    else:
        best = 999
        for m in moves:
            board[m] = human_side
            best = min(best, _minimax(board, True, ai_side, human_side))
            board[m] = None
        return best


def minimax_best_move(board, ai_side, human_side):
    moves = get_empty_cells(board)
    best_val, best_move = -999, moves[0]
    for m in moves:
        board[m] = ai_side
        val = _minimax(board, False, ai_side, human_side)
        board[m] = None
        if val > best_val:
            best_val, best_move = val, m
    return best_move

def _alphabeta(board, is_maximizing, alpha, beta, ai_side, human_side):
    winner, _ = check_winner(board)
    if winner == ai_side:
        return 10 - (9 - len(get_empty_cells(board)))
    if winner == human_side:
        return -10 + (9 - len(get_empty_cells(board)))
    if winner == 'draw':
        return 0

    moves = get_empty_cells(board)
    if is_maximizing:
        best = -999
        for m in moves:
            board[m] = ai_side
            best = max(best, _alphabeta(board, False, alpha, beta, ai_side, human_side))
            board[m] = None
            alpha = max(alpha, best)
            if beta <= alpha:
                break  # Beta cut-off
        return best
    else:
        best = 999
        for m in moves:
            board[m] = human_side
            best = min(best, _alphabeta(board, True, alpha, beta, ai_side, human_side))
            board[m] = None
            beta = min(beta, best)
            if beta <= alpha:
                break  # Alpha cut-off
        return best


def alphabeta_best_move(board, ai_side, human_side):
    """Trả về nước đi tốt nhất theo Alpha-Beta Pruning."""
    moves = get_empty_cells(board)
    best_val, best_move = -999, moves[0]
    alpha, beta = -999, 999
    for m in moves:
        board[m] = ai_side
        val = _alphabeta(board, False, alpha, beta, ai_side, human_side)
        board[m] = None
        if val > best_val:
            best_val, best_move = val, m
        alpha = max(alpha, best_val)
    return best_move

def _expectimax(board, is_maximizing, depth, ai_side, human_side):
    winner, _ = check_winner(board)
    if winner == ai_side:
        return 10
    if winner == human_side:
        return -10
    if winner == 'draw':
        return 0

    moves = get_empty_cells(board)
    if not moves or depth == 0:
        return 0

    if is_maximizing:
        best = -999
        for m in moves:
            board[m] = ai_side
            val = _expectimax(board, False, depth - 1, ai_side, human_side)
            board[m] = None
            best = max(best, val)
        return best
    else:
       
        total = 0
        for m in moves:
            board[m] = human_side
            total += _expectimax(board, True, depth - 1, ai_side, human_side)
            board[m] = None
        return total / len(moves)


def expectimax_best_move(board, ai_side, human_side, depth=9):
    """Trả về nước đi tốt nhất theo Expectimax."""
    moves = get_empty_cells(board)
    best_val, best_move = -999, moves[0]
    for m in moves:
        board[m] = ai_side
        val = _expectimax(board, False, depth - 1, ai_side, human_side)
        board[m] = None
        if val > best_val:
            best_val, best_move = val, m
    return best_move

def get_ai_move(board, ai_side, human_side, algorithm='minimax', depth=9):
    if algorithm == 'alphabeta':
        return alphabeta_best_move(board, ai_side, human_side)
    elif algorithm == 'expectimax':
        return expectimax_best_move(board, ai_side, human_side, depth=depth)
    else:
        return minimax_best_move(board, ai_side, human_side)
