# d:/game/puzzle/src/const.py
# ゲーム全体の定数定義
# 画面サイズ、色、状態名、タイマー時間などを一元管理するため
# RELEVANT FILES: src/app.py, src/states/attract.py

# 画面サイズ
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 1000
FPS = 60

# 色定義 (R, G, B)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (64, 64, 64)  # インベントリ背景用

# 状態名（ステート）
STATE_ATTRACT = "ATTRACT"
STATE_TITLE = "TITLE"
STATE_PLAY = "PLAY"
STATE_CONFIRM = "CONFIRM"
STATE_DEV = "DEV"

# タイマー設定 (ミリ秒)
TITLE_WAIT_TIME = 3000  # タイトル画面の表示時間 (3秒)
PLAY_TIMEOUT = 60000  # プレイ中の無操作タイムアウト (1分)
CONFIRM_TIMEOUT = 10000  # コンティニュー確認のタイムアウト (10秒)
MOUSE_MOVE_THRESHOLD = 100  # マウス移動検知の閾値 (ピクセル移動量の累積など)

STRING_TITLE = "Puzzle Game"

# タイルID
TILE_NULL = "00000"  # 壁・無効エリア
TILE_PIT = "00100"  # 奈落
TILE_NORMAL = "00200"  # 通常マス
TILE_GOAL = "00300"  # ゴール
TILE_UP = "00400"  # 上矢印
TILE_DOWN = "00500"  # 下矢印
TILE_RIGHT = "00600"  # 右矢印
TILE_LEFT = "00700"  # 左矢印
TILE_WARP = "00800"  # ワープ

# シミュレーション設定
SIM_STEP_DELAY = 500  # ms
SIM_ANIM_DURATION = 500  # ms - アニメーション時間 (< SIM_STEP_DELAY)

# ゲーム状態
GAME_STATE_PLACING = "placing"
GAME_STATE_SIMULATING = "simulating"

# 描画設定
TILE_SIZE = 64  # タイルの描画サイズ (px)
