# -*- coding: utf-8 -*-
import config as _cfg

class GomokuGame:
    def __init__(self, size=None):
        self.size = size if size is not None else _cfg.game("board_size", 9)
        # 棋盘状态表示：0代表空格，1代表人类玩家（黑子），2代表AI（白子）
        self.board = [[0] * size for _ in range(size)]
        # 当前执子方，默认黑子（1）先下
        self.current_player = 1 

    def is_legal_move(self, r, c):
        """检查落子位置是否合法"""
        return 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == 0

    def make_move(self, r, c, player):
        """尝试落子，成功返回 True，失败返回 False"""
        if self.is_legal_move(r, c):
            self.board[r][c] = player
            return True
        return False

    def undo_move(self, r, c):
        """
        【核心优化】撤销 (r, c) 处的落子。
        这是写 Minimax 树搜索时的神技，能避免频繁复制整个棋盘，极大提升运算效率！
        """
        if 0 <= r < self.size and 0 <= c < self.size:
            self.board[r][c] = 0

    def check_winner(self):
        """
        检查是否有玩家获胜
        返回 1 代表人类胜，2 代表AI胜，0 代表尚未分出胜负或平局
        """
        # 四个扫描方向：横、竖、正对角线、反对角线
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(self.size):
            for c in range(self.size):
                player = self.board[r][c]
                if player == 0:
                    continue  # 空格不需要检查

                for dr, dc in directions:
                    count = 1
                    # 向选定方向连续检查4个棋子
                    for i in range(1, 5):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr][nc] == player:
                            count += 1
                        else:
                            break

                    if count == 5:
                        return player  # 找到连续5个同色子，返回赢家
        return 0

    def get_winning_line(self):
        """获取获胜的五连子坐标列表"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(self.size):
            for c in range(self.size):
                player = self.board[r][c]
                if player == 0:
                    continue

                for dr, dc in directions:
                    count = 1
                    positions = [(r, c)]
                    # 向选定方向连续检查4个棋子
                    for i in range(1, 5):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr][nc] == player:
                            count += 1
                            positions.append((nr, nc))
                        else:
                            break

                    if count == 5:
                        return positions
        return []

    def is_board_full(self):
        """检查棋盘是否下满（用于判断平局）"""
        for row in self.board:
            if 0 in row:
                return False
        return True

    def reset(self):
        """重置游戏状态"""
        self.board = [[0] * self.size for _ in range(self.size)]
        self.current_player = 1

    def get_ai_move(self, depth):
        """获取AI的最佳移动（深度搜索）"""
        from ai.search import alpha_beta, clear_trans_table, compute_hash, set_time_limit
        # 每步棋开始前清空置换表，设置5秒思考时间上限
        clear_trans_table()
        set_time_limit(5.0)
        current_hash = compute_hash(self.board, self.size)
        score, best_move = alpha_beta(
            self,
            depth=depth,
            alpha=-float('inf'),
            beta=float('inf'),
            is_maximizing=True,
            current_hash=current_hash
        )
        return best_move
