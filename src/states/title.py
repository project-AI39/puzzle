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
)


class TitleState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 64)
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
        surface.fill(COLOR_BLACK)
        text = self.font.render("TITLE SCREEN", True, COLOR_WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text, rect)
