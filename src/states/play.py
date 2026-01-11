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
)
from src.game.loader import StageLoader
from src.game.map import TileMap
from src.game.inventory import Inventory


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

    def enter(self):
        print("プレイモードに遷移しました")
        self.inactivity_timer = 0
        self.last_mouse_pos = pygame.mouse.get_pos()
        self.held_piece = None
        self.is_dragging = False

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

            # ドラッグ判定
            if self.held_piece and not self.is_dragging:
                dx = event.pos[0] - self.drag_start_pos[0]
                dy = event.pos[1] - self.drag_start_pos[1]
                if (dx * dx + dy * dy) > self.drag_threshold**2:
                    self.is_dragging = True

        # マウスボタンダウン (掴む処理)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左クリック
                if self.held_piece:
                    # 既に掴んでいる場合は配置試行（クリック＆クリック操作の2回目）
                    self._try_place_piece(event.pos)
                else:
                    # 何も掴んでいない場合は掴む試行
                    self._try_grab_piece(event.pos)

        # マウスボタンアップ (ドラッグ＆ドロップの配置処理)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
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
        else:
            # 無効な場所なら離す（ドラッグ中ならインベントリに戻る、クリック操作なら戻る）
            # 仕様：もし配置できない場所だったらインベントリに戻す
            self.inventory.add_piece(self.held_piece)
            self.held_piece = None
            self.is_dragging = False

    def update(self, dt):
        # フレームごとに無操作タイマーを加算
        # handle_eventでリセットされない限り加算され続ける
        self.inactivity_timer += dt

        if self.inactivity_timer >= PLAY_TIMEOUT:
            from src.states.confirm import ConfirmContinueState

            self.manager.change_state(ConfirmContinueState(self.manager))

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
            self.tile_map.draw(surface, map_x, map_y)

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
