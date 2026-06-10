# -*- coding: utf-8 -*-
"""
五子棋GUI界面模块
=================
使用Pygame实现的五子棋游戏界面，包含以下核心功能：
- 交互式棋盘显示与棋子落子
- AI对战引擎集成
- 难度选择系统（2-4层搜索深度）
- 悔棋功能
- 动画效果（落子缩放动画、棋子阴影）
- 音效管理
- 胜利判定高亮显示
- 规则说明界面
- 积分系统与战绩统计

架构设计：
1. 常量定义 - 颜色、配置参数
2. 工具类 - Button、FontManager、SoundManager
3. 主类 - GomokuGUI 负责全局管理和渲染
"""
import pygame
import sys
import time
from enum import Enum
from typing import Tuple, Optional, List
from core.scoring import ScoreManager
import config as _cfg

# ==================== 从 config.json 加载常量 ====================
# 颜色常量
BOARD_COLOR       = _cfg.color("board")
LINE_COLOR        = _cfg.color("line")
BLACK_STONE       = _cfg.color("black_stone")
WHITE_STONE       = _cfg.color("white_stone")
BTN_COLOR         = _cfg.color("btn")
BTN_HOVER_COLOR   = _cfg.color("btn_hover")
BTN_PRESS_COLOR   = _cfg.color("btn_press")
BTN_RESTART_COLOR = _cfg.color("btn_restart")
BTN_RESTART_HOVER = _cfg.color("btn_restart_hover")
BTN_RESTART_PRESS = _cfg.color("btn_restart_press")
TEXT_COLOR        = _cfg.color("text")
BG_MENU_COLOR     = _cfg.color("bg_menu")
HIGHLIGHT_COLOR   = _cfg.color("highlight")
VALID_MOVE_COLOR  = _cfg.color("valid_move")
SHADOW_COLOR      = _cfg.color("shadow")
BTN_DANGER_COLOR       = _cfg.color("btn_danger")
BTN_DANGER_HOVER       = _cfg.color("btn_danger_hover")
BTN_DANGER_PRESS       = _cfg.color("btn_danger_press")

# 游戏状态枚举
class GameState(Enum):
    """游戏界面状态"""
    MENU = 1           # 主菜单
    RULES = 2          # 规则说明
    PLAYING = 3        # 对战中
    GAME_OVER = 4      # 游戏结束
    DIFFICULTY = 5     # 难度选择
    LEADERBOARD = 6    # 战绩排行榜
    SETTINGS = 7       # 设置界面

# 配置常量
CELL_SIZE = _cfg.ui("cell_size", 60)
MARGIN    = _cfg.ui("margin", 50)
FONT_PATH = _cfg.ui("font_path", "C:/Windows/Fonts/msyh.ttc")
MAX_UNDO  = _cfg.ui("max_undo", 999999)
ANIM_SPEED = _cfg.ui("animation_speed", 6)
WIN_CAPTION = _cfg.ui("window_caption", "9x9 五子棋博弈系统")

# ==================== 工具类与组件 ====================

class Button:
    """
    通用按钮类
    功能：处理按钮的状态管理、交互、绘制
    特性：
    - 状态跟踪：正常、悬停、按下
    - 视觉反馈：颜色变化、阴影效果
    - 点击检测：返回完整的点击周期（按下+释放）
    """
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font,
                 color: Tuple[int, int, int], hover_color: Tuple[int, int, int],
                 press_color: Tuple[int, int, int], text_color: Tuple[int, int, int] = TEXT_COLOR,
                 border_radius: int = 10):
        """
        初始化按钮
        :param rect: 按钮矩形区域
        :param text: 按钮文字
        :param font: 字体对象
        :param color: 正常颜色
        :param hover_color: 悬停颜色
        :param press_color: 按下颜色
        :param text_color: 文字颜色
        :param border_radius: 圆角半径
        """
        self.rect = rect
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.press_color = press_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.is_hovered = False
        self.is_pressed = False

        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def update(self, mouse_pos: Tuple[int, int], mouse_pressed: bool) -> bool:
        """
        更新按钮状态并检测点击
        :param mouse_pos: 鼠标位置
        :param mouse_pressed: 鼠标是否按下
        :return: 点击完成（按下且释放）返回True
        """
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_hovered and mouse_pressed:
            if not self.is_pressed:
                self.is_pressed = True
            return False
        elif self.is_hovered and not mouse_pressed and self.is_pressed:
            self.is_pressed = False
            return True
        else:
            self.is_pressed = False
            return False

    def draw(self, surface: pygame.Surface):
        """绘制按钮及其视觉效果"""
        current_color = self.color
        if self.is_pressed:
            current_color = self.press_color
        elif self.is_hovered:
            current_color = self.hover_color

        shadow_rect = self.rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(surface, SHADOW_COLOR, shadow_rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, current_color, self.rect, border_radius=self.border_radius)
        surface.blit(self.text_surf, self.text_rect)


class FontManager:
    """
    字体管理器
    功能：缓存字体对象，统一管理游戏中的所有字体
    优势：避免重复加载同一字体，提高性能
    """
    _fonts = {}

    @staticmethod
    def get_font(size: int, bold: bool = False) -> pygame.font.Font:
        """
        获取指定大小和样式的字体（支持缓存）
        :param size: 字体大小
        :param bold: 是否加粗
        :return: 字体对象
        """
        key = (size, bold)
        if key not in FontManager._fonts:
            try:
                font = pygame.font.Font(FONT_PATH, size)
            except Exception:
                font = pygame.font.Font(None, size)
            font.set_bold(bold)
            FontManager._fonts[key] = font
        return FontManager._fonts[key]


class SoundManager:
    """
    音效管理器
    功能：加载和播放游戏音效
    说明：当前音效文件为可选项，不影响游戏正常运行
    """
    _sounds = {}

    @staticmethod
    def load_sound(name: str, path: str):
        """加载音效文件"""
        try:
            sound = pygame.mixer.Sound(path)
            SoundManager._sounds[name] = sound
        except Exception:
            print(f"警告：无法加载音效 {path}")

    @staticmethod
    def play_sound(name: str):
        """播放已加载的音效"""
        if name in SoundManager._sounds:
            SoundManager._sounds[name].play()

# ==================== 主GUI类 ====================

class GomokuGUI:
    """
    五子棋游戏主界面类
    职责：
    - 管理游戏状态和界面切换
    - 处理用户输入和事件
    - 绘制界面和动画
    - 协调游戏逻辑和AI移动

    核心属性：
    - state: 当前界面状态
    - difficulty: AI搜索深度
    - undo_history: 悔棋历史记录
    - animating_stone: 当前动画中的棋子
    """

    def __init__(self, game, score_manager=None, cell_size: int = CELL_SIZE, margin: int = MARGIN):
        """
        初始化游戏界面
        :param game: 游戏核心逻辑对象
        :param score_manager: 积分管理器（可选）
        :param cell_size: 每个格子的像素尺寸
        :param margin: 棋盘边距
        """
        self.game = game
        self.score_manager = score_manager
        self._last_game_score = 0
        self.cell_size = cell_size
        self.margin = margin
        size = (game.size - 1) * cell_size + 2 * margin
        self.window_size = (size, size)

        # 初始化Pygame和音效系统
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        pygame.display.set_caption(WIN_CAPTION)

        # 加载音效（可选）
        # SoundManager.load_sound("place", "sounds/place.wav")
        # SoundManager.load_sound("win", "sounds/win.wav")
        # SoundManager.load_sound("lose", "sounds/lose.wav")

        # === 游戏状态 ===
        self.state = GameState.MENU                 # 初始状态为主菜单
        self.difficulty = 3                         # AI搜索深度（2-4）
        self.undo_history = []                      # 回合记录：[(行, 列, 玩家), ...]
        self.last_move = None                       # 最后一步棋的坐标
        self.winning_line = []                      # 胜利的五连子坐标列表

        # === 动画状态 ===
        self.animating_stone = None                 # 动画中的棋子：(行, 列, 玩家) 或 None
        self.animation_progress = 0.0               # 动画进度：0.0-1.0

        # === 游戏计时 ===
        self.game_start_time = None                 # 游戏开始时间
        self.game_end_time = None                   # 游戏结束时间

        # 初始化所有按钮
        self._init_buttons()

        # 预渲染棋盘背景（性能优化）
        self._pre_render()

    def _init_buttons(self):
        """
        初始化所有界面按钮
        按钮分类：
        1. 主菜单按钮：开始游戏、难度选择、规则、退出、战绩
        2. 规则页面按钮：返回菜单
        3. 难度选择按钮：简单、中等、困难
        4. 游戏过程按钮：悔棋、返回菜单
        5. 游戏结束按钮：再来一局、返回菜单
        """
        cx = self.window_size[0] // 2

        # 【主菜单按钮】
        self.btn_ai = Button(
            pygame.Rect(cx - 100, 200, 200, 50),
            "AI 智能对战", FontManager.get_font(20),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )
        self.btn_difficulty = Button(
            pygame.Rect(cx - 100, 280, 200, 50),
            "难度选择", FontManager.get_font(20),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )
        self.btn_rules = Button(
            pygame.Rect(cx - 100, 360, 200, 50),
            "规则说明", FontManager.get_font(20),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )
        self.btn_quit = Button(
            pygame.Rect(cx - 100, 440, 200, 50),
            "退出游戏", FontManager.get_font(20),
            BTN_DANGER_COLOR, BTN_DANGER_HOVER, BTN_DANGER_PRESS  # 红色主题
        )
        self.btn_leaderboard = Button(
            pygame.Rect(cx - 100, 510, 200, 50),
            "📊 战绩", FontManager.get_font(20),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )

        # 【规则页面按钮】
        self.btn_back_menu = Button(
            pygame.Rect(cx - 100, 410, 200, 50),
            "返回主菜单", FontManager.get_font(20),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )

        # 【难度选择按钮】
        self.btn_easy = Button(
            pygame.Rect(cx - 100, 200, 200, 50),
            "简单 (深度2)", FontManager.get_font(20),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )
        self.btn_medium = Button(
            pygame.Rect(cx - 100, 270, 200, 50),
            "中等 (深度3)", FontManager.get_font(20),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )
        self.btn_hard = Button(
            pygame.Rect(cx - 100, 340, 200, 50),
            "困难 (深度4)", FontManager.get_font(20),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )

        # 【游戏结束按钮】
        self.btn_restart = Button(
            pygame.Rect(cx - 120, 280, 110, 45),
            "再来一局", FontManager.get_font(18),
            BTN_RESTART_COLOR, BTN_RESTART_HOVER, BTN_RESTART_PRESS
        )
        self.btn_back = Button(
            pygame.Rect(cx + 10, 280, 110, 45),
            "返回主菜单", FontManager.get_font(18),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )

        # 【游戏中按钮】— 放置在棋盘下方
        btn_y = self.margin + (self.game.size - 1) * self.cell_size + 10
        self.btn_undo = Button(
            pygame.Rect(10, btn_y, 80, 30),
            "悔棋", FontManager.get_font(14),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )
        self.btn_menu = Button(
            pygame.Rect(self.window_size[0] - 90, btn_y, 80, 30),
            "菜单", FontManager.get_font(14),
            BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        )

        # 【战绩页面按钮】
        self.btn_clear_scores = Button(
            pygame.Rect(cx - 100, 480, 200, 45),
            "🗑️ 清空战绩", FontManager.get_font(18),
            BTN_DANGER_COLOR, BTN_DANGER_HOVER, BTN_DANGER_PRESS  # 红色主题
        )

        # 【设置界面按钮】
        w, h = self.window_size
        self.btn_gear = Button(
            pygame.Rect(w - 55, h - 55, 45, 45),
            "", FontManager.get_font(24),
            (100, 100, 100), (150, 150, 150), (60, 60, 60),
            border_radius=22
        )
        # 设置页内的颜色选项
        self._settings_theme_btns = []
        self._settings_bg_btns = []
        self._build_settings_buttons()

    def _pre_render(self):
        """
        预渲染棋盘背景（性能优化）
        静态元素一次性渲染后缓存，每帧只需直接使用，无需重复计算
        """
        self.board_background = pygame.Surface(self.window_size)
        self.board_background.fill(BOARD_COLOR)

        # 绘制棋盘网格
        for i in range(self.game.size):
            pygame.draw.line(self.board_background, LINE_COLOR,
                             (self.margin, self.margin + i * self.cell_size),
                             (self.window_size[0] - self.margin, self.margin + i * self.cell_size), 1)
            pygame.draw.line(self.board_background, LINE_COLOR,
                             (self.margin + i * self.cell_size, self.margin),
                             (self.margin + i * self.cell_size, self.window_size[1] - self.margin), 1)

        # 在棋盘边缘添加坐标标签（列标 A-L，行号 1-12）
        coord_font = FontManager.get_font(12, bold=True)
        col_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i in range(self.game.size):
            # 顶部列标（字母）
            text = coord_font.render(col_labels[i], True, LINE_COLOR)
            self.board_background.blit(text, (self.margin + i * self.cell_size - text.get_width()//2, 8))
            # 左侧行号（数字）
            text = coord_font.render(str(i + 1), True, LINE_COLOR)
            self.board_background.blit(text, (8, self.margin + i * self.cell_size - text.get_height()//2))

    def handle_events(self) -> bool:
        """
        处理所有事件
        :return: 返回False表示退出游戏，True表示继续
        事件类型：
        - QUIT: 关闭窗口
        - VIDEORESIZE: 调整窗口大小
        - KEYDOWN: 键盘按下（ESC、Z、R快捷键）
        - MOUSEBUTTONDOWN: 棋盘点击落子
        """
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                return False

            if event.type == pygame.VIDEORESIZE:
                # 处理窗口大小调整（重新初始化按钮和棋盘）
                self.window_size = max(event.w, 400), max(event.h, 400)
                self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                self._init_buttons()
                self._pre_render()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC返回主菜单
                    if self.state in [GameState.PLAYING, GameState.GAME_OVER, GameState.RULES, GameState.DIFFICULTY, GameState.LEADERBOARD, GameState.SETTINGS]:
                        self.state = GameState.MENU
                elif event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                    # R键快速重新开始
                    self.restart_game()
                elif event.key == pygame.K_z and self.state == GameState.PLAYING:
                    # Z键悔棋
                    self.undo()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 鼠标左键点击棋盘（仅在游戏进行中且无动画时）
                if self.state == GameState.PLAYING and not self.animating_stone:
                    cell = self.get_click_cell(mouse_pos)
                    if cell and self.game.board[cell[0]][cell[1]] == 0:
                        self.make_move(cell[0], cell[1])

        # 处理所有按钮的点击事件
        self._handle_button_clicks(mouse_pos, mouse_pressed)

        return True

    def _handle_button_clicks(self, mouse_pos: Tuple[int, int], mouse_pressed: bool):
        """
        处理按钮点击事件（根据当前游戏状态分发处理）
        """
        if self.state == GameState.MENU:
            # 主菜单按钮处理
            if self.btn_ai.update(mouse_pos, mouse_pressed):
                self.restart_game()
                self.state = GameState.PLAYING
            elif self.btn_difficulty.update(mouse_pos, mouse_pressed):
                self.state = GameState.DIFFICULTY
            elif self.btn_rules.update(mouse_pos, mouse_pressed):
                self.state = GameState.RULES
            elif self.btn_quit.update(mouse_pos, mouse_pressed):
                self.quit()
                pygame.quit()
                sys.exit()
            elif self.btn_leaderboard.update(mouse_pos, mouse_pressed):
                self.state = GameState.LEADERBOARD

        elif self.state == GameState.RULES:
            # 规则页面按钮
            if self.btn_back_menu.update(mouse_pos, mouse_pressed):
                self.state = GameState.MENU

        elif self.state == GameState.DIFFICULTY:
            # 难度选择按钮
            if self.btn_easy.update(mouse_pos, mouse_pressed):
                self.difficulty = 2
                self.state = GameState.MENU
            elif self.btn_medium.update(mouse_pos, mouse_pressed):
                self.difficulty = 3
                self.state = GameState.MENU
            elif self.btn_hard.update(mouse_pos, mouse_pressed):
                self.difficulty = 4
                self.state = GameState.MENU
            elif self.btn_back_menu.update(mouse_pos, mouse_pressed):
                self.state = GameState.MENU

        elif self.state == GameState.PLAYING:
            # 游戏中按钮
            if self.btn_undo.update(mouse_pos, mouse_pressed):
                self.undo()
            elif self.btn_menu.update(mouse_pos, mouse_pressed):
                self.state = GameState.MENU

        elif self.state == GameState.GAME_OVER:
            # 游戏结束按钮
            if self.btn_restart.update(mouse_pos, mouse_pressed):
                self.restart_game()
            elif self.btn_back.update(mouse_pos, mouse_pressed):
                self.state = GameState.MENU

        elif self.state == GameState.LEADERBOARD:
            # 战绩页面按钮
            if self.btn_back_menu.update(mouse_pos, mouse_pressed):
                self.state = GameState.MENU
            elif self.btn_clear_scores.update(mouse_pos, mouse_pressed):
                if self.score_manager:
                    self.score_manager.clear_scores()

        elif self.state == GameState.SETTINGS:
            # 设置界面按钮
            if self.btn_back_menu.update(mouse_pos, mouse_pressed):
                self.state = GameState.MENU
            for btn, (theme_name, btn_c, btn_h, btn_p) in self._settings_theme_btns:
                if btn.update(mouse_pos, mouse_pressed):
                    self._apply_theme(theme_name, btn_c, btn_h, btn_p)
            for btn, (bg_name, bg_c) in self._settings_bg_btns:
                if btn.update(mouse_pos, mouse_pressed):
                    self._apply_bg(bg_name, bg_c)

        # 齿轮按钮在MENU状态也可点击
        if self.state in [GameState.MENU, GameState.SETTINGS]:
            if self.btn_gear.update(mouse_pos, mouse_pressed):
                self.state = GameState.SETTINGS

    def make_move(self, r: int, c: int):
        """
        执行落子操作
        流程：
        1. 保存到历史记录（用于悔棋）
        2. 启动棋子动画
        3. 更新棋盘数据
        4. 立即切换玩家（以便显示正确的当前玩家）
        :param r: 行号
        :param c: 列号
        """
        # 保存历史记录用于悔棋
        self.undo_history.append((r, c, self.game.current_player))
        if len(self.undo_history) > MAX_UNDO * 2:
            self.undo_history.pop(0)

        # 启动落子动画
        self.animating_stone = (r, c, self.game.current_player)
        self.animation_progress = 0.0
        self.last_move = (r, c)

        # 将棋子放置到棋盘
        self.game.board[r][c] = self.game.current_player

        # 立即切换玩家，使得显示能正确反映当前玩家
        self.game.current_player = 3 - self.game.current_player

        SoundManager.play_sound("place")

    def update_animation(self, dt: float):
        """
        更新动画状态（每帧调用）
        功能：
        - 推进落子动画进度
        - 动画完成后检查胜负
        - 触发AI回合
        :param dt: 时间差（秒）
        """
        if self.animating_stone:
            self.animation_progress += dt * ANIM_SPEED

            if self.animation_progress >= 1.0:
                # 动画完成，处理游戏逻辑
                r, c, player = self.animating_stone
                self.animating_stone = None
                self.animation_progress = 0.0

                # 检查是否有获胜者
                winner = self.game.check_winner()
                if winner != 0:
                    self.winning_line = self.game.get_winning_line()
                    self.state = GameState.GAME_OVER
                    self.game_end_time = time.time()
                    # 记录积分
                    self._last_game_score = 0
                    if self.score_manager:
                        self._last_game_score = self.score_manager.record_game(self.difficulty, winner)
                    if winner == 1:
                        SoundManager.play_sound("win")
                    else:
                        SoundManager.play_sound("lose")
                elif self.game.is_board_full():
                    # 棋盘满且无人获胜，判定为平局
                    self.state = GameState.GAME_OVER
                    self.game_end_time = time.time()
                    # 记录平局积分
                    self._last_game_score = 0
                    if self.score_manager:
                        self._last_game_score = self.score_manager.record_game(self.difficulty, 0)
                else:
                    # 继续游戏：如果是AI的回合，调用AI决策
                    if self.game.current_player == 2:
                        ai_move = self.game.get_ai_move(self.difficulty)
                        if ai_move:
                            self.make_move(ai_move[0], ai_move[1])

    def undo(self):
        """
        悔棋功能
        规则：一次悔棋撤销玩家和AI各一步（回到玩家的前一个轮次）
        限制：
        - 必须有至少2步记录（玩家1步+AI1步）
        - 动画进行时无法悔棋
        """
        if len(self.undo_history) >= 2 and not self.animating_stone:
            # 撤销AI的最后一步
            r, c, _ = self.undo_history.pop()
            self.game.board[r][c] = 0
            # 撤销玩家的最后一步
            r, c, _ = self.undo_history.pop()
            self.game.board[r][c] = 0
            # 恢复到玩家回合
            self.game.current_player = 1
            self.last_move = None
            self.winning_line = []

    def restart_game(self):
        """重新开始游戏，重置所有游戏状态"""
        self.game.reset()
        self.state = GameState.PLAYING
        self.undo_history = []
        self.last_move = None
        self.winning_line = []
        self.animating_stone = None
        self.animation_progress = 0.0
        self.game_start_time = time.time()
        self.game_end_time = None

    def draw(self):
        """
        绘制当前界面（根据游戏状态分发）
        每帧调用一次
        """
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.RULES:
            self.draw_rules()
        elif self.state == GameState.DIFFICULTY:
            self.draw_difficulty()
        elif self.state in [GameState.PLAYING, GameState.GAME_OVER]:
            self.draw_game()
        elif self.state == GameState.LEADERBOARD:
            self.draw_leaderboard()
        elif self.state == GameState.SETTINGS:
            self.draw_settings()

        # 在 MENU 和 SETTINGS 页绘制齿轮按钮
        if self.state in [GameState.MENU, GameState.SETTINGS]:
            self._draw_gear_btn()

        pygame.display.flip()

    def draw_menu(self):
        """
        绘制主菜单界面
        元素：渐变背景、标题、副标题、5个功能按钮
        """
        # 绘制渐变背景效果
        for y in range(self.window_size[1]):
            color = (
                BG_MENU_COLOR[0] + y // 4,
                BG_MENU_COLOR[1] + y // 4,
                BG_MENU_COLOR[2] + y // 4
            )
            pygame.draw.line(self.screen, color, (0, y), (self.window_size[0], y))

        # 标题
        title_font = FontManager.get_font(36, bold=True)
        title_surf = title_font.render("12x12 五子棋博弈系统", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(self.window_size[0] // 2, 100))
        self.screen.blit(title_surf, title_rect)

        # 副标题
        subtitle_font = FontManager.get_font(16)
        subtitle_surf = subtitle_font.render("核心算法：极大极小值 + Alpha-Beta剪枝", True, (200, 200, 200))
        subtitle_rect = subtitle_surf.get_rect(center=(self.window_size[0] // 2, 150))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # 按钮
        self.btn_ai.draw(self.screen)
        self.btn_difficulty.draw(self.screen)
        self.btn_rules.draw(self.screen)
        self.btn_quit.draw(self.screen)
        self.btn_leaderboard.draw(self.screen)

    def draw_rules(self):
        """
        绘制规则说明界面
        展示游戏规则和快捷键说明
        """
        self.screen.fill(BG_MENU_COLOR)

        title_font = FontManager.get_font(36, bold=True)
        title_surf = title_font.render("五子棋游戏规则", True, TEXT_COLOR)
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.window_size[0] // 2, 80)))

        rules_lines = [
            "1. 游戏使用 12x12 路棋盘，黑子先手，白子后手。",
            "2. 玩家与 AI 轮流在网格的交叉点上落子。",
            "3. 任何一方在横、竖、斜任意方向上，",
            "   率先形成连续的【五个同色棋子】即获胜。",
            "4. 当棋盘落满且无人达成五连时，判定为平局。",
            "5. 按 Z 键悔棋，按 ESC 返回主菜单。"
        ]

        text_font = FontManager.get_font(18)
        for i, line in enumerate(rules_lines):
            surf = text_font.render(line, True, TEXT_COLOR)
            self.screen.blit(surf, (60, 160 + i * 35))

        self.btn_back_menu.draw(self.screen)

    def draw_difficulty(self):
        """
        绘制难度选择界面
        展示3个难度级别和当前选中的难度
        """
        self.screen.fill(BG_MENU_COLOR)

        title_font = FontManager.get_font(36, bold=True)
        title_surf = title_font.render("选择难度", True, TEXT_COLOR)
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.window_size[0] // 2, 100)))

        # 显示当前难度
        difficulty_text = '简单' if self.difficulty == 2 else '中等' if self.difficulty == 3 else '困难'
        current_text = f"当前难度：{difficulty_text}"
        current_font = FontManager.get_font(20)
        current_surf = current_font.render(current_text, True, (255, 215, 0))
        self.screen.blit(current_surf, current_surf.get_rect(center=(self.window_size[0] // 2, 160)))

        self.btn_easy.draw(self.screen)
        self.btn_medium.draw(self.screen)
        self.btn_hard.draw(self.screen)
        self.btn_back_menu.draw(self.screen)

    def draw_leaderboard(self):
        """
        绘制战绩排行榜界面
        展示各难度累计积分和最近对局记录
        """
        self.screen.fill(BG_MENU_COLOR)

        # 标题
        title_font = FontManager.get_font(36, bold=True)
        title_surf = title_font.render("📊 战绩统计", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(self.window_size[0] // 2, 50))
        self.screen.blit(title_surf, title_rect)

        if not self.score_manager:
            nodata_font = FontManager.get_font(18)
            nodata_surf = nodata_font.render("积分系统未启用", True, (180, 180, 180))
            self.screen.blit(nodata_surf, nodata_surf.get_rect(center=(self.window_size[0] // 2, 150)))
            self.btn_back_menu.draw(self.screen)
            return

        scores = self.score_manager.get_scores()

        # 分难度积分表
        header_font = FontManager.get_font(20, bold=True)
        row_font = FontManager.get_font(18)

        # 表头
        headers = ["难度", "积分"]
        col_widths = [160, 120]
        table_start_y = 110
        table_x = self.window_size[0] // 2 - sum(col_widths) // 2

        for j, header in enumerate(headers):
            hx = table_x + sum(col_widths[:j]) + col_widths[j] // 2
            hs = header_font.render(header, True, (255, 215, 0))
            self.screen.blit(hs, hs.get_rect(center=(hx, table_start_y)))

        # 分隔线
        sep_y = table_start_y + 30
        pygame.draw.line(self.screen, (100, 150, 200), (table_x, sep_y),
                         (table_x + sum(col_widths), sep_y), 1)

        # 数据行
        difficulties = ["简单", "中等", "困难"]
        colors = {
            "简单": (144, 238, 144),
            "中等": (255, 215, 0),
            "困难": (255, 127, 127)
        }
        for i, diff in enumerate(difficulties):
            row_y = sep_y + 15 + i * 35
            score_val = scores.get(diff, 0)
            sign = "+" if score_val > 0 else ""
            score_text = f"{sign}{score_val}"

            diff_color = colors.get(diff, TEXT_COLOR)
            score_color = (144, 238, 144) if score_val > 0 else (255, 127, 127) if score_val < 0 else TEXT_COLOR

            # 难度标签
            ds = row_font.render(diff, True, diff_color)
            dx = table_x + col_widths[0] // 2
            self.screen.blit(ds, ds.get_rect(center=(dx, row_y)))

            # 积分值
            ss = row_font.render(score_text, True, score_color)
            sx = table_x + col_widths[0] + col_widths[1] // 2
            self.screen.blit(ss, ss.get_rect(center=(sx, row_y)))

        # 最近对局记录
        history_y = sep_y + 15 + len(difficulties) * 35 + 30
        hist_title = header_font.render("最近对局", True, (255, 215, 0))
        self.screen.blit(hist_title, hist_title.get_rect(center=(self.window_size[0] // 2, history_y)))

        history = self.score_manager.get_recent_history(8)
        small_font = FontManager.get_font(14)
        for i, record in enumerate(history):
            line_y = history_y + 30 + i * 25
            line = f"{record['time']}  [{record['difficulty']}]  {record['result']}"
            if record['result'] == '胜':
                result_color = (144, 238, 144)
            elif record['result'] == '负':
                result_color = (255, 127, 127)
            else:
                result_color = (255, 215, 0)
            ls = small_font.render(line, True, result_color)
            self.screen.blit(ls, ls.get_rect(center=(self.window_size[0] // 2, line_y)))

        self.btn_back_menu.draw(self.screen)
        self.btn_clear_scores.draw(self.screen)

    def draw_game(self):
        """
        绘制游戏盘面
        渲染元素（分层）：
        1. 棋盘背景和网格
        2. 可落子位置高亮
        3. 已放置的棋子
        4. 落子动画
        5. 最后落子标记
        6. 胜利五连高亮
        7. 玩家提示和按钮
        8. 游戏结束蒙层和结算界面（含积分）
        """
        # 1. 绘制预渲染的棋盘背景
        self.screen.blit(self.board_background, (0, 0))

        # 2. 绘制可落子位置高亮（玩家轮次且无动画进行时）
        if self.state == GameState.PLAYING and self.game.current_player == 1 and not self.animating_stone:
            mouse_pos = pygame.mouse.get_pos()
            cell = self.get_click_cell(mouse_pos)
            if cell and self.game.board[cell[0]][cell[1]] == 0:
                center = (self.margin + cell[1] * self.cell_size, self.margin + cell[0] * self.cell_size)
                pygame.draw.circle(self.screen, (255, 60, 60), center, int(self.cell_size * 0.37), 3)

        # 3. 绘制棋盘上所有已落的棋子
        for r in range(self.game.size):
            for c in range(self.game.size):
                if self.game.board[r][c] != 0:
                    self._draw_stone(r, c, self.game.board[r][c])

        # 4. 绘制动画中的棋子（缩放效果）
        if self.animating_stone:
            r, c, player = self.animating_stone
            scale = self.animation_progress
            self._draw_stone(r, c, player, scale, is_animating=True)

        # 5. 绘制最后落子的标记圆点（红色）
        if self.last_move and not self.animating_stone:
            r, c = self.last_move
            center = (self.margin + c * self.cell_size, self.margin + r * self.cell_size)
            pygame.draw.circle(self.screen, (255, 0, 0), center, 5)

        # 6. 绘制胜利的五连子高亮
        if self.winning_line:
            for r, c in self.winning_line:
                center = (self.margin + c * self.cell_size, self.margin + r * self.cell_size)
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, center, int(self.cell_size * 0.45))

        # 7. 绘制当前玩家提示和游戏中按钮
        if self.state == GameState.PLAYING:
            player_text = "当前玩家：黑子（你）" if self.game.current_player == 1 else "当前玩家：白子（AI）"
            text_font = FontManager.get_font(16)
            text_surf = text_font.render(player_text, True, TEXT_COLOR)
            self.screen.blit(text_surf, (self.window_size[0] // 2 - text_surf.get_width() // 2, 10))

            self.btn_undo.draw(self.screen)
            self.btn_menu.draw(self.screen)

            # 快捷键提示栏
            hint_font = FontManager.get_font(12)
            hints = "快捷键: Z-悔棋 | ESC-返回菜单"
            hint_surf = hint_font.render(hints, True, (160, 180, 200))
            hint_rect = hint_surf.get_rect(center=(self.window_size[0] // 2, self.window_size[1] - 15))
            self.screen.blit(hint_surf, hint_rect)

        # 8. 游戏结束界面
        if self.state == GameState.GAME_OVER:
            # 快捷键提示栏
            hint_font = FontManager.get_font(12)
            hints = "快捷键: R-再来一局 | ESC-返回菜单"
            hint_surf = hint_font.render(hints, True, (160, 180, 200))
            hint_rect = hint_surf.get_rect(center=(self.window_size[0] // 2, self.window_size[1] - 15))
            self.screen.blit(hint_surf, hint_rect)
            # 绘制半透明蒙层
            overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            # 计算游戏统计信息
            game_duration = 0
            if self.game_start_time and self.game_end_time:
                game_duration = int(self.game_end_time - self.game_start_time)
            total_rounds = len(self.undo_history)
            difficulty_map = {2: "简单", 3: "中等", 4: "困难"}
            difficulty_text = difficulty_map.get(self.difficulty, "未知")

            # 绘制结算面板背景（加高以容纳积分信息）
            panel_width = 450
            panel_height = 360
            panel_x = (self.window_size[0] - panel_width) // 2
            panel_y = (self.window_size[1] - panel_height) // 2
            panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
            pygame.draw.rect(self.screen, (40, 40, 60), panel_rect, border_radius=15)
            pygame.draw.rect(self.screen, (100, 150, 200), panel_rect, 3, border_radius=15)

            # 绘制结算文本
            winner_status = self.game.check_winner()
            if winner_status == 1:
                result_text = "🎉 恭喜你，获得了胜利！"
                result_color = (144, 238, 144)  # 浅绿色
            elif winner_status == 2:
                result_text = "🤖 遗憾！AI 赢得了比赛。"
                result_color = (255, 127, 127)  # 浅红色
            else:
                result_text = "🤝 棋盘已满，平局！"
                result_color = (255, 215, 0)  # 金色

            # 结果标题
            win_font = FontManager.get_font(28, bold=True)
            win_surf = win_font.render(result_text, True, result_color)
            win_rect = win_surf.get_rect(center=(self.window_size[0] // 2, panel_y + 40))
            self.screen.blit(win_surf, win_rect)

            # 统计信息
            stat_font = FontManager.get_font(16)
            stats = [
                f"总回合数: {total_rounds}",
                f"游戏用时: {game_duration}秒",
                f"难度等级: {difficulty_text}"
            ]
            for i, stat in enumerate(stats):
                stat_surf = stat_font.render(stat, True, (220, 220, 220))
                stat_rect = stat_surf.get_rect(center=(self.window_size[0] // 2, panel_y + 90 + i * 30))
                self.screen.blit(stat_surf, stat_rect)

            # ---- 本局得分和累计积分（新增）----
            if self.score_manager:
                # 分隔线
                sep_y = panel_y + 90 + len(stats) * 30 + 5
                pygame.draw.line(self.screen, (100, 150, 200),
                                 (panel_x + 30, sep_y), (panel_x + panel_width - 30, sep_y), 1)

                # 本局得分
                score_s = self._last_game_score
                sign = "+" if score_s > 0 else ""
                score_label = f"🏆 本局得分: {sign}{score_s}"
                if score_s > 0:
                    score_color = (144, 238, 144)
                elif score_s < 0:
                    score_color = (255, 127, 127)
                else:
                    score_color = (255, 215, 0)
                score_font = FontManager.get_font(18, bold=True)
                score_surf = score_font.render(score_label, True, score_color)
                score_rect = score_surf.get_rect(center=(self.window_size[0] // 2, sep_y + 25))
                self.screen.blit(score_surf, score_rect)

                # 分难度积分
                sc = self.score_manager.get_scores()
                diffs = [f"简单: {sc['简单']:+d}", f"中等: {sc['中等']:+d}", f"困难: {sc['困难']:+d}"]
                diff_text = "  |  ".join(diffs)
                diff_font = FontManager.get_font(14)
                diff_surf = diff_font.render(f"📊 {diff_text}", True, (200, 200, 200))
                diff_rect = diff_surf.get_rect(center=(self.window_size[0] // 2, sep_y + 55))
                self.screen.blit(diff_surf, diff_rect)

            # 绘制结束页面按钮（动态调整位置到结算面板下方）
            button_y = panel_y + panel_height + 20
            self.btn_restart.rect.y = button_y
            self.btn_back.rect.y = button_y
            self.btn_restart.text_rect = self.btn_restart.text_surf.get_rect(center=self.btn_restart.rect.center)
            self.btn_back.text_rect = self.btn_back.text_surf.get_rect(center=self.btn_back.rect.center)
            self.btn_restart.draw(self.screen)
            self.btn_back.draw(self.screen)

    def _ease_out_back(self, t: float) -> float:
        """回退缓动：快速落下后弹起的效果"""
        c1, c3 = 1.70158, 1.70158 + 1
        return 1 + c3 * ((t - 1) ** 3) + c1 * ((t - 1) ** 2)

    def _draw_stone(self, r: int, c: int, player: int, scale: float = 1.0, is_animating: bool = False):
        """
        绘制单个棋子（含3D阴影、发光和弹性动画效果）
        视觉特性：
        - 底层阴影：提供立体感，动画时缩小增强落下感
        - 棋子主体：实心圆，动画时带弹性缩放
        - 发光环：动画时周围发光渐隐
        - 高光：白子亮点，黑子暗点
        - 边框：白子黑色边框
        :param r: 行号
        :param c: 列号
        :param player: 玩家ID（1=黑子，2=白子）
        :param scale: 缩放比例（用于动画，0-1）
        :param is_animating: 是否在动画中（带弹性效果）
        """
        color = BLACK_STONE if player == 1 else WHITE_STONE
        center = (self.margin + c * self.cell_size, self.margin + r * self.cell_size)

        if is_animating:
            eased_scale = self._ease_out_back(min(scale, 0.95))
            actual_scale = eased_scale
            radius = int(self.cell_size * 0.45 * actual_scale)

            # 发光环（动画时显示）
            glow_radius = int(self.cell_size * 0.5 * (1 - actual_scale) + self.cell_size * 0.1)
            glow_alpha = int(100 * (1 - actual_scale))
            if glow_radius > radius:
                glow_color = (255, 215, 0) if player == 2 else (150, 150, 150)
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*glow_color, glow_alpha), (glow_radius, glow_radius), glow_radius)
                self.screen.blit(glow_surface, (center[0] - glow_radius, center[1] - glow_radius))

            # 动画时阴影缩小（增强落下感）
            shadow_offset = int(8 * (1 - actual_scale))
            shadow_center = (center[0] + shadow_offset, center[1] + shadow_offset)
            shadow_radius = int(radius * 0.9)
            pygame.draw.circle(self.screen, SHADOW_COLOR, shadow_center, max(shadow_radius, 1))
        else:
            actual_scale = scale
            radius = int(self.cell_size * 0.45 * actual_scale)

            # 阴影层（投影）
            shadow_offset = int(3 * scale)
            shadow_center = (center[0] + shadow_offset, center[1] + shadow_offset)
            pygame.draw.circle(self.screen, SHADOW_COLOR, shadow_center, radius)

        # 棋子主体
        pygame.draw.circle(self.screen, color, center, radius)

        # 棋子装饰（高光，白子不加黑色边框保持纯白）
        if player == 2:
            highlight_center = (center[0] - radius//3, center[1] - radius//3)
            pygame.draw.circle(self.screen, (255, 255, 255), highlight_center, max(radius//4, 1))
        else:
            highlight_center = (center[0] - radius//3, center[1] - radius//3)
            pygame.draw.circle(self.screen, (50, 50, 50), highlight_center, max(radius//4, 1))

    def get_click_cell(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        将屏幕像素坐标转换为棋盘网格坐标
        采用四舍五入，使得点击范围更加友好
        :param pos: 屏幕坐标 (x, y)
        :return: 棋盘坐标 (行, 列) 或 None（超出范围）
        """
        x, y = pos
        c = round((x - self.margin) / self.cell_size)
        r = round((y - self.margin) / self.cell_size)
        if 0 <= r < self.game.size and 0 <= c < self.game.size:
            return r, c
        return None

    # ================================================================
    # 设置页面方法
    # ================================================================
    def _build_settings_buttons(self):
        """构建设置页面的颜色选项按钮"""
        cx = self.window_size[0] // 2
        btn_font = FontManager.get_font(14)
        small_font = FontManager.get_font(12)

        # 按钮颜色主题（颜色固定，不随主题切换而变化）
        themes = [
            ("默认蓝",  (52, 152, 219), (41, 128, 185), (21, 93, 144)),
            ("翡翠绿", (46, 204, 113), (82, 222, 151), (30, 180, 90)),
            ("琥珀橙", (230, 126, 34), (243, 156, 18), (211, 84, 0)),
            ("紫罗兰", (142, 68, 173), (155, 89, 182), (113, 54, 138)),
        ]
        self._settings_theme_btns = []
        for i, (name, c, h, p) in enumerate(themes):
            btn = Button(
                pygame.Rect(cx - 240 + (i % 2) * 250, 140 + (i // 2) * 55, 230, 40),
                name, btn_font, c, h, p,
                text_color=TEXT_COLOR, border_radius=8
            )
            self._settings_theme_btns.append((btn, (name, c, h, p)))

        # 背景颜色主题
        bgs = [
            ("深海蓝", (44, 62, 80)),
            ("石墨灰", (52, 73, 94)),
            ("暗夜紫", (48, 40, 66)),
            ("墨绿色", (33, 55, 45)),
        ]
        self._settings_bg_btns = []
        for i, (name, c) in enumerate(bgs):
            btn = Button(
                pygame.Rect(cx - 240 + (i % 2) * 250, 300 + (i // 2) * 55, 230, 40),
                name, btn_font, (*c, 0), (*[min(v+40,255) for v in c], 0), (*[max(v-30,0) for v in c], 0),
                text_color=TEXT_COLOR, border_radius=8
            )
            self._settings_bg_btns.append((btn, (name, c)))

    def _apply_theme(self, theme_name, btn_c, btn_h, btn_p):
        """应用按钮颜色主题"""
        global BTN_COLOR, BTN_HOVER_COLOR, BTN_PRESS_COLOR
        BTN_COLOR = btn_c
        BTN_HOVER_COLOR = btn_h
        BTN_PRESS_COLOR = btn_p
        # 更新 config.json
        self._update_config_colors({"btn": btn_c, "btn_hover": btn_h, "btn_press": btn_p})
        self._init_buttons()

    def _apply_bg(self, bg_name, bg_c):
        """应用背景颜色主题"""
        global BG_MENU_COLOR
        BG_MENU_COLOR = bg_c
        self._update_config_colors({"bg_menu": bg_c})
        self._init_buttons()
        self._pre_render()

    def _update_config_colors(self, colors_dict):
        """写入颜色到 config.json"""
        import json, os
        cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for key, val in colors_dict.items():
                cfg["ui"]["colors"][key] = list(val)
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            _cfg.reload()
        except Exception:
            pass

    def _draw_gear_btn(self):
        """绘制齿轮图标按钮"""
        # 先绘制按钮背景
        btn = self.btn_gear
        current_color = btn.color
        if btn.is_pressed:
            current_color = btn.press_color
        elif btn.is_hovered:
            current_color = btn.hover_color
        shadow_rect = btn.rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(self.screen, SHADOW_COLOR, shadow_rect, border_radius=btn.border_radius)
        pygame.draw.rect(self.screen, current_color, btn.rect, border_radius=btn.border_radius)

        # 绘制齿轮图标
        import math
        cx, cy = btn.rect.center
        r_outer = 13
        r_inner = 8
        teeth = 8
        tooth_width = 3  # 齿宽角度（度）
        color_icon = (220, 220, 220)  # 浅灰白色图标

        points = []
        for i in range(teeth):
            angle_base = (360 / teeth) * i
            half_tooth = tooth_width / 2
            # 齿外侧
            a1 = math.radians(angle_base - half_tooth)
            a2 = math.radians(angle_base + half_tooth)
            # 齿内侧
            a3 = math.radians(angle_base - half_tooth * 0.5)
            a4 = math.radians(angle_base + half_tooth * 0.5)

            # 外齿凸起
            points.append((cx + r_outer * math.cos(a1), cy + r_outer * math.sin(a1)))
            points.append((cx + r_outer * math.cos(a2), cy + r_outer * math.sin(a2)))
            # 齿间凹陷
            points.append((cx + r_inner * math.cos(a4), cy + r_inner * math.sin(a4)))
            points.append((cx + r_inner * math.cos(a3), cy + r_inner * math.sin(a3)))

        if len(points) >= 6:
            pygame.draw.polygon(self.screen, color_icon, points)
            # 中心圆孔
            pygame.draw.circle(self.screen, current_color, (cx, cy), 5)

    def draw_settings(self):
        """绘制设置界面"""
        self.screen.fill(BG_MENU_COLOR)
        cx = self.window_size[0] // 2

        # 标题
        title_font = FontManager.get_font(36, bold=True)
        title_surf = title_font.render("⚙ 设置", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(cx, 60))
        self.screen.blit(title_surf, title_rect)

        # 按钮颜色主题区块
        sec_font = FontManager.get_font(20, bold=True)
        sec_surf = sec_font.render("🎨 按钮颜色主题", True, (255, 215, 0))
        self.screen.blit(sec_surf, sec_surf.get_rect(center=(cx, 100)))

        # 当前选中提示
        hint_font = FontManager.get_font(12)
        hint_text = "当前选中"

        for btn, (theme_name, _, _, _) in self._settings_theme_btns:
            btn.draw(self.screen)

        # 背景颜色主题区块
        bg_sec_surf = sec_font.render("🖥️ 界面背景颜色", True, (255, 215, 0))
        self.screen.blit(bg_sec_surf, bg_sec_surf.get_rect(center=(cx, 260)))

        for btn, (bg_name, _) in self._settings_bg_btns:
            btn.draw(self.screen)

        # 返回按钮
        self.btn_back_menu.draw(self.screen)

    def quit(self):
        """清理资源并退出"""
        pygame.mixer.quit()
        pygame.quit()
