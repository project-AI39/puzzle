import pygame
from src.core.state_machine import State
from src.const import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_WHITE


class GameClearState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.title_font = pygame.font.SysFont("Arial", 240, bold=True)
        self.msg_font = pygame.font.SysFont("Arial", 64)
        self.timer = 0
        self.duration = 5000  # 5秒表示

    def enter(self):
        print("Game Clear! Transitioning to Attract in 5s.")
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            from src.states.attract import AttractState

            self.manager.change_state(AttractState(self.manager))

    def draw(self, surface):
        if self.manager.app.bg_image:
            surface.blit(self.manager.app.bg_image, (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        # "GAME CLEAR"
        title = self.title_font.render("GAME CLEAR", True, COLOR_WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(title, title_rect)

        # "Thank you for playing!"
        msg = self.msg_font.render("Thank you for playing!", True, COLOR_WHITE)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        surface.blit(msg, msg_rect)
