# d:/game/puzzle/src/ui/widgets.py
# UIウィジェット（ボタン、テキスト入力）の定義
# 開発者モードなどで使用する簡易的なUI要素
# RELEVANT FILES: src/states/dev.py

import pygame
from src.const import COLOR_WHITE, COLOR_BLACK, COLOR_GRAY, COLOR_DARK_GRAY


class Button:
    def __init__(
        self,
        rect,
        text,
        callback,
        font_size=24,
        bg_color=COLOR_GRAY,
        text_color=COLOR_WHITE,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.bg_color = bg_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", font_size)
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.rendered_text.get_rect(center=self.rect.center)
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface):
        # ホバー時は少し明るくするなどの演出も可
        color = (
            (
                min(self.bg_color[0] + 20, 255),
                min(self.bg_color[1] + 20, 255),
                min(self.bg_color[2] + 20, 255),
            )
            if self.hovered
            else self.bg_color
        )
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, COLOR_WHITE, self.rect, 2)  # ボーダー
        surface.blit(self.rendered_text, self.text_rect)


class TextInput:
    def __init__(
        self,
        rect,
        initial_text="",
        font_size=24,
        text_color=COLOR_WHITE,
        bg_color=COLOR_DARK_GRAY,
    ):
        self.rect = pygame.Rect(rect)
        self.text = initial_text
        self.font = pygame.font.SysFont("Arial", font_size)
        self.text_color = text_color
        self.bg_color = bg_color
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            return self.active

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                # Enterで確定動作などを入れたい場合はここでフラグ処理
                pass
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # 制御文字などは除外
                if len(event.unicode) > 0 and event.unicode.isprintable():
                    self.text += event.unicode
            return True
        return False

    def update(self, dt):
        if self.active:
            self.cursor_timer += dt
            if self.cursor_timer >= 500:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
        else:
            self.cursor_visible = False
            self.cursor_timer = 0

    def draw(self, surface):
        # 背景
        color = (
            self.bg_color
            if not self.active
            else (self.bg_color[0] + 20, self.bg_color[1] + 20, self.bg_color[2] + 20)
        )
        pygame.draw.rect(surface, color, self.rect)
        # 枠線
        border_color = COLOR_WHITE if self.active else COLOR_GRAY
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # テキスト
        rendered_text = self.font.render(self.text, True, self.text_color)
        surface.blit(rendered_text, (self.rect.x + 5, self.rect.y + 5))

        # カーソル
        if self.cursor_visible and self.active:
            cursor_x = self.rect.x + 5 + rendered_text.get_width()
            pygame.draw.line(
                surface,
                self.text_color,
                (cursor_x, self.rect.y + 5),
                (cursor_x, self.rect.y + self.rect.height - 5),
            )
