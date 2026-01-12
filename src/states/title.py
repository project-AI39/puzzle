# d:/game/puzzle/src/states/title.py
# タイトル画面の状態
# 一定時間待機した後にプレイ画面へ遷移する
# RELEVANT FILES: src/const.py, src/core/state_machine.py

import pygame
from src.core.state_machine import State
from src.const import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BLACK,
    COLOR_WHITE,
    TITLE_WAIT_TIME,
    STRING_TITLE,
)


class TitleState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 240)  # フォントサイズ拡大
        self.timer = 0

    def enter(self):
        print("タイトル画面に遷移しました")
        self.timer = 0

    def update(self, dt):
        # 一定時間経過後にプレイモードへ
        self.timer += dt
        if self.timer >= TITLE_WAIT_TIME:
            from src.states.play import PlayState

            self.manager.change_state(PlayState(self.manager))

    def draw(self, surface):
        if self.manager.app.bg_image:
            surface.blit(self.manager.app.bg_image, (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        # タイトル文字列（影付き）
        text_str = STRING_TITLE

        # 影
        shadow = self.font.render(text_str, True, COLOR_BLACK)
        shadow_rect = shadow.get_rect(
            center=(SCREEN_WIDTH // 2 + 8, SCREEN_HEIGHT // 2 + 8)
        )
        surface.blit(shadow, shadow_rect)

        # 本体
        text = self.font.render(text_str, True, COLOR_WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text, rect)
