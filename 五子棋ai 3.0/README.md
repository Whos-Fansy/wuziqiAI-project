# AI五子棋1.0版本
## 文件架构

GomokuProject/
│
├── core/                   # 核心游戏引擎模块
│   ├── __init__.py
│   └── game.py             # 存放 GomokuGame 类（处理棋盘状态、规则、落子、胜负）
│
├── ai/                     # AI 决策与算法模块
│   ├── __init__.py
│   ├── search.py           # 存放 Minimax 算法和 Alpha-Beta 剪枝核心逻辑
│   └── evaluation.py       # 存放启发式评估函数（负责对五子棋棋型进行打分）
│
├── ui/                     # 交互与界面展现模块
│   ├── __init__.py
│   └── gui.py              # （后续扩展）负责 pygame 漂亮的图形界面
│
├── main.py                 # 整个项目的总入口
├── requirements.txt        # 记录项目依赖项（如 pygame）
└── README.md               # 你的实验项目说明文档

这一版采用的是经典博弈树搜索（传统AI阶段）

## 核心算法
极大极小值算法（Minimax）与$\alpha-\beta$剪枝

## 优化方向（按顺序进行）
1.前端用户界面功能优化
2.优化评估函数（包括ai能力测试算法）
3.增加用户积分系统
4.搭建Internet网页端接口
5.添加深度强化学习，利用蒙特卡洛树搜索（MCTS） + 深度神经网络（类似 AlphaZero 的架构）

# AI五子棋2.0版本

## 前端优化
1.增加了初始界面和结算界面
2.调整pygame显示框大小
3.添加难度选择玩法，对应不同的minimax算法搜索深度
4.增加渲染效果，优化互动过程

## 后端优化
1.增加悔棋功能
2.记录回合数和对弈时间

# AI五子棋3.0版本

## AI算法优化
1. 新增移动排序 (Move Ordering)
2. 新增 Zobrist 哈希置换表
3. 新增杀棋检测 (Threat Space Search) 

## 战绩系统优化
4. 增加对局结果分难度统计
5. 增加对局记录功能
6. 新增清空战绩功能 

## 前端交互优化
7. 新增快捷键提示栏
8. 棋盘坐标标签升级
9. 优化对局中按钮位置
10. 增加界面和按钮颜色修改设置


## 更新文件架构

```
GomokuProject/
│
├── main.py               # 程序总入口，初始化游戏并启动主循环
├── config.json            # 全局配置文件（颜色主题、棋盘尺寸、AI参数、积分规则等）
├── config.py              # 配置加载器，从 config.json 读取并提供模块化属性访问
├── scores.json            # 积分与战绩数据持久化文件（分难度积分、胜率、连胜记录）
├── requirements.txt       # 项目依赖（pygame）
├── README.md              # 项目文档
│
├── core/
│   ├── __init__.py        # 包初始化
│   ├── game.py            # 棋盘状态管理、落子规则、胜负判定、AI调用接口
│   └── scoring.py         # 积分记录、战绩统计（胜/负/平）、连胜追踪、对局历史
│
├── ai/
│   ├── __init__.py        # 包初始化
│   ├── search.py          # Alpha-Beta剪枝搜索、Zobrist置换表、移动排序、杀棋检测
│   └── evaluation.py      # 启发式评估函数（五元组滑动窗口打分、中心位置加权）
│
└── ui/
    ├── __init__.py        # 包初始化
    └── gui.py             # Pygame图形界面（主菜单、棋盘渲染、动画、设置页、战绩页、齿轮图标按钮）
```
代码量：2122行

## 4.0版本工作（实现AI全栈开发）
1. 前端网页设计（HTML+CSS+Javascript）
2. 本地数据库搭建（SQlite）
3. 账号ID系统
4. 搭建五子棋AI接口（Fast API）
5. 整合工作