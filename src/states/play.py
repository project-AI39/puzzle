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
    INVENTORY_WIDTH,
    SIMULATION_TIMEOUT,
)
from src.game.loader import StageLoader
from src.game.map import TileMap
from src.game.inventory import Inventory
from src.game.simulator import Simulator


class PlayState(State):
    def __init__(self, manager, stage_data=None):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 48)

        # 結果表示用
        self.result_font = pygame.font.SysFont("MS Gothic", 64, bold=True)
        self.result_timer = 0
        self.result_duration = 1000  # 1秒

        self.inactivity_timer = 0
        self.last_mouse_pos = None

        # ゲームコンポーネント
        self.loader = StageLoader()
        self.tile_map = None
        self.inventory = None
        self.current_level = 1

        # テストプレイ用データ
        self.custom_stage_data = stage_data

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

        # ガイド用
        self.show_guide = False
        self.guide_timer = 0

        # ライフ
        self.lives = 5

        # デモモード用
        self.is_demo = False
        self.demo_phase = "IDLE"
        self.demo_timer = 0
        self.demo_wait_timer = 0  # デモ用ウェイト

    def enter(self):
        print("プレイモードに遷移しました")
        self.inactivity_timer = 0
        self.last_mouse_pos = pygame.mouse.get_pos()
        self.held_piece = None
        self.is_dragging = False

        self.game_state = GAME_STATE_PLACING
        self.simulator = None
        self.sim_timer = 0
        self.result_timer = 0  # 初期化

        self.show_guide = False
        self.guide_timer = 0

        # デモモードはデフォルトOFF
        self.is_demo = False

        # ステージ読み込み（リセットも兼ねてここで読み込む）
        try:
            if self.custom_stage_data:
                # テストプレイ用データを使用
                stage_data = self.custom_stage_data
                self.tile_map = TileMap(stage_data["map_data"])

                # 自動リサイズ (DevModeからのテストプレイ時も適用してOK)
                play_area_w = SCREEN_WIDTH - INVENTORY_WIDTH
                play_area_h = SCREEN_HEIGHT - 100  # ヘッダー分などを考慮
                self.tile_map.fit_to_area(play_area_w, play_area_h)

                # "answer" (正解配置/初期配置) が含まれている場合
                if "answer" in stage_data:
                    # インベントリは空にする（全て配置済み）
                    self.inventory = Inventory([])
                    # 駒を配置
                    for p_data in stage_data["answer"]:
                        self.tile_map.place_piece(
                            p_data["grid_x"], p_data["grid_y"], p_data["piece"]
                        )

                    # auto_playフラグがあればシミュレーション開始
                    if stage_data.get("auto_play", False):
                        print("Auto-playing answer...")
                        self._start_simulation()
                    else:
                        # 手動プレイ（配置状態からスタート）
                        print("Manual Play from Setup")
                        self.game_state = GAME_STATE_PLACING
                else:
                    # 通常のテストプレイ（手動配置）
                    self.inventory = Inventory(stage_data["players"][:])

            else:
                stage_data = self.loader.load_stage(self.current_level)
                self.tile_map = TileMap(stage_data["map_data"])

                # 自動リサイズ
                play_area_w = SCREEN_WIDTH - INVENTORY_WIDTH
                play_area_h = SCREEN_HEIGHT - 100
                self.tile_map.fit_to_area(play_area_w, play_area_h)

                self.inventory = Inventory(stage_data["players"][:])
                # インベントリサイズもマップに合わせる
                self.inventory.set_tile_size(self.tile_map.tile_size, INVENTORY_WIDTH)

                if self.current_level == 1:
                    self.show_guide = True

        except Exception as e:
            print(f"Error loading stage {self.current_level}: {e}")

    def setup_demo(self, stage_data):
        """デモモード用にステージをロードして初期化"""
        self.is_demo = True
        self.custom_stage_data = stage_data
        self.current_level = 0  # 無視されるが念のため

        # enter() と同様の初期化を行うが、自動プレイを前提とする
        self.inactivity_timer = 0
        self.last_mouse_pos = pygame.mouse.get_pos()
        self.held_piece = None
        self.game_state = GAME_STATE_PLACING
        self.simulator = None
        self.sim_timer = 0
        self.result_timer = 0  # 初期化
        self.show_guide = False  # デモ中ガイドは不要

        try:
            # インベントリ初期化
            self.tile_map = TileMap(stage_data["map_data"])

            # 自動リサイズ
            play_area_w = SCREEN_WIDTH - INVENTORY_WIDTH
            play_area_h = SCREEN_HEIGHT - 100
            self.tile_map.fit_to_area(play_area_w, play_area_h)

            self.inventory = Inventory(stage_data["players"][:])
            # インベントリサイズもマップに合わせる
            self.inventory.set_tile_size(self.tile_map.tile_size, INVENTORY_WIDTH)

            # デモ開始
            self.demo_phase = "PLACING"
            self.demo_timer = 0
            print("Demo Setup Complete")
        except Exception as e:
            print(f"Error setup_demo: {e}")

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
                        self.show_guide = False  # ドラッグ開始でも消す

        # マウスボタンダウン (掴む処理)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if (
                event.button == 1 and self.game_state == GAME_STATE_PLACING
            ):  # 左クリックかつ配置モード
                self.show_guide = False  # 操作開始で消す
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
        self.sim_elapsed_time = 0
        self.sim_last_result = "CONTINUE"
        # 初期座標を記録
        self.prev_player_positions = [
            {"x": p["grid_x"], "y": p["grid_y"]} for p in self.tile_map.placed_pieces
        ]

    def _update_demo(self, dt):
        """デモモードの更新処理"""
        if self.demo_phase == "PLACING":
            self.demo_timer += dt
            place_interval = 1500

            if self.inventory and len(self.inventory.players_data) > 0:
                if self.demo_timer >= place_interval:
                    piece_data = self.inventory.players_data[0]
                    if "answer" in piece_data:
                        ans = piece_data["answer"]
                        piece = {"direction": piece_data["direction"]}
                        self.tile_map.place_piece(ans["x"], ans["y"], piece)
                    self.inventory.remove_piece(piece_data)
                    self.demo_timer = 0
            else:
                self._start_simulation()
                self.demo_phase = "SIMULATING"

        elif self.demo_phase == "SIMULATING":
            self.sim_timer += dt
            if self.sim_timer >= SIM_STEP_DELAY:
                if self.sim_last_result in ["WIN", "LOSE"]:
                    self.demo_phase = "DONE"
                    return  # 終了

                self.sim_timer = 0
                self.prev_player_positions = [
                    {"x": p["grid_x"], "y": p["grid_y"]}
                    for p in self.tile_map.placed_pieces
                ]
                self.sim_last_result = self.simulator.step()

    def update(self, dt):
        if self.is_demo:
            self._update_demo(dt)
            return

        # フレームごとに無操作タイマーを加算
        # handle_eventでリセットされない限り加算され続ける
        self.inactivity_timer += dt

        if self.inactivity_timer >= PLAY_TIMEOUT:
            from src.states.confirm import ConfirmContinueState

            self.manager.change_state(ConfirmContinueState(self.manager))

        # ガイド更新
        if self.show_guide:
            self.guide_timer += dt

        # シミュレーション更新
        if self.game_state == GAME_STATE_SIMULATING:
            self.sim_timer += dt
            self.sim_elapsed_time += dt

            # タイムアウトチェック
            if (
                self.sim_elapsed_time >= SIMULATION_TIMEOUT
                and self.sim_last_result == "CONTINUE"
            ):
                print("Simulation Timed Out! Force LOSE.")
                self.sim_last_result = "LOSE"
                self.sim_timer = SIM_STEP_DELAY  # 強制的に結果処理へ

            if self.sim_timer >= SIM_STEP_DELAY:
                # 前回の結果判定をここで行う（アニメーション終了後）
                if self.sim_last_result in ["WIN", "LOSE"]:
                    # 結果表示ウェイト
                    if self.result_timer == 0:
                        self.result_timer = self.result_duration
                        return  # 1秒待機開始

                    self.result_timer -= dt
                    if self.result_timer > 0:
                        return  # 待機中

                    if self.sim_last_result == "WIN":
                        print(f"Level {self.current_level} Cleared!")

                        if self.custom_stage_data:
                            # テストプレイ完了 -> 開発者モードに戻る
                            from src.states.dev import DevState

                            print("Test Play Cleared! Returning to Dev Mode.")
                            self.manager.change_state(
                                DevState(
                                    self.manager, initial_data=self.custom_stage_data
                                )
                            )
                            return

                        # 次のレベルがあるか確認
                        next_level = self.current_level + 1
                        available_levels = self.loader.get_available_levels()

                        if next_level in available_levels:
                            self.current_level = next_level
                            self.lives = 5  # ステージクリアでライフ回復
                            self.enter()
                        else:
                            # 全ステージクリア -> ゲームクリア画面へ
                            from src.states.game_clear import GameClearState

                            self.manager.change_state(GameClearState(self.manager))
                        return
                    elif self.sim_last_result == "LOSE":
                        self.lives -= 1
                        print(f"Failed... Lives left: {self.lives}")

                        if self.lives <= 0:
                            # ゲームオーバー
                            from src.states.game_over import GameOverState

                            if self.custom_stage_data:
                                # テストプレイ -> DevStateへ戻る
                                from src.states.dev import DevState

                                next_class = DevState
                                next_args = {"initial_data": self.custom_stage_data}
                            else:
                                # 通常プレイ -> タイトルへ
                                from src.states.attract import AttractState

                                next_class = AttractState
                                next_args = {}

                            self.manager.change_state(
                                GameOverState(
                                    self.manager,
                                    next_state_class=next_class,
                                    next_state_args=next_args,
                                )
                            )
                            return
                        else:
                            # リトライ（ライフ維持）
                            print("Resetting for retry...")
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
        if self.manager.app.bg_image:
            surface.blit(self.manager.app.bg_image, (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        if self.tile_map:
            # マップ描画エリア (画面幅 - インベントリ幅)
            play_area_width = SCREEN_WIDTH - INVENTORY_WIDTH
            play_area_height = SCREEN_HEIGHT

            # 有効領域(=マップの中身)を画面中央に配置するためのオフセット計算
            content_off_x, content_off_y, content_w, content_h = (
                self.tile_map.get_content_info()
            )

            # 画面中央オフセット = 描画開始オフセット + content_off
            # 描画開始オフセット = 画面中央オフセット - content_off
            center_x = (play_area_width - content_w) // 2
            center_y = (play_area_height - content_h) // 2

            map_x = center_x - content_off_x
            map_y = center_y - content_off_y

            # --- マップ描画 ---
            # シミュレーション中はTileMapの駒描画を一時的に無効化し、補間描画を行う
            real_placed_pieces = self.tile_map.placed_pieces
            if self.game_state == GAME_STATE_SIMULATING:
                self.tile_map.placed_pieces = []  # 一時的に隠す

            self.tile_map.draw(surface, map_x, map_y)

            if self.game_state == GAME_STATE_SIMULATING:
                self.tile_map.placed_pieces = real_placed_pieces  # 戻す

                # アニメーション補間して描画

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
                        screen_x = map_x + lerp_gx * self.tile_map.tile_size
                        screen_y = map_y + lerp_gy * self.tile_map.tile_size

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
                                (
                                    screen_x,
                                    screen_y,
                                    self.tile_map.tile_size,
                                    self.tile_map.tile_size,
                                ),
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

        # ライフ表示
        lives_text = self.font.render(f"Lives: {self.lives}", True, COLOR_WHITE)
        surface.blit(lives_text, (20, 70))

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

        # Level 1 ガイドアニメーション (インベントリ -> マップ配置)
        if (
            self.show_guide
            and self.inventory
            and self.tile_map
            and self.manager.app.cursor_img
        ):
            # アニメーション周期 (2秒: 1秒移動、1秒待機)
            cycle = 2000
            t = (self.guide_timer % cycle) / 1000.0  # 0.0 - 2.0

            # 始点: インベントリの先頭アイテム
            start_rect = self.inventory.get_item_rect(
                0,
                pygame.Rect(
                    SCREEN_WIDTH - INVENTORY_WIDTH, 0, INVENTORY_WIDTH, SCREEN_HEIGHT
                ),
            )

            # 終点: 正解位置
            # インベントリ内のデータに answer がある前提
            players = self.inventory.players_data
            if start_rect and players and len(players) > 0 and "answer" in players[0]:
                ans = players[0]["answer"]
                gx, gy = ans["x"], ans["y"]

                # マップ描画オフセット (PlayState.draw内で計算されている値と同じ計算が必要)
                # PlayState.draw内の変数はローカルなので再計算する
                content_off_x, content_off_y, content_w, content_h = (
                    self.tile_map.get_content_info()
                )
                play_area_width = SCREEN_WIDTH - INVENTORY_WIDTH
                play_area_height = SCREEN_HEIGHT

                center_x = (play_area_width - content_w) // 2
                center_y = (play_area_height - content_h) // 2
                map_x = center_x - content_off_x
                map_y = center_y - content_off_y

                target_x = (
                    map_x + gx * self.tile_map.tile_size + self.tile_map.tile_size // 2
                )
                target_y = (
                    map_y + gy * self.tile_map.tile_size + self.tile_map.tile_size // 2
                )

                start_x, start_y = start_rect.center

                # 現在位置の計算
                cur_x, cur_y = start_x, start_y
                if t < 1.0:
                    # 移動フェーズ (Ease-outっぽい動きにするとリッチだがまずは線形)
                    # t = 0.0 -> start, t = 1.0 -> target
                    cur_x = start_x + (target_x - start_x) * t
                    cur_y = start_y + (target_y - start_y) * t
                else:
                    # 待機フェーズ (target位置で止まる)
                    cur_x, cur_y = target_x, target_y

                # カーソル画像の描画 (左上が基準なので少しずらす？ mouse.pngのホットスポットによるが、とりあえずそのまま)
                surface.blit(self.manager.app.cursor_img, (cur_x, cur_y))

        # デモモードの配置アニメーション
        if self.is_demo and self.demo_phase == "PLACING" and self.inventory:
            if len(self.inventory.players_data) > 0:
                t = self.demo_timer / 1000.0
                if t > 1.0:
                    t = 1.0

                target_piece = self.inventory.players_data[0]
                play_area_width = SCREEN_WIDTH - INVENTORY_WIDTH
                inv_rect = pygame.Rect(
                    play_area_width, 0, INVENTORY_WIDTH, SCREEN_HEIGHT
                )
                start_rect = self.inventory.get_item_rect(0, inv_rect)

                if start_rect and "answer" in target_piece:
                    ans = target_piece["answer"]
                    # マップオフセット再計算
                    # マップオフセット再計算
                    content_off_x, content_off_y, content_w, content_h = (
                        self.tile_map.get_content_info()
                    )
                    play_area_width = SCREEN_WIDTH - INVENTORY_WIDTH
                    play_area_height = SCREEN_HEIGHT

                    center_x = (play_area_width - content_w) // 2
                    center_y = (play_area_height - content_h) // 2
                    map_x = center_x - content_off_x
                    map_y = center_y - content_off_y

                    target_x = (
                        map_x
                        + ans["x"] * self.tile_map.tile_size
                        + self.tile_map.tile_size // 2
                    )
                    target_y = (
                        map_y
                        + ans["y"] * self.tile_map.tile_size
                        + self.tile_map.tile_size // 2
                    )
                    start_x, start_y = start_rect.center

                    cur_x = start_x + (target_x - start_x) * t
                    cur_y = start_y + (target_y - start_y) * t

                    img = self.inventory.images.get(target_piece["direction"])
                    if img:
                        rect = img.get_rect(center=(cur_x, cur_y))
                        surface.blit(img, rect)

        # 結果表示オーバーレイ
        if self.result_timer > 0 and self.sim_last_result in ["WIN", "LOSE"]:
            text = "CLEAR!" if self.sim_last_result == "WIN" else "FAILED..."
            color = (255, 255, 0) if self.sim_last_result == "WIN" else (255, 0, 0)

            cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

            # 影
            shadow = self.result_font.render(text, True, COLOR_BLACK)
            sh_rect = shadow.get_rect(center=(cx + 2, cy + 2))
            surface.blit(shadow, sh_rect)

            # 本体
            surf = self.result_font.render(text, True, color)
            rect = surf.get_rect(center=(cx, cy))
            surface.blit(surf, rect)
