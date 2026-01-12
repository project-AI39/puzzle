import pygame
import json
import os
import datetime
import tkinter as tk
from tkinter import filedialog
from src.core.state_machine import State
from src.ui.widgets import Button
from src.game.map import TileMap
from src.const import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_GREEN,
    TILE_NORMAL,
    TILE_GOAL,
    TILE_PIT,
    TILE_WARP,
    TILE_UP,
    TILE_DOWN,
    TILE_LEFT,
    TILE_RIGHT,
    TILE_SIZE,
)


class DevState(State):
    def __init__(self, manager, initial_data=None):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 32)
        self.small_font = pygame.font.SysFont("Arial", 24)

        # UIレイアウト
        self.panel_width = 500
        center_x = self.panel_width // 2

        # --- ボタン定義 ---

        # 1. 操作系
        self.clear_btn = Button(
            rect=(center_x - 100, 50, 200, 40),
            text="Clear Map",
            callback=self._on_clear,
        )
        self.save_btn = Button(
            rect=(center_x - 100, 110, 200, 40),
            text="Save JSON",
            callback=self._on_save,
        )
        self.load_btn = Button(
            rect=(center_x - 100, 170, 200, 40),
            text="Load JSON",
            callback=self._on_load,
        )
        self.test_play_btn = Button(
            rect=(center_x - 100, 230, 200, 40),
            text="Test Play",
            callback=self._on_test_play,
        )

        # 2. ブラシ選択 (パレット)
        self.brushes = [
            {"label": "Floor", "value": TILE_NORMAL, "type": "tile"},
            {"label": "Goal", "value": TILE_GOAL, "type": "tile"},
            {"label": "Pit", "value": TILE_PIT, "type": "tile"},
            {"label": "Arrow U", "value": TILE_UP, "type": "tile"},
            {"label": "Arrow D", "value": TILE_DOWN, "type": "tile"},
            {"label": "Arrow L", "value": TILE_LEFT, "type": "tile"},
            {"label": "Arrow R", "value": TILE_RIGHT, "type": "tile"},
            {"label": "Warp 0", "value": TILE_WARP, "type": "tile"},
            {"label": "Warp 1", "value": "00801", "type": "tile"},
            {"label": "Warp 2", "value": "00802", "type": "tile"},
            {"label": "Warp 3", "value": "00803", "type": "tile"},
            {"label": "Player U", "value": "up", "type": "player"},
            {"label": "Player D", "value": "down", "type": "player"},
            {"label": "Player L", "value": "left", "type": "player"},
            {"label": "Player R", "value": "right", "type": "player"},
        ]

        # パレット設定
        self.palette_start_x = 30
        self.palette_start_y = 300
        self.palette_tile_size = 48  # 表示サイズ
        self.palette_cols = 8  # 1行あたりの数
        self.palette_margin = 10

        self.current_brush = self.brushes[0]

        # マッセージ
        self.message = "Map Editor: Paint tiles freely."
        self.message_timer = 0

        # マップデータ管理
        self.map_width = 15
        self.map_height = 10

        if initial_data:
            print("Restoring Map Data...")
            self.map_data = initial_data["map_data"]
            self.placed_players = []
            if "players" in initial_data:
                for p in initial_data["players"]:
                    if "answer" in p:
                        self.placed_players.append(
                            {
                                "grid_x": p["answer"]["x"],
                                "grid_y": p["answer"]["y"],
                                "direction": p["direction"],
                            }
                        )
        else:
            self.map_data = [
                [TILE_PIT for _ in range(self.map_width)]
                for _ in range(self.map_height)
            ]
            self.placed_players = []

        # TileMapインスタンス
        self.tile_map = TileMap(self.map_data)
        self._refresh_tile_map()

    def _set_brush(self, brush):
        self.current_brush = brush
        self.message = f"Brush: {brush['label']}"

    def _on_clear(self):
        self.map_data = [
            [TILE_PIT for _ in range(self.map_width)] for _ in range(self.map_height)
        ]
        self.placed_players = []
        self._refresh_tile_map()
        self.message = "Map Cleared."

    def _refresh_tile_map(self):
        """TileMapの再生成"""
        self.tile_map = TileMap(self.map_data)
        self.tile_map.placed_pieces = []
        for p in self.placed_players:
            self.tile_map.place_piece(
                p["grid_x"], p["grid_y"], {"direction": p["direction"]}
            )

    def _on_save(self):
        try:
            save_dir = "create_stage"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            now = datetime.datetime.now()
            filename = f"stage_{now.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(save_dir, filename)

            # playersリストにanswer情報を含める(1.json形式)
            players_export = []
            for p in self.placed_players:
                players_export.append(
                    {
                        "direction": p["direction"],
                        "answer": {"x": p["grid_x"], "y": p["grid_y"]},
                    }
                )

            data = {
                "map_data": self.map_data,
                "players": players_export,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.message = "Map Saved!"
        except Exception as e:
            print(e)
            self.message = "Save Error."

    def _on_load(self):
        try:
            # 隠しウィンドウの作成（rootウィンドウを出さないため）
            root = tk.Tk()
            root.withdraw()

            # ファイルダイアログ表示
            filepath = filedialog.askopenfilename(
                title="Select Map File",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                initialdir="create_stage",  # デフォルトディレクトリ
            )
            root.destroy()  # ウィンドウ破棄

            if filepath:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # マップデータ反映
                self.map_data = data["map_data"]

                # プレイヤーデータ反映
                self.placed_players = []
                if "players" in data:
                    for p in data["players"]:
                        # 新形式: playersリスト内の各要素に answer がある
                        if "answer" in p:
                            self.placed_players.append(
                                {
                                    "grid_x": p["answer"]["x"],
                                    "grid_y": p["answer"]["y"],
                                    "direction": p["direction"],
                                }
                            )

                # タイルマップ再描画
                self._refresh_tile_map()
                self.message = f"Loaded: {os.path.basename(filepath)}"

        except Exception as e:
            print(f"Load Error: {e}")
            self.message = "Load Error."

    def _on_test_play(self):
        if not self.placed_players:
            self.message = "No players placed!"
            return

        players_export = []
        for p in self.placed_players:
            players_export.append(
                {
                    "direction": p["direction"],
                    "answer": {"x": p["grid_x"], "y": p["grid_y"]},
                }
            )

        # テストプレイ用データ
        # PlayStateが「初期配置済み」と認識するように answer キーを入れる
        answer_export = []
        for p in self.placed_players:
            answer_export.append(
                {
                    "grid_x": p["grid_x"],
                    "grid_y": p["grid_y"],
                    "piece": {"direction": p["direction"]},
                }
            )

        stage_data = {
            "map_data": self.map_data,
            "players": players_export,
            "answer": answer_export,
            # auto_play: True にすると自動再生になるが、ここは配置済みからの手動プレイ
        }

        print("Starting Test Play...")
        from src.states.play import PlayState

        self.manager.change_state(PlayState(self.manager, stage_data=stage_data))

    def enter(self):
        print("Dev Mode Entered")
        pygame.key.set_repeat(200, 50)

    def leave(self):
        pygame.key.set_repeat()

    def handle_event(self, event):
        self.clear_btn.handle_event(event)
        self.save_btn.handle_event(event)
        self.load_btn.handle_event(event)
        self.test_play_btn.handle_event(event)

        # パレットクリック処理
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if mx < self.panel_width:
                # パレットエリア判定
                for i, brush in enumerate(self.brushes):
                    r = i // self.palette_cols
                    c = i % self.palette_cols

                    x = self.palette_start_x + c * (
                        self.palette_tile_size + self.palette_margin
                    )
                    y = self.palette_start_y + r * (
                        self.palette_tile_size + self.palette_margin
                    )

                    rect = pygame.Rect(
                        x, y, self.palette_tile_size, self.palette_tile_size
                    )
                    if rect.collidepoint(mx, my):
                        self._set_brush(brush)
                        break

        # マップクリック処理 (ペイント機能)
        is_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        is_drag = event.type == pygame.MOUSEMOTION and event.buttons[0]

        if is_click or is_drag:
            mx, my = event.pos
            # マップエリア内か判定 (右側)
            if mx > self.panel_width:
                # オフセットをここで計算して使用する (TileMap内部状態への依存を排除)
                area_w = SCREEN_WIDTH - self.panel_width
                map_pixel_w = self.tile_map.width
                map_pixel_h = self.tile_map.height

                offset_x = self.panel_width + (area_w - map_pixel_w) // 2
                offset_y = (SCREEN_HEIGHT - map_pixel_h) // 2

                # 座標変換
                gx = (mx - offset_x) // TILE_SIZE
                gy = (my - offset_y) // TILE_SIZE

                if 0 <= gx < self.map_width and 0 <= gy < self.map_height:
                    # 左クリック(1)として処理
                    self._apply_brush(gx, gy, 1)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                from src.states.attract import AttractState

                self.manager.change_state(AttractState(self.manager))

    def _apply_brush(self, gx, gy, button):
        if button != 1:
            return

        tile_changed = False

        if self.current_brush["type"] == "tile":
            current_val = self.map_data[gy][gx]
            new_val = self.current_brush["value"]

            if current_val != new_val:
                self.map_data[gy][gx] = new_val
                # タイルが変わったらその上のプレイヤー削除 (Wall/Pit/Loop対策など、基本は置いたタイルの整合性を取る)
                # 特にNULL/PITにした場合はプレイヤー落とす
                if new_val == TILE_PIT:
                    self.placed_players = [
                        p
                        for p in self.placed_players
                        if not (p["grid_x"] == gx and p["grid_y"] == gy)
                    ]
                tile_changed = True

        elif self.current_brush["type"] == "player":
            direction = self.current_brush["value"]

            # 既に同じ場所に同じ向きのプレイヤーがいれば何もしない（無駄な更新防止）
            existing = [
                p
                for p in self.placed_players
                if p["grid_x"] == gx and p["grid_y"] == gy
            ]
            if existing:  # 既に誰かいる
                # 向き更新なら実行
                if existing[0]["direction"] != direction:
                    existing[0]["direction"] = direction
                    tile_changed = True
            else:
                # 追加
                self.placed_players.append(
                    {"grid_x": gx, "grid_y": gy, "direction": direction}
                )
                # その下のタイルをNormalにする
                if self.map_data[gy][gx] == TILE_PIT:
                    self.map_data[gy][gx] = TILE_NORMAL
                tile_changed = True

        if tile_changed:
            self._refresh_tile_map()

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.message = ""

    def draw(self, surface):
        if self.manager.app.bg_image:
            surface.blit(self.manager.app.bg_image, (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        # パネル背景
        pygame.draw.rect(surface, (30, 30, 30), (0, 0, self.panel_width, SCREEN_HEIGHT))

        self.clear_btn.draw(surface)
        self.save_btn.draw(surface)
        self.load_btn.draw(surface)
        self.test_play_btn.draw(surface)

        # ブラシパレットラベル
        brush_label = self.font.render(
            f"Palette: {self.current_brush['label']}", True, COLOR_GREEN
        )
        surface.blit(brush_label, (20, 210))

        # 画像パレット描画
        for i, brush in enumerate(self.brushes):
            r = i // self.palette_cols
            c = i % self.palette_cols

            x = self.palette_start_x + c * (
                self.palette_tile_size + self.palette_margin
            )
            y = self.palette_start_y + r * (
                self.palette_tile_size + self.palette_margin
            )
            rect = pygame.Rect(x, y, self.palette_tile_size, self.palette_tile_size)

            # 枠線 (選択中なら赤、それ以外は白)
            if self.current_brush == brush:
                pygame.draw.rect(surface, (255, 0, 0), rect.inflate(6, 6), 3)
            else:
                pygame.draw.rect(surface, (100, 100, 100), rect, 1)

            # 画像取得・描画
            img = None
            if brush["type"] == "tile":
                val = brush["value"]
                if val in self.tile_map.images:
                    img = self.tile_map.images[val]
            elif brush["type"] == "player":
                val = brush["value"]
                if val in self.tile_map.player_images:
                    frames = self.tile_map.player_images[val]
                    if frames:
                        img = frames[0]

            if img:
                # パレットサイズに合わせてスケール
                scaled_img = pygame.transform.scale(
                    img, (self.palette_tile_size, self.palette_tile_size)
                )
                surface.blit(scaled_img, rect)

        # メッセージ
        msg_surf = self.font.render(self.message, True, COLOR_WHITE)
        surface.blit(msg_surf, (20, SCREEN_HEIGHT - 50))

        # マップ描画
        area_w = SCREEN_WIDTH - self.panel_width
        map_pixel_w = self.tile_map.width
        map_pixel_h = self.tile_map.height

        offset_x = self.panel_width + (area_w - map_pixel_w) // 2
        offset_y = (SCREEN_HEIGHT - map_pixel_h) // 2

        pygame.draw.rect(
            surface,
            (50, 50, 50),
            (offset_x - 5, offset_y - 5, map_pixel_w + 10, map_pixel_h + 10),
        )

        self.tile_map.draw(surface, offset_x, offset_y)

        guide = self.small_font.render("Press 'D' to Quit", True, (100, 100, 100))
        surface.blit(guide, (20, SCREEN_HEIGHT - 20))
