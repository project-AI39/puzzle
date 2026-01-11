# d:/game/puzzle/src/states/confirm.py
# コンティニュー確認画面の状態
# プレイ中に長時間放置された場合に表示。ユーザーが操作すればプレイに戻るが、放置すればアトラクトに戻る。
# RELEVANT FILES: src/const.py, src/states/play.py, src/states/attract.py

import pygame
import math
from src.core.state_machine import State
from src.const import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_RED,
    CONFIRM_TIMEOUT,
    MOUSE_MOVE_THRESHOLD,
)


class ConfirmContinueState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 48)
        self.timer = 0
        self.accumulated_move = 0.0
        self.last_mouse_pos = None

    def enter(self):
        print("コンティニュー確認画面に遷移しました")
        self.timer = 0
        self.accumulated_move = 0.0
        self.last_mouse_pos = pygame.mouse.get_pos()

    def handle_event(self, event):
        # マウス移動があればプレイモードに戻る
        if event.type == pygame.MOUSEMOTION:
            current_pos = event.pos
            if self.last_mouse_pos:
                dx = current_pos[0] - self.last_mouse_pos[0]
                dy = current_pos[1] - self.last_mouse_pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                self.accumulated_move += dist

            self.last_mouse_pos = current_pos

            if self.accumulated_move > MOUSE_MOVE_THRESHOLD:
                # プレイモードへ復帰
                from src.states.play import PlayState

                self.manager.change_state(PlayState(self.manager))

    def update(self, dt):
        self.timer += dt
        if self.timer >= CONFIRM_TIMEOUT:
            from src.states.attract import AttractState

            self.manager.change_state(AttractState(self.manager))

    def draw(self, surface):
        surface.fill(COLOR_BLACK)
        text = self.font.render("CONTINUE?", True, COLOR_RED)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text, rect)

        sub = pygame.font.SysFont("Arial", 24).render(
            f"Timeout in {(CONFIRM_TIMEOUT - self.timer) // 1000}", True, COLOR_WHITE
        )
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        surface.blit(sub, sub_rect)
