# -*- coding: utf-8 -*-
"""
config.py — 全局配置加载器
==========================
从 config.json 读取配置，提供模块化属性访问。
所有模块应通过此模块获取配置，而非硬编码常量。
"""
import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# 延迟加载（避免在 import 阶段因 JSON 异常崩溃）
_cfg = None


def _load():
    global _cfg
    if _cfg is not None:
        return _cfg
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        _cfg = json.load(f)
    return _cfg


def reload():
    """强制重新加载配置文件（运行时热重载）"""
    global _cfg
    _cfg = None
    return _load()


# ==================== 便捷访问器 ====================

def game(key, default=None):
    return _load().get("game", {}).get(key, default)


def ai(key, default=None):
    return _load().get("ai", {}).get(key, default)


def ui(key, default=None):
    return _load().get("ui", {}).get(key, default)


def scoring(key, default=None):
    return _load().get("scoring", {}).get(key, default)


def color(name):
    """获取 RGBA 颜色元组，范例: config.color('board') -> (220,179,92)"""
    c = _load().get("ui", {}).get("colors", {}).get(name, [255, 255, 255])
    return tuple(c)


def difficulty_depth(label):
    """
    难度标签 → 搜索深度
    label: '简单' / '中等' / '困难'
    """
    mapping = {"简单": "easy", "中等": "medium", "困难": "hard"}
    key = mapping.get(label, "medium")
    return _load().get("ai", {}).get("difficulty", {}).get(key, 3)


def eval_param(name, default=0):
    """评估参数快捷访问"""
    return _load().get("ai", {}).get("evaluation", {}).get(name, default)