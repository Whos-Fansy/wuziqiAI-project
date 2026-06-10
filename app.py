# -*- coding: utf-8 -*-
"""
app.py - 五子棋AI Web版后端 (Flask)
=====================================
复用现有 core/ 和 ai/ 模块，通过 REST API 暴露游戏功能。
"""
from flask import Flask, render_template, request, jsonify, session
import uuid
import config as _cfg
from core.game import GomokuGame
from core.scoring import ScoreManager

app = Flask(__name__)
app.secret_key = 'gomoku_ai_web_secret_key_3.0'

# 存储多个游戏实例 (按 session/game_id)
games = {}
score_manager = ScoreManager()


def _get_or_create_game():
    """获取或创建当前用户的游戏实例"""
    game_id = session.get('game_id')
    if not game_id or game_id not in games:
        game_id = str(uuid.uuid4())
        session['game_id'] = game_id
        size = _cfg.game("board_size", 9)
        games[game_id] = {
            'game': GomokuGame(size=size),
            'difficulty': 3,
            'undo_stack': [],
            'last_move': None,
            'winning_line': [],
            'game_over': False,
            'ai_thinking': False
        }
    return game_id, games[game_id]


@app.route('/')
def index():
    """返回前端页面"""
    return render_template('index.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    """开始新游戏"""
    data = request.get_json() or {}
    difficulty = data.get('difficulty', 3)
    size = data.get('size', _cfg.game("board_size", 9))
    player_first = data.get('player_first', True)  # 玩家先手标志

    game_id = str(uuid.uuid4())
    session['game_id'] = game_id

    games[game_id] = {
        'game': GomokuGame(size=size),
        'difficulty': difficulty,
        'undo_stack': [],
        'last_move': None,
        'winning_line': [],
        'game_over': False,
        'ai_thinking': False,
        'human_player': 1 if player_first else 2   # 人类执子颜色
    }

    ctx = games[game_id]
    game = ctx['game']

    ai_first_move = None
    if not player_first:
        # AI先行：AI执黑棋(1)，先落一子
        game.current_player = 1
        ai_first_move = game.get_ai_move(difficulty)
        if ai_first_move:
            ar, ac = ai_first_move
            game.board[ar][ac] = 1
            game.current_player = 2  # 轮到人类(白棋2)
            ctx['undo_stack'].append((ar, ac, 1))
            ctx['last_move'] = (ar, ac)

    return jsonify({
        'success': True,
        'board': game.board,
        'size': size,
        'current_player': game.current_player,
        'difficulty': difficulty,
        'player_first': player_first,
        'ai_first_move': ai_first_move  # AI先行时的第一步
    })


@app.route('/api/move', methods=['POST'])
def make_move():
    """玩家落子"""
    game_id, ctx = _get_or_create_game()
    game = ctx['game']

    if ctx['game_over'] or ctx['ai_thinking']:
        return jsonify({'success': False, 'error': '游戏已结束或AI正在思考'})

    data = request.get_json()
    r, c = data.get('row'), data.get('col')

    if r is None or c is None:
        return jsonify({'success': False, 'error': '无效的落子坐标'})

    human_player = ctx.get('human_player', 1)
    if game.current_player != human_player:
        return jsonify({'success': False, 'error': '当前不是玩家回合'})

    if not game.is_legal_move(r, c):
        return jsonify({'success': False, 'error': '非法落子位置'})

    # 记录悔棋历史
    ctx['undo_stack'].append((r, c, human_player))
    if len(ctx['undo_stack']) > _cfg.ui("max_undo", 999999) * 2:
        ctx['undo_stack'].pop(0)

    # 落子
    game.board[r][c] = human_player
    game.current_player = 3 - human_player  # 切换为对方
    ctx['last_move'] = (r, c)

    # 检查胜负
    winner = game.check_winner()
    if winner == human_player:
        ctx['winning_line'] = game.get_winning_line()
        ctx['game_over'] = True
        score_manager.record_game(ctx['difficulty'], winner)
        return jsonify({
            'success': True,
            'board': game.board,
            'current_player': game.current_player,
            'winner': winner,
            'winning_line': ctx['winning_line'],
            'game_over': True
        })

    if game.is_board_full():
        ctx['game_over'] = True
        score_manager.record_game(ctx['difficulty'], 0)
        return jsonify({
            'success': True,
            'board': game.board,
            'current_player': game.current_player,
            'winner': 0,
            'winning_line': [],
            'game_over': True
        })

    # AI 回合
    ai_player = 3 - human_player  # AI的棋子颜色
    ctx['ai_thinking'] = True
    ai_move = game.get_ai_move(ctx['difficulty'])

    if ai_move:
        ar, ac = ai_move
        ctx['undo_stack'].append((ar, ac, ai_player))
        if len(ctx['undo_stack']) > _cfg.ui("max_undo", 999999) * 2:
            ctx['undo_stack'].pop(0)

        game.board[ar][ac] = ai_player
        game.current_player = human_player
        ctx['last_move'] = (ar, ac)

        ai_winner = game.check_winner()
        if ai_winner == ai_player:
            ctx['winning_line'] = game.get_winning_line()
            ctx['game_over'] = True
            ctx['ai_thinking'] = False
            score_manager.record_game(ctx['difficulty'], ai_winner)
            return jsonify({
                'success': True,
                'board': game.board,
                'current_player': game.current_player,
                'ai_move': ai_move,
                'winner': ai_winner,
                'winning_line': ctx['winning_line'],
                'game_over': True
            })

        if game.is_board_full():
            ctx['game_over'] = True
            ctx['ai_thinking'] = False
            score_manager.record_game(ctx['difficulty'], 0)
            return jsonify({
                'success': True,
                'board': game.board,
                'current_player': game.current_player,
                'ai_move': ai_move,
                'winner': 0,
                'winning_line': [],
                'game_over': True
            })

    ctx['ai_thinking'] = False
    return jsonify({
        'success': True,
        'board': game.board,
        'current_player': game.current_player,
        'ai_move': ai_move,
        'winner': 0,
        'winning_line': [],
        'game_over': False,
        'last_move': ctx['last_move']
    })


@app.route('/api/undo', methods=['POST'])
def undo():
    """悔棋：撤销玩家+AI各一步"""
    game_id, ctx = _get_or_create_game()
    game = ctx['game']

    if ctx['game_over']:
        return jsonify({'success': False, 'error': '游戏已结束，无法悔棋'})
    if ctx['ai_thinking']:
        return jsonify({'success': False, 'error': 'AI正在思考，无法悔棋'})
    if len(ctx['undo_stack']) < 2:
        return jsonify({'success': False, 'error': '没有足够的步骤可撤销'})

    # 撤销AI步
    ar, ac, _ = ctx['undo_stack'].pop()
    game.board[ar][ac] = 0
    # 撤销玩家步
    pr, pc, _ = ctx['undo_stack'].pop()
    game.board[pr][pc] = 0

    game.current_player = 1
    ctx['last_move'] = ctx['undo_stack'][-1][:2] if ctx['undo_stack'] else None
    ctx['winning_line'] = []

    return jsonify({
        'success': True,
        'board': game.board,
        'current_player': game.current_player,
        'last_move': ctx['last_move']
    })


@app.route('/api/state', methods=['GET'])
def get_state():
    """获取当前游戏状态"""
    if 'game_id' not in session or session['game_id'] not in games:
        return jsonify({
            'has_game': False,
            'board': None,
            'size': _cfg.game("board_size", 9),
            'current_player': 1,
            'difficulty': 3
        })

    game_id = session['game_id']
    ctx = games[game_id]
    game = ctx['game']

    return jsonify({
        'has_game': True,
        'board': game.board,
        'size': game.size,
        'current_player': game.current_player,
        'difficulty': ctx['difficulty'],
        'game_over': ctx['game_over'],
        'winning_line': ctx['winning_line'],
        'last_move': ctx['last_move'],
        'ai_thinking': ctx['ai_thinking']
    })


@app.route('/api/scores', methods=['GET'])
def get_scores():
    """获取积分统计"""
    return jsonify({
        'scores': score_manager.get_scores(),
        'stats': score_manager.get_stats(),
        'streak': score_manager.get_streak(),
        'total_games': score_manager.get_total_games(),
        'recent_history': score_manager.get_recent_history(10)
    })


@app.route('/api/clear_scores', methods=['POST'])
def clear_scores():
    """清空积分数据"""
    score_manager.clear_scores()
    return jsonify({'success': True})


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取前端需要的配置"""
    return jsonify({
        'board_size': _cfg.game("board_size", 9),
        'cell_size': _cfg.ui("cell_size", 60),
        'margin': _cfg.ui("margin", 50),
        'colors': {
            'board': _cfg.color("board"),
            'line': _cfg.color("line"),
            'black_stone': _cfg.color("black_stone"),
            'white_stone': _cfg.color("white_stone"),
            'highlight': _cfg.color("highlight"),
            'bg_menu': _cfg.color("bg_menu"),
            'text': _cfg.color("text"),
            'btn': _cfg.color("btn"),
            'btn_hover': _cfg.color("btn_hover"),
            'btn_danger': _cfg.color("btn_danger"),
            'btn_danger_hover': _cfg.color("btn_danger_hover"),
            'btn_restart': _cfg.color("btn_restart"),
            'btn_restart_hover': _cfg.color("btn_restart_hover"),
        },
        'max_undo': _cfg.ui("max_undo", 999999),
        'difficulty': {
            'easy': _cfg.ai("difficulty", {}).get("easy", 2),
            'medium': _cfg.ai("difficulty", {}).get("medium", 3),
            'hard': _cfg.ai("difficulty", {}).get("hard", 4)
        }
    })


if __name__ == '__main__':
    print("=" * 50)
    print("五子棋AI 3.0 Web版")
    print(f"访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)