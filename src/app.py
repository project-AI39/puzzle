# d:/game/puzzle/src/app.py
# Main App Class
# Manages Pygame initialization and main loop
# RELEVANT FILES: src/const.py, src/core/state_machine.py, src/states/attract.py

import pygame
import sys
from src.const import SCREEN_WIDTH, SCREEN_HEIGHT, STRING_TITLE, FPS
from src.core.state_machine import StateMachine
from src.states.attract import AttractState

# Add a title constant if not exists, or just use string


class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(STRING_TITLE)
        self.clock = pygame.time.Clock()
        self.state_machine = StateMachine(self)
        self.running = True

    def run(self):
        # Start with Attract State
        self.state_machine.change_state(AttractState(self.state_machine))

        while self.running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.state_machine.handle_event(event)

            self.state_machine.update(dt)
            self.state_machine.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()
