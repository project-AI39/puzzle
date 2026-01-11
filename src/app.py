# d:/game/puzzle/src/app.py
# メインアプリケーションクラス
# Pygameの初期化とメインループ（更新・描画）を管理する
# RELEVANT FILES: src/const.py, src/core/state_machine.py, src/states/attract.py

import pygame
import sys
from src.const import SCREEN_WIDTH, SCREEN_HEIGHT, STRING_TITLE, FPS
from src.core.state_machine import StateMachine
from src.states.attract import AttractState

# タイトル文字列は定数ファイルから取得するため削除


class GameApp:
    def __init__(self):
        # Pygameの初期化
        pygame.init()
        # フルスクリーン起動 (SCALEDで解像度維持)
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED
        )
        pygame.display.set_caption(STRING_TITLE)
        self.clock = pygame.time.Clock()
        self.state_machine = StateMachine(self)
        self.running = True

    def run(self):
        # アトラクトモードから開始
        self.state_machine.change_state(AttractState(self.state_machine))

        while self.running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                self.state_machine.handle_event(event)

            self.state_machine.update(dt)
            self.state_machine.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()
