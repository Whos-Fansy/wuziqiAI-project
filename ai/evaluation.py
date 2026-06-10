# -*- coding: utf-8 -*-
"""
ai/evaluation.py - 高级启发式五元组盘面评估引擎 (v3.0)
改进：
  1. 边界感知 — 区分活棋(open)与眠/冲棋(blocked)
  2. 混合窗口不再简单返回0
  3. 重构评分体系，拉开活/眠差距
  4. 中心位置加权
  5. 防守偏置 — 人类威胁权重×2.0
"""

# ---------------------------------------------------------------------------
# 配置常量 (从 config.json 加载)
# ---------------------------------------------------------------------------
import config as _cfg

# 纯棋型评分（玩家 = AI 时为正，玩家 = 人类时为负）
SCORE_FIVE       = _cfg.eval_param("score_five", 100000)
SCORE_OPEN_FOUR  = _cfg.eval_param("score_open_four", 50000)
SCORE_CLOSE_FOUR = _cfg.eval_param("score_close_four", 5000)
SCORE_OPEN_THREE = _cfg.eval_param("score_open_three", 5000)
SCORE_CLOSE_THREE= _cfg.eval_param("score_close_three", 500)
SCORE_OPEN_TWO   = _cfg.eval_param("score_open_two", 200)
SCORE_CLOSE_TWO  = _cfg.eval_param("score_close_two", 50)

# 防守偏置 — 人类棋型的绝对值再乘此系数
DEFENSE_BIAS = _cfg.eval_param("defense_bias", 2.0)

# 位置权重 — 中心衰减系数 (标准差 ≈ size/3)
POSITION_SIGMA_FACTOR = _cfg.eval_param("position_sigma_factor", 0.333)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------
def _is_open_ends(size, board, r, c, dr, dc, stone):
    """
    检查以 (r,c) 为起点的5格线段两端是否为空格（或越界视为墙壁）
    返回 (open_start, open_end)
    """
    # 起点前
    pr, pc = r - dr, c - dc
    open_start = (0 <= pr < size and 0 <= pc < size and board[pr][pc] == 0)
    # 终点后 (起点 + 4 格)
    nr, nc = r + 4 * dr, c + 4 * dc
    open_end = (0 <= nr < size and 0 <= nc < size and board[nr][nc] == 0)
    return open_start, open_end


def _position_weight(r, c, size):
    """
    中心加权：棋盘中心权重≈1.0，边缘衰减至≈0.6
    使用二维高斯距离公式
    """
    center = (size - 1) / 2.0
    sigma = size * POSITION_SIGMA_FACTOR
    dist_sq = (r - center) ** 2 + (c - center) ** 2
    # 基础权重0.6，中心加成0.4 (总计1.0在中心)
    weight = 0.6 + 0.4 * (1.0 / (2.71828 ** (dist_sq / (2 * sigma * sigma))))
    return max(weight, 0.6)


def _score_window(board, r, c, dr, dc, stone, size):
    """
    对从 (r,c) 沿 (dr,dc) 方向的5格窗口进行精细打分。
    返回绝对分值（正数），调用方根据 stone 决定符号。
    stone: 1=人类(黑子), 2=AI(白子)
    """
    # 收集5格
    cells = []
    for i in range(5):
        rr, cc = r + i * dr, c + i * dc
        cells.append(board[rr][cc])

    stone_count = cells.count(stone)
    opp_count = cells.count(3 - stone)  # 对手棋子数
    space_count = cells.count(0)

    # 混合填充：同时包含双方棋子，无价值
    if stone_count > 0 and opp_count > 0:
        return 0

    # 纯空格窗口
    if stone_count == 0:
        return 0

    open_start, open_end = _is_open_ends(size, board, r, c, dr, dc, stone)

    # ---------- 纯子数窗口打分 ----------
    if stone_count == 5:
        return SCORE_FIVE

    if stone_count == 4:
        if open_start and open_end:
            return SCORE_OPEN_FOUR    # 活四：两端全空（必胜）
        elif open_start or open_end:
            return SCORE_CLOSE_FOUR   # 冲四：仅一端为空
        else:
            return 0                  # 两端全封，无威胁

    if stone_count == 3:
        if open_start and open_end:
            return SCORE_OPEN_THREE   # 活三
        elif open_start or open_end:
            return SCORE_CLOSE_THREE  # 眠三（一端被封）
        else:
            return 0                  # 两端全封，无威胁

    if stone_count == 2:
        if open_start and open_end:
            return SCORE_OPEN_TWO     # 活二
        elif open_start or open_end:
            return SCORE_CLOSE_TWO    # 眠二（一端被封）
        else:
            return 0                  # 两端全封，无威胁

    return 0


def evaluate_board(game):
    """
    全盘扫描函数：滑动窗口遍历全盘四个方向
    返回值越高，对AI越有利；返回值越低，对人类越有利。
    接口与旧版完全兼容。
    """
    total_score = 0
    size = game.size
    board = game.board

    # 四个扫描方向：(dr, dc)
    directions = [
        (0, 1),   # 横向 →
        (1, 0),   # 竖向 ↓
        (1, 1),   # 主对角线 ↘
        (1, -1),  # 反对角线 ↙
    ]

    for dr, dc in directions:
        # 根据方向计算合法的行列范围
        if dc == 1 and dr == 0:          # 横向
            row_range = range(size)
            col_range = range(size - 4)
        elif dr == 1 and dc == 0:        # 竖向
            row_range = range(size - 4)
            col_range = range(size)
        elif dr == 1 and dc == 1:        # 主对角线
            row_range = range(size - 4)
            col_range = range(size - 4)
        else:                             # 反对角线 (dr=1, dc=-1)
            row_range = range(size - 4)
            col_range = range(4, size)

        for r in row_range:
            for c in col_range:
                # ---- 评估 AI (白子, 2) 的进攻棋型 ----
                ai_score = _score_window(board, r, c, dr, dc, stone=2, size=size)
                if ai_score > 0:
                    # 取窗口中心位置做加权
                    mid_r, mid_c = r + 2 * dr, c + 2 * dc
                    if dc == -1:
                        mid_r, mid_c = r + 2, c - 2
                    else:
                        mid_r, mid_c = r + 2 * dr, c + 2 * dc
                    w = _position_weight(mid_r, mid_c, size)
                    total_score += ai_score * w

                # ---- 评估 人类 (黑子, 1) 的进攻棋型（防守评分）----
                human_score = _score_window(board, r, c, dr, dc, stone=1, size=size)
                if human_score > 0:
                    # 位置权重（同AI）
                    if dc == -1:
                        mid_r, mid_c = r + 2, c - 2
                    else:
                        mid_r, mid_c = r + 2 * dr, c + 2 * dc
                    w = _position_weight(mid_r, mid_c, size)
                    # 防守偏置：人类棋型威胁权重加倍
                    total_score -= human_score * w * DEFENSE_BIAS

    return total_score