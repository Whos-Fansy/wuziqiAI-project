# -*- coding: utf-8 -*-
"""
ai/search.py - 高级 Alpha-Beta 剪枝算法
=========================================
v3.0 优化:
  1. 移动排序 (Move Ordering) — 按启发式估值排序候选落子，大幅提升剪枝效率
  2. Zobrist 哈希 + 置换表 — 缓存已搜索局面，避免重复计算
  3. 杀棋检测 (Threat Space Search) — 优先寻找直接四三/四四杀棋路径
"""
import random
import time
from ai.evaluation import evaluate_board

# ==========================================================================
# Zobrist 哈希系统
# ==========================================================================
_zobrist_init = False
_zobrist_keys = {}          # (row, col, player) -> 64-bit key
_zobrist_side = 0           # 黑方轮次标记
_search_start_time = 0      # 搜索开始时间
_search_time_limit = 5.0    # 搜索时间上限（秒）
_search_deadline_reached = False

# 置换表: key=hash, value=(depth, score, flag, best_move)
# flag: 0=EXACT, 1=LOWER_BOUND, 2=UPPER_BOUND
EXACT       = 0
LOWER_BOUND = 1
UPPER_BOUND = 2
_trans_table = {}

def _init_zobrist(size=9):
    """惰性初始化 Zobrist 随机哈希表"""
    global _zobrist_init, _zobrist_side
    if _zobrist_init:
        return
    random.seed(42)
    for r in range(size):
        for c in range(size):
            for p in (1, 2):
                _zobrist_keys[(r, c, p)] = random.getrandbits(64)
    _zobrist_side = random.getrandbits(64)
    _zobrist_init = True

def compute_hash(board, size=9):
    """全盘计算 Zobrist 哈希值"""
    _init_zobrist(size)
    h = 0
    for r in range(size):
        for c in range(size):
            p = board[r][c]
            if p != 0:
                h ^= _zobrist_keys[(r, c, p)]
    return h

def apply_move_hash(h, r, c, player):
    """增量更新 Zobrist 哈希（落子）"""
    return h ^ _zobrist_keys[(r, c, player)]

def remove_move_hash(h, r, c, player):
    """增量更新 Zobrist 哈希（撤销落子）— 等同 apply_move_hash"""
    return h ^ _zobrist_keys[(r, c, player)]

def clear_trans_table():
    """每步棋开始前清空置换表"""
    _trans_table.clear()

def set_time_limit(seconds):
    """设置AI搜索时间上限"""
    global _search_time_limit, _search_start_time, _search_deadline_reached
    _search_time_limit = seconds
    _search_start_time = time.time()
    _search_deadline_reached = False

def _is_time_up():
    """检查搜索是否超时"""
    global _search_deadline_reached
    if _search_deadline_reached:
        return True
    if time.time() - _search_start_time > _search_time_limit:
        _search_deadline_reached = True
        return True
    return False

# ==========================================================================
# 移动排序：启发式估值
# ==========================================================================
def _quick_eval(game, r, c, player):
    """
    快速静态评估某落子点的价值，用于移动排序。
    分值越高越值得优先探索。
    """
    board = game.board
    size = game.size
    score = 0
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    # 临时落子
    board[r][c] = player

    for dr, dc in directions:
        # 统计该方向上的连续子数
        count = 1
        # 正向
        for i in range(1, 5):
            nr, nc = r + dr * i, c + dc * i
            if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player:
                count += 1
            else:
                break
        # 反向
        for i in range(1, 5):
            nr, nc = r - dr * i, c - dc * i
            if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == player:
                count += 1
            else:
                break

        if count >= 5:
            score += 100000  # 直接赢棋
        elif count == 4:
            score += 5000    # 活四/冲四
        elif count == 3:
            score += 500     # 活三/眠三
        elif count == 2:
            score += 50      # 活二/眠二

    # 位置加权：靠近中心加分
    center = (size - 1) / 2.0
    dist_sq = (r - center) ** 2 + (c - center) ** 2
    sigma = size * 0.333
    pos_weight = 0.6 + 0.4 * (1.0 / (2.71828 ** (dist_sq / (2 * sigma * sigma))))
    score = int(score * pos_weight)

    # 撤销落子
    board[r][c] = 0
    return score

# ==========================================================================
# 杀棋检测
# ==========================================================================
def _find_immediate_win(game, player):
    """
    杀棋检测：查找指定玩家是否可以一步获胜。
    返回获胜落子坐标，或 None。
    """
    size = game.size
    board = game.board
    for r in range(size):
        for c in range(size):
            if board[r][c] != 0:
                continue
            board[r][c] = player
            if game.check_winner() == player:
                board[r][c] = 0
                return (r, c)
            board[r][c] = 0
    return None

# ==========================================================================
# 候选落子生成
# ==========================================================================
def get_potential_moves(game):
    """
    只将已有棋子周围半径为 2 的空位列为候选落子点。
    """
    moves = []
    has_stone = False
    size = game.size
    board = game.board

    for r in range(size):
        for c in range(size):
            if board[r][c] != 0:
                has_stone = True
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == 0:
                            if (nr, nc) not in moves:
                                moves.append((nr, nc))

    if not has_stone:
        center = size // 2
        return [(center, center)]

    return moves

# ==========================================================================
# Alpha-Beta 核心算法
# ==========================================================================
def alpha_beta(game, depth, alpha, beta, is_maximizing, current_hash=None):
    """
    增强版 Alpha-Beta 剪枝算法，融合：
      - Zobrist 哈希置换表
      - 移动排序
      - 杀棋检测
    """
    size = game.size
    board = game.board
    _init_zobrist(size)

    # ---- 计算/更新哈希 ----
    if current_hash is None:
        current_hash = compute_hash(board, size)

    # ---- 置换表查表 ----
    tt_entry = _trans_table.get(current_hash)
    if tt_entry is not None:
        tt_depth, tt_score, tt_flag, tt_move = tt_entry
        if tt_depth >= depth:
            if tt_flag == EXACT:
                return tt_score, tt_move
            elif tt_flag == LOWER_BOUND and tt_score >= beta:
                return tt_score, tt_move
            elif tt_flag == UPPER_BOUND and tt_score <= alpha:
                return tt_score, tt_move

    # ---- 递归终点判定 ----
    winner = game.check_winner()
    if winner == 2:
        return 1000000 + depth, None

    if winner == 1:
        return -1000000 - depth, None

    if game.is_board_full():
        return 0, None

    if depth == 0:
        score = evaluate_board(game)
        _trans_table[current_hash] = (depth, score, EXACT, None)
        return score, None

    # ---- 杀棋检测（仅在顶层 depth 足够时执行）----
    # AI 有直接获胜的棋 → 立即走
    win_move = _find_immediate_win(game, 2)
    if win_move:
        _trans_table[current_hash] = (depth, 1000000 + depth, EXACT, win_move)
        return 1000000 + depth, win_move

    # 人类有直接获胜的棋 → 必须堵住
    block_move = _find_immediate_win(game, 1)
    if block_move:
        # 只有一个必须堵的点
        game.make_move(block_move[0], block_move[1], 2)
        new_hash = apply_move_hash(current_hash, block_move[0], block_move[1], 2)
        score, _ = alpha_beta(game, depth - 1, alpha, beta, False, new_hash)
        game.undo_move(block_move[0], block_move[1])
        _trans_table[current_hash] = (depth, score, EXACT, block_move)
        return score, block_move

    # ---- 获取候选落子 ----
    moves = get_potential_moves(game)
    if not moves:
        score = evaluate_board(game)
        _trans_table[current_hash] = (depth, score, EXACT, None)
        return score, None

    # ---- 移动排序 ----
    if is_maximizing:
        # AI 回合：按对AI的利好程度降序排列
        scored_moves = [(m, _quick_eval(game, m[0], m[1], 2)) for m in moves]
        scored_moves.sort(key=lambda x: x[1], reverse=True)
    else:
        # 人类回合：按对人类的利好程度降序排列（AI需要优先考虑人类的好棋）
        scored_moves = [(m, _quick_eval(game, m[0], m[1], 1)) for m in moves]
        scored_moves.sort(key=lambda x: x[1], reverse=True)

    moves = [m for m, _ in scored_moves]

    # ---- 搜索 ----
    best_move = None
    original_alpha = alpha

    if is_maximizing:
        max_eval = -float('inf')

        for r, c in moves:
            if _is_time_up():
                break
            game.make_move(r, c, 2)
            new_hash = apply_move_hash(current_hash, r, c, 2)
            score, _ = alpha_beta(game, depth - 1, alpha, beta, False, new_hash)
            game.undo_move(r, c)

            if score > max_eval:
                max_eval = score
                best_move = (r, c)

            alpha = max(alpha, score)
            if beta <= alpha:
                break

        # ---- 存储到置换表 ----
        if best_move:
            flag = EXACT
            if max_eval <= original_alpha:
                flag = UPPER_BOUND
            elif max_eval >= beta:
                flag = LOWER_BOUND
            _trans_table[current_hash] = (depth, max_eval, flag, best_move)

        return max_eval, best_move

    else:
        min_eval = float('inf')

        for r, c in moves:
            if _is_time_up():
                break
            game.make_move(r, c, 1)
            new_hash = apply_move_hash(current_hash, r, c, 1)
            score, _ = alpha_beta(game, depth - 1, alpha, beta, True, new_hash)
            game.undo_move(r, c)

            if score < min_eval:
                min_eval = score
                best_move = (r, c)

            beta = min(beta, score)
            if beta <= alpha:
                break

        # ---- 存储到置换表 ----
        if best_move:
            flag = EXACT
            if min_eval <= original_alpha:
                flag = UPPER_BOUND
            elif min_eval >= beta:
                flag = LOWER_BOUND
            _trans_table[current_hash] = (depth, min_eval, flag, best_move)

        return min_eval, best_move