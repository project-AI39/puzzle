# d:/game/puzzle/src/states/game_over.py
# ゲームオーバー画面の状態
# "GAME OVER" を表示し、指定時間後に次の状態（タイトルまたはエディタ）へ遷移する
# RELEVANT FILES: src/core/state_machine.py

import pygame
from src.core.state_machine import State
from src.const import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK


class GameOverState(State):
    def __init__(self, manager, next_state_class=None, next_state_args=None):
        super().__init__(manager)
        # 英語フォントを使用
        self.font = pygame.font.SysFont("Arial", 120, bold=True)
        self.next_state_class = next_state_class
        self.next_state_args = next_state_args if next_state_args else {}
        self.timer = 0
        self.duration = 3000  # 3秒間表示

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            if self.next_state_class:
                # 指定された次の状態へ（引数付き）
                self.manager.change_state(
                    self.next_state_class(self.manager, **self.next_state_args)
                )
            else:
                # デフォルトはアトラクトモード（タイトル）へ
                from src.states.attract import AttractState

                self.manager.change_state(AttractState(self.manager))

    def draw(self, surface):
        if self.manager.app.bg_image:
            surface.blit(self.manager.app.bg_image, (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        text = self.font.render("GAME OVER", True, (255, 0, 0))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text, rect)
