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
    COLOR_GREEN,
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

    def enter(self):
        print("プレイモードに遷移しました")
        self.inactivity_timer = 0
        self.last_mouse_pos = pygame.mouse.get_pos()

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

        # 'D'キーで開発者モードへ
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                from src.states.dev import DevState

                self.manager.change_state(DevState(self.manager))

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
