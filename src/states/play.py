# d:/game/puzzle/src/states/play.py
# プレイモードの状態
# ゲームのメインループ（現在はプレースホルダー）
# 無操作状態を監視し、一定時間経過でコンティニュー確認へ遷移する
# RELEVANT FILES: src/const.py, src/core/state_machine.py

import pygame
from src.core.state_machine import State
from src.const import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BLACK,
    PLAY_TIMEOUT,
    COLOR_WHITE,
    GAME_STATE_PLACING,
    GAME_STATE_SIMULATING,
    SIM_STEP_DELAY,
    SIM_ANIM_DURATION,
)
from src.game.loader import StageLoader
from src.game.map import TileMap
from src.game.inventory import Inventory
from src.game.simulator import Simulator


class PlayState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 48)
        self.inactivity_timer = 0
        self.last_mouse_pos = None

        # ゲームコンポーネント
        self.loader = StageLoader()
        self.tile_map = None
        self.inventory = None
        self.current_level = 1

        # ドラッグ＆ドロップ操作用
        self.held_piece = None  # 現在掴んでいる駒
        self.is_dragging = False  # ドラッグ中フラグ
        self.drag_start_pos = (0, 0)  # ドラッグ開始位置
        self.drag_threshold = 5  # ドラッグとみなす移動量

        # シミュレーション用
        self.game_state = GAME_STATE_PLACING
        self.simulator = None
        self.sim_timer = 0
        self.sim_last_result = "CONTINUE"
        self.prev_player_positions = []  # アニメーション用: 各プレイヤーの移動前座標 [{"x": int, "y": int}]

    def enter(self):
        print("プレイモードに遷移しました")
        self.inactivity_timer = 0
        self.last_mouse_pos = pygame.mouse.get_pos()
        self.held_piece = None
        self.is_dragging = False

        self.game_state = GAME_STATE_PLACING
        self.simulator = None
        self.sim_timer = 0

        # ステージ読み込み（リセットも兼ねてここで読み込む）
        try:
            stage_data = self.loader.load_stage(self.current_level)
            self.tile_map = TileMap(stage_data["map_data"])
            self.inventory = Inventory(stage_data["players"])
        except Exception as e:
            print(f"Error loading stage {self.current_level}: {e}")

    def handle_event(self, event):
        # マウスが動いたらタイマーリセット
        if event.type == pygame.MOUSEMOTION:
            self.inactivity_timer = 0

            if self.game_state == GAME_STATE_PLACING:
                # ドラッグ判定
                if self.held_piece and not self.is_dragging:
                    dx = event.pos[0] - self.drag_start_pos[0]
                    dy = event.pos[1] - self.drag_start_pos[1]
                    if (dx * dx + dy * dy) > self.drag_threshold**2:
                        self.is_dragging = True

        # マウスボタンダウン (掴む処理)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if (
                event.button == 1 and self.game_state == GAME_STATE_PLACING
            ):  # 左クリックかつ配置モード
                if self.held_piece:
                    # 既に掴んでいる場合は配置試行（クリック＆クリック操作の2回目）
                    self._try_place_piece(event.pos)
                else:
                    # 何も掴んでいない場合は掴む試行
                    self._try_grab_piece(event.pos)

        # マウスボタンアップ (ドラッグ＆ドロップの配置処理)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.game_state == GAME_STATE_PLACING:
                # ドラッグ中であれば配置試行
                if self.held_piece and self.is_dragging:
                    self._try_place_piece(event.pos)

        # 'D'キーで開発者モードへ
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                from src.states.dev import DevState

                self.manager.change_state(DevState(self.manager))

    def _try_grab_piece(self, pos):
        """駒を掴む試行"""
        # 1. インベントリから探す
        piece = self.inventory.get_piece_at(pos)
        if piece:
            self.held_piece = piece
            self.drag_start_pos = pos
            self.is_dragging = False
            return

        # 2. マップから探す
        grid_x, grid_y = self.tile_map.get_grid_pos(pos[0], pos[1])
        piece = self.tile_map.remove_piece_at(grid_x, grid_y)
        if piece:
            self.held_piece = piece
            self.drag_start_pos = pos
            self.is_dragging = False
            return

    def _try_place_piece(self, pos):
        """駒を配置する試行"""
        grid_x, grid_y = self.tile_map.get_grid_pos(pos[0], pos[1])

        # 有効なタイルかチェック
        if self.tile_map.is_valid_tile(grid_x, grid_y):
            self.tile_map.place_piece(grid_x, grid_y, self.held_piece)
            self.held_piece = None
            self.is_dragging = False

            # 全ての駒が配置されたかチェック
            if len(self.inventory.players_data) == 0:
                self._start_simulation()
        else:
            # 無効な場所なら離す（ドラッグ中ならインベントリに戻る、クリック操作なら戻る）
            # 仕様：もし配置できない場所だったらインベントリに戻す
            self.inventory.add_piece(self.held_piece)
            self.held_piece = None
            self.is_dragging = False

    def _start_simulation(self):
        print("Start Simulation")
        self.game_state = GAME_STATE_SIMULATING
        self.simulator = Simulator(self.tile_map.map_data, self.tile_map.placed_pieces)
        self.sim_timer = SIM_STEP_DELAY  # 即座に最初のステップを実行させるため
        self.sim_last_result = "CONTINUE"
        # 初期座標を記録
        self.prev_player_positions = [
            {"x": p["grid_x"], "y": p["grid_y"]} for p in self.tile_map.placed_pieces
        ]

    def update(self, dt):
        # フレームごとに無操作タイマーを加算
        # handle_eventでリセットされない限り加算され続ける
        self.inactivity_timer += dt

        if self.inactivity_timer >= PLAY_TIMEOUT:
            from src.states.confirm import ConfirmContinueState

            self.manager.change_state(ConfirmContinueState(self.manager))

        # シミュレーション更新
        if self.game_state == GAME_STATE_SIMULATING:
            self.sim_timer += dt

            if self.sim_timer >= SIM_STEP_DELAY:
                # 前回の結果判定をここで行う（アニメーション終了後）
                if self.sim_last_result == "WIN":
                    print(f"Level {self.current_level} Cleared!")
                    self.current_level += 1
                    self.enter()
                    return
                elif self.sim_last_result == "LOSE":
                    print("Example Failed... Resetting.")
                    self.enter()
                    return

                # 次のステップへ
                self.sim_timer = 0

                # 現在位置を「前回位置」として保存
                self.prev_player_positions = [
                    {"x": p["grid_x"], "y": p["grid_y"]}
                    for p in self.tile_map.placed_pieces
                ]

                # シミュレーション実行 (座標が更新される)
                self.sim_last_result = self.simulator.step()

    def draw(self, surface):
        surface.fill(COLOR_BLACK)

        # レイアウト定数 (簡易)
        INVENTORY_WIDTH = 120

        if self.tile_map:
            # マップ描画エリア (画面幅 - インベントリ幅)
            play_area_width = SCREEN_WIDTH - INVENTORY_WIDTH

            # マップをプレイエリアの中央に配置
            map_x = (play_area_width - self.tile_map.width) // 2
            map_y = (SCREEN_HEIGHT - self.tile_map.height) // 2

            # --- マップ描画 ---
            # シミュレーション中はTileMapの駒描画を一時的に無効化し、補間描画を行う
            real_placed_pieces = self.tile_map.placed_pieces
            if self.game_state == GAME_STATE_SIMULATING:
                self.tile_map.placed_pieces = []  # 一時的に隠す

            self.tile_map.draw(surface, map_x, map_y)

            if self.game_state == GAME_STATE_SIMULATING:
                self.tile_map.placed_pieces = real_placed_pieces  # 戻す

                # アニメーション補間して描画
                import src.const as c  # 定数参照用

                # 等速直線運動 (t: 0.0 -> 1.0)
                t = min(self.sim_timer / SIM_ANIM_DURATION, 1.0)

                # スプライトアニメーション (フレーム計算)
                # 0~1の進行度を4フレームにマッピング (0, 1, 2, 3)
                frame_index = int(t * 4) % 4

                for i, p in enumerate(self.tile_map.placed_pieces):
                    if i < len(self.prev_player_positions):
                        # 最新座標 (grid)
                        curr_gx, curr_gy = p["grid_x"], p["grid_y"]
                        # 前回座標
                        prev_pos = self.prev_player_positions[i]
                        prev_gx, prev_gy = prev_pos["x"], prev_pos["y"]

                        # 補間座標 (grid単位) - 等速
                        lerp_gx = prev_gx + (curr_gx - prev_gx) * t
                        lerp_gy = prev_gy + (curr_gy - prev_gy) * t

                        # 画面座標変換
                        screen_x = map_x + lerp_gx * c.TILE_SIZE
                        screen_y = map_y + lerp_gy * c.TILE_SIZE

                        # 画像取得 (TileMapの新しいplayer_imagesを使用)
                        direction = p["piece"]["direction"]
                        # 方向に対応するフレームリストを取得
                        frames = self.tile_map.player_images.get(direction)
                        if frames and len(frames) > 0:
                            # フレーム数が4未満の場合の安全策
                            safe_frame_index = frame_index % len(frames)
                            img = frames[safe_frame_index]
                            surface.blit(img, (screen_x, screen_y))
                        else:
                            # 万が一画像がない場合は矩形で描画 (デバッグ用)
                            pygame.draw.rect(
                                surface,
                                (255, 0, 0),
                                (screen_x, screen_y, c.TILE_SIZE, c.TILE_SIZE),
                            )

            # インベントリ領域の計算 (画面右端)
            inventory_rect = pygame.Rect(
                play_area_width, 0, INVENTORY_WIDTH, SCREEN_HEIGHT
            )

            if self.inventory:
                self.inventory.draw(surface, inventory_rect)

        # レベル表示 (左上)
        level_text = self.font.render(f"Level {self.current_level}", True, COLOR_WHITE)
        surface.blit(level_text, (20, 20))

        # 掴んでいる駒の描画 (カーソル追従)
        if self.held_piece:
            mx, my = pygame.mouse.get_pos()
            # 駒の中央をカーソルに合わせる（画像サイズがわかれば。Inventoryから取得するか、Mapから取得するか）
            # インベントリとマップの画像ローダーを共有していないので、とりあえずInventoryの画像を使う
            # 実際はリファクタリングで共通化すべきだが、ここではinventory.imagesを参照
            img = self.inventory.images.get(self.held_piece["direction"])
            if img:
                rect = img.get_rect(center=(mx, my))
                surface.blit(img, rect)
