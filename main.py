import pygame
from board import *
from ai_search import AI

# 窗口设置
SIZE = 9
CELL = 60
WIDTH = CELL * SIZE
pygame.init()
screen = pygame.display.set_mode((WIDTH, WIDTH))
pygame.display.set_caption("五子棋AI(AlphaBeta剪枝)")

# 颜色
WHITE_COLOR = (255,255,255)
BLACK_COLOR = (0,0,0)
BG = (220,180,120)

def draw_board():
    screen.fill(BG)
    for i in range(SIZE):
        pygame.draw.line(screen,BLACK_COLOR,(i*CELL,0),(i*CELL,WIDTH),2)
        pygame.draw.line(screen,BLACK_COLOR,(0,i*CELL),(WIDTH,i*CELL),2)

def draw_piece(board):
    for y in range(SIZE):
        for x in range(SIZE):
            c = board.board[y][x]
            if c == BLACK:
                pygame.draw.circle(screen,BLACK_COLOR,(x*CELL+CELL//2,y*CELL+CELL//2),25)
            elif c == WHITE:
                pygame.draw.circle(screen,WHITE_COLOR,(x*CELL+CELL//2,y*CELL+CELL//2),25)

def main():
    b = Board()
    ai = AI()
    turn = BLACK
    clock = pygame.time.Clock()
    run = True
    while run:
        draw_board()
        draw_piece(b)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
            if e.type == pygame.MOUSEBUTTONDOWN and turn == BLACK:
                mx, my = pygame.mouse.get_pos()
                x = mx // CELL
                y = my // CELL
                if b.is_empty(x,y):
                    b.set_piece(x,y,BLACK)
                    if b.judge_win(BLACK):
                        print("玩家胜利！")
                        run=False
                    turn = WHITE
        # AI落子
        if turn == WHITE and run:
            ax, ay = ai.get_best(b)
            b.set_piece(ax,ay,WHITE)
            if b.judge_win(WHITE):
                print("AI胜利！")
                run=False
            turn = BLACK
        pygame.display.update()
        clock.tick(30)
    pygame.quit()

if __name__ == "__main__":
    main()