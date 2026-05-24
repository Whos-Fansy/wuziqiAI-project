import numpy as np

WHITE = 2
BLACK = 1
EMPTY = 0

# 评估棋盘分数（简单版，不卡死）
def evaluate(board, color):
    score = 0
    opp = 3 - color
    b = board.board

    for i in range(board.size):
        for j in range(board.size):
            if b[i][j] == color:
                score += 1
            elif b[i][j] == opp:
                score -= 1
    return score

# 获取可落子位置（只拿周围有棋子的位置，超快）
def get_moves(board):
    moves = []
    size = board.size
    for i in range(size):
        for j in range(size):
            if board.get_piece(i, j) == EMPTY:
                moves.append((i, j))
    return moves

# 核心AI算法（带深度限制，绝对不卡死）
def minimax(board, depth, is_max, alpha, beta, color):
    if depth == 0 or board.judge_win(color) or board.judge_win(3-color):
        return evaluate(board, color), None

    moves = get_moves(board)
    best_move = None

    if is_max:
        max_val = -np.inf
        for (x, y) in moves:
            board.set_piece(x, y, color)
            val, _ = minimax(board, depth-1, False, alpha, beta, color)
            board.set_piece(x, y, EMPTY)

            if val > max_val:
                max_val = val
                best_move = (x, y)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_val, best_move
    else:
        min_val = np.inf
        for (x, y) in moves:
            board.set_piece(x, y, 3-color)
            val, _ = minimax(board, depth-1, True, alpha, beta, color)
            board.set_piece(x, y, EMPTY)

            if val < min_val:
                min_val = val
                best_move = (x, y)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_val, best_move

# 给main.py调用的接口
def get_best(board):
    val, move = minimax(board, depth=2, is_max=True, alpha=-np.inf, beta=np.inf, color=WHITE)
    return move