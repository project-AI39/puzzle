# d:/game/puzzle/src/states/attract.py
# アトラクトモード（デモ待機）の状態
# デモを表示し（現在はプレースホルダー）、ユーザーの操作を待つ
# RELEVANT FILES: src/const.py, src/core/state_machine.py

import pygame
import math
from src.core.state_machine import State
from src.const import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_GRAY,
    MOUSE_MOVE_THRESHOLD,
)


class AttractState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 48)
        self.sub_font = pygame.font.SysFont("Arial", 24)
        self.accumulated_move = 0.0  # 累積移動距離
        self.last_mouse_pos = None

    def enter(self):
        print("アトラクトモードに遷移しました")
        self.accumulated_move = 0.0
        self.last_mouse_pos = pygame.mouse.get_pos()

    def handle_event(self, event):
        # マウス移動の検知（閾値以上でタイトルへ）
        if event.type == pygame.MOUSEMOTION:
            current_pos = event.pos
            if self.last_mouse_pos:
                dx = current_pos[0] - self.last_mouse_pos[0]
                dy = current_pos[1] - self.last_mouse_pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                self.accumulated_move += dist

            self.last_mouse_pos = current_pos

            if self.accumulated_move > MOUSE_MOVE_THRESHOLD:
                from src.states.title import TitleState

                self.manager.change_state(TitleState(self.manager))

        # 'D'キーで開発者モードへ
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                from src.states.dev import DevState

                self.manager.change_state(DevState(self.manager))

    def update(self, dt):
        pass

    def draw(self, surface):
        if self.manager.app.bg_image:
            surface.blit(self.manager.app.bg_image, (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        text = self.font.render("ATTRACT MODE", True, COLOR_WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text, rect)

        sub = self.sub_font.render("Move Mouse to Start", True, COLOR_GRAY)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        surface.blit(sub, sub_rect)
