# d:/game/puzzle/src/states/dev.py
# 開発者モードの状態
# ステージ作成やデバッグ機能を提供する（現在はプレースホルダー）
# RELEVANT FILES: src/const.py, src/core/state_machine.py

import pygame
from src.core.state_machine import State
from src.const import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BLACK,
    COLOR_BLUE,
)


class DevState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 48)

    def enter(self):
        print("開発者モードに遷移しました")

    def handle_event(self, event):
        # 'D'キーでアトラクトモードに戻る
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                from src.states.attract import AttractState

                self.manager.change_state(AttractState(self.manager))

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(COLOR_BLACK)
        text = self.font.render("DEVELOPER MODE", True, COLOR_BLUE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text, rect)
