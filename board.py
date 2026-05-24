# 棋盘 + 评估函数模块 成员2负责
import numpy as np

EMPTY = 0
BLACK = 1
WHITE = 2

# 棋型权重
SCORE_MAP = {
    "five": 100000,
    "live4": 12000,
    "sleep4": 1000,
    "live3": 500,
    "sleep3": 100,
    "live2": 50,
    "sleep2": 10
}

class Board:
    def __init__(self, size=9):
        self.size = size
        self.board = np.zeros((size, size), dtype=int)

    def reset(self):
        self.board = np.zeros((self.size, self.size), dtype=int)

    def is_in_board(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def set_piece(self, x, y, color):
        self.board[y][x] = color

    def is_empty(self, x, y):
        return self.board[y][x] == EMPTY

    # 判断输赢
    def judge_win(self, color):
        dirs = [(1,0),(0,1),(1,1),(1,-1)]
        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x] == color:
                    for dx, dy in dirs:
                        cnt = 1
                        nx, ny = x+dx, y+dy
                        while self.is_in_board(nx, ny) and self.board[ny][nx]==color:
                            cnt += 1
                            nx += dx
                            ny += dy
                        if cnt >= 5:
                            return True
        return False

    # 启发式评估函数
    def evaluate(self, color):
        score = 0
        opp = WHITE if color==BLACK else BLACK
        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x]==color:
                    score += self.get_point_score(x,y,color)
                elif self.board[y][x]==opp:
                    score -= self.get_point_score(x,y,opp)
        return score

    def get_point_score(self,x,y,color):
        dirs = [(1,0),(0,1),(1,1),(1,-1)]
        max_s = 0
        for dx, dy in dirs:
            line = self.get_line(x,y,dx,dy,color)
            s = self.calc_line_score(line)
            max_s = max(max_s, s)
        return max_s

    def get_line(self,x,y,dx,dy,color):
        line = []
        for i in range(-4,5):
            nx = x + dx*i
            ny = y + dy*i
            if self.is_in_board(nx,ny):
                line.append(self.board[ny][nx])
            else:
                line.append(-1)
        return line

    def calc_line_score(self,line):
        s = 0
        str_line = "".join(map(str,line))
        if "11111" in str_line or "22222" in str_line:
            s = SCORE_MAP["five"]
        elif "011110" in str_line or "022220" in str_line:
            s = SCORE_MAP["live4"]
        elif "11110" in str_line or "01111" in str_line:
            s = SCORE_MAP["sleep4"]
        elif "01110" in str_line:
            s = SCORE_MAP["live3"]
        elif "0110" in str_line:
            s = SCORE_MAP["live2"]
        return s

    def get_empty(self):
        res = []
        for y in range(self.size):
            for x in range(self.size):
                if self.is_empty(x,y):
                    res.append((x,y))
        return res