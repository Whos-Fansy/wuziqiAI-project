# -*- coding: utf-8 -*-
"""
core/scoring.py - 用户积分与战绩统计系统
=========================================
管理按难度分类的积分累计，持久化存储到本地JSON文件。

积分规则：
  - 胜利: +1
  - 平局:  0
  - 失败: −1
  - 按难度（简单/中等/困难）分别独立统计

v3.0 优化:
  - Win/Loss/Draw 独立统计（胜场、负场、平局、胜率）
  - 当前连胜 & 历史最长连胜记录
"""

import json
import os
from datetime import datetime

# 积分数据文件（与 main.py 同级）
SCORE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scores.json")

DIFFICULTY_LABEL = {2: "简单", 3: "中等", 4: "困难"}
DIFFICULTY_KEY   = {"简单": "easy", "中等": "medium", "困难": "hard"}
RESULT_LABEL     = {1: "胜", 2: "负", 0: "平"}


class ScoreManager:
    """
    积分管理器 — 核心职责：
      1. 计算单局积分
      2. 更新分难度累计积分
      3. 维护 Win/Loss/Draw 统计 & 连胜记录
      4. JSON 文件的读写持久化
    """

    def __init__(self):
        self.data = self._load()

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------
    def record_game(self, difficulty: int, winner: int):
        """
        记录一局游戏结果并返回本局得分。
        :param difficulty: AI 搜索深度 (2/3/4)
        :param winner: 1=人类胜, 2=AI胜, 0=平局
        :return: 本局得分 (-1 / 0 / +1)
        """
        result_label = RESULT_LABEL[winner]
        difficulty_label = DIFFICULTY_LABEL[difficulty]

        # 计算得分
        if winner == 1:        # 人类胜利
            score = +1
        elif winner == 2:      # AI 胜利
            score = -1
        else:                  # 平局
            score = 0

        key = DIFFICULTY_KEY[difficulty_label]

        # ---- 更新累计积分 ----
        self.data[key] = self.data.get(key, 0) + score

        # ---- 更新 Win/Loss/Draw 统计 ----
        self.data.setdefault("stats", {})
        for dk in ("easy", "medium", "hard"):
            if dk not in self.data["stats"]:
                self.data["stats"][dk] = {"wins": 0, "losses": 0, "draws": 0}

        stats = self.data["stats"][key]
        if winner == 1:
            stats["wins"] += 1
        elif winner == 2:
            stats["losses"] += 1
        else:
            stats["draws"] += 1

        # ---- 更新连胜记录 ----
        self.data.setdefault("streak", 0)      # 当前连胜
        self.data.setdefault("best_streak", 0) # 最长连胜

        if winner == 1:
            self.data["streak"] += 1
            if self.data["streak"] > self.data["best_streak"]:
                self.data["best_streak"] = self.data["streak"]
        else:
            self.data["streak"] = 0

        # ---- 记录历史 ----
        self.data.setdefault("history", [])
        self.data["history"].append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "difficulty": difficulty_label,
            "result": result_label,
            "score": score
        })

        self._save()
        return score

    def get_scores(self):
        """
        获取各难度累计积分。
        :return: {"简单": int, "中等": int, "困难": int}
        """
        return {
            "简单": self.data.get("easy", 0),
            "中等": self.data.get("medium", 0),
            "困难": self.data.get("hard", 0)
        }

    def get_stats(self):
        """
        获取各难度的 Win/Loss/Draw 统计及胜率。
        :return: {"简单": {"wins":n, "losses":n, "draws":n, "total":n, "win_rate":f}, ...}
        """
        result = {}
        for label, key in [("简单", "easy"), ("中等", "medium"), ("困难", "hard")]:
            s = self.data.get("stats", {}).get(key, {"wins": 0, "losses": 0, "draws": 0})
            total = s["wins"] + s["losses"] + s["draws"]
            win_rate = (s["wins"] / total * 100) if total > 0 else 0.0
            result[label] = {
                "wins": s["wins"],
                "losses": s["losses"],
                "draws": s["draws"],
                "total": total,
                "win_rate": win_rate
            }
        return result

    def get_streak(self):
        """
        获取连胜信息。
        :return: {"current": int, "best": int}
        """
        return {
            "current": self.data.get("streak", 0),
            "best": self.data.get("best_streak", 0)
        }

    def get_total_games(self):
        """获取总对局数"""
        total = 0
        for key in ("easy", "medium", "hard"):
            s = self.data.get("stats", {}).get(key, {"wins": 0, "losses": 0, "draws": 0})
            total += s["wins"] + s["losses"] + s["draws"]
        return total

    def get_recent_history(self, count: int = 10):
        """
        获取最近 N 条对局记录。
        :return: 记录列表，按时间倒序
        """
        history = self.data.get("history", [])
        return history[-count:][::-1]  # 最新的在前

    def clear_scores(self):
        """
        清空所有积分数据和对局历史记录，重置为默认状态。
        """
        self.data = self._default_data()
        self._save()

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _default_data(self):
        return {
            "easy": 0,
            "medium": 0,
            "hard": 0,
            "stats": {
                "easy":   {"wins": 0, "losses": 0, "draws": 0},
                "medium": {"wins": 0, "losses": 0, "draws": 0},
                "hard":   {"wins": 0, "losses": 0, "draws": 0}
            },
            "streak": 0,
            "best_streak": 0,
            "history": []
        }

    def _load(self):
        try:
            if os.path.exists(SCORE_FILE):
                with open(SCORE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                default = self._default_data()
                default.update(loaded)
                # 数据完整性校验：若历史记录为空，则所有积分应重置为0
                if not default.get("history"):
                    default["easy"] = 0
                    default["medium"] = 0
                    default["hard"] = 0
                # 补齐 stats 子字段
                for dk in ("easy", "medium", "hard"):
                    if "stats" not in default:
                        default["stats"] = {}
                    if dk not in default["stats"]:
                        default["stats"][dk] = {"wins": 0, "losses": 0, "draws": 0}
                    else:
                        for field in ("wins", "losses", "draws"):
                            if field not in default["stats"][dk]:
                                default["stats"][dk][field] = 0
                if "streak" not in default:
                    default["streak"] = 0
                if "best_streak" not in default:
                    default["best_streak"] = 0
                return default
        except (json.JSONDecodeError, IOError):
            pass
        return self._default_data()

    def _save(self):
        try:
            with open(SCORE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[ScoreManager] 写入 scores.json 失败: {e}")