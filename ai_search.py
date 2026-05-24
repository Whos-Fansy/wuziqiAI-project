# Minimax + AlphaBeta 算法 成员1负责
import copy
from board import *

DEPTH = 4   # 搜索深度，可调

class AI:
    def __init__(self):
        pass

    def alphabeta(self, board, depth, alpha, beta, is_max):
        if depth <= 0:
            return board.evaluate(WHITE)
        empty = board.get_empty()
        if not empty:
            return 0

        if is_max:
            max_val = -float("inf")
            for x,y in empty:
                new_b = copy.deepcopy(board)
                new_b.set_piece(x,y,WHITE)
                if new_b.judge_win(WHITE):
                    return SCORE_MAP["five"]
                val = self.alphabeta(new_b, depth-1, alpha, beta, False)
                max_val = max(max_val, val)
                alpha = max(alpha, max_val)
                if alpha >= beta:
                    break
            return max_val
        else:
            min_val = float("inf")
            for x,y in empty:
                new_b = copy.deepcopy(board)
                new_b.set_piece(x,y,BLACK)
                if new_b.judge_win(BLACK):
                    return -SCORE_MAP["five"]
                val = self.alphabeta(new_b, depth-1, alpha, beta, True)
                min_val = min(min_val, val)
                beta = min(beta, min_val)
                if alpha >= beta:
                    break
            return min_val

    def get_best(self, board):
        best_sc = -float("inf")
        best_pos = None
        empty = board.get_empty()
        for x,y in empty:
            nb = copy.deepcopy(board)
            nb.set_piece(x,y,WHITE)
            sc = self.alphabeta(nb, DEPTH-1, -float("inf"), float("inf"), False)
            if sc > best_sc:
                best_sc = sc
                best_pos = (x,y)
        return best_pos
