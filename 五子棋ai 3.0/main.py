# -*- coding: utf-8 -*-
"""
main.py
"""
import sys
import pygame
import config as _cfg

from core.game import GomokuGame
from core.scoring import ScoreManager
from ui.gui import GomokuGUI


def main():
    board_size = _cfg.game("board_size", 9)
    fps = _cfg.game("fps", 60)
    game = GomokuGame(size=board_size)
    score_manager = ScoreManager()
    gui = GomokuGUI(game, score_manager=score_manager)
    running = True
    clock = pygame.time.Clock()

    while running:
        # 事件处理
        running = gui.handle_events()

        # 更新动画
        dt = clock.tick(fps) / 1000.0
        gui.update_animation(dt)

        # 绘制界面
        gui.draw()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # 捕获 Ctrl+C 中断信号
        print("\n👋 [系统提示] 收到强制终止信号 (Ctrl+C)，程序正在安全退出...")
        
        # 确保 Pygame 的资源被正确释放，防止窗口卡死
        import pygame
        import sys
        pygame.quit()
        sys.exit(0)