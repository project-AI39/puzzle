# d:/game/puzzle/src/states/attract.py
# アトラクトモード（デモ待機）の状態
# デモを表示し（現在はプレースホルダー）、ユーザーの操作を待つ
# RELEVANT FILES: src/const.py, src/core/state_machine.py

import pygame
import math
import random
import os
from src.core.state_machine import State
from src.const import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_GRAY,
    MOUSE_MOVE_THRESHOLD,
)
from src.game.loader import StageLoader
from src.states.play import PlayState


class AttractState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 48)
        self.sub_font = pygame.font.SysFont("Arial", 24)

        self.accumulated_move = 0.0  # 累積移動距離
        self.last_mouse_pos = None

        # PlayStateをサブステートとして持つ（デモ再生用）
        self.play_state = PlayState(manager)
        self.loader = StageLoader()

        self.demo_wait_timer = 0
        self.is_waiting_next = False

        # アトラクト音声
        self.attract_voice = None
        voice_path = os.path.join("sound", "遊んでね.mp3")
        if os.path.exists(voice_path):
            try:
                self.attract_voice = pygame.mixer.Sound(voice_path)
            except Exception as e:
                print(f"Error loading attract voice: {e}")

        self.voice_timer = 0

    def enter(self):
        print("アトラクトモード(Delegated to PlayState)に遷移しました")
        self.accumulated_move = 0.0
        self.last_mouse_pos = pygame.mouse.get_pos()
        self.voice_timer = 0
        self._start_new_demo()

    def _start_new_demo(self):
        """新しいステージをランダムに選んでデモ開始"""
        levels = self.loader.get_available_levels()
        if not levels:
            print("No levels found for demo.")
            return

        level = random.choice(levels)
        try:
            stage_data = self.loader.load_stage(level)

            # PlayStateにデモ設定をロードさせる
            self.play_state.setup_demo(stage_data)

            self.is_waiting_next = False
            self.demo_wait_timer = 0

            print(f"Demo started: Level {level}")

        except Exception as e:
            print(f"Error starting demo level {level}: {e}")
            self.is_waiting_next = True  # エラー時はすぐ次へ

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
        # 定期音声再生 (10秒ごと)
        if self.attract_voice:
            self.voice_timer += dt
            if self.voice_timer >= 10000:  # 10秒
                self.attract_voice.play()
                self.voice_timer = 0

        # デモ終了待ち
        if self.is_waiting_next:
            self.demo_wait_timer += dt
            if self.demo_wait_timer > 2000:  # 2秒待機
                self._start_new_demo()
            return

        # PlayStateの更新
        self.play_state.update(dt)

        # PlayStateのデモが終了したかチェック
        if self.play_state.demo_phase == "DONE":
            self.is_waiting_next = True
            self.demo_wait_timer = 0

    def draw(self, surface):
        if self.manager.app.bg_image:
            surface.blit(self.manager.app.bg_image, (0, 0))
        else:
            surface.fill(COLOR_BLACK)

        # PlayStateに描画させる
        self.play_state.draw(surface)

        # "DEMO PLAY" 表示 (PlayStateの上に重ねる)
        text = self.font.render("DEMO PLAY", True, COLOR_WHITE)
        rect = text.get_rect(topleft=(20, 20))
        surface.blit(text, rect)

        sub = self.sub_font.render("Move Mouse to Start", True, COLOR_GRAY)
        sub_rect = sub.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        surface.blit(sub, sub_rect)
