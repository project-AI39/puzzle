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
)


class PlayState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 48)
        self.inactivity_timer = 0
        self.last_mouse_pos = None

    def enter(self):
        print("プレイモードに遷移しました")
        self.inactivity_timer = 0
        self.last_mouse_pos = pygame.mouse.get_pos()

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
        text = self.font.render("PLAY MODE", True, COLOR_GREEN)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text, rect)
