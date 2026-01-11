# d:/game/puzzle/src/states/dev.py
# 開発者モードの状態
# ステージ作成やデバッグ機能を提供する
# RELEVANT FILES: src/const.py, src/core/state_machine.py, src/ui/widgets.py, src/game/generator.py, src/game/map.py

import pygame
import threading
import json
import os
import datetime
from src.core.state_machine import State
from src.ui.widgets import Button, TextInput
from src.game.generator import Generator
from src.game.map import TileMap
from src.const import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BLACK, COLOR_BLUE, COLOR_WHITE


class DevState(State):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 24)

        # UI要素の初期化 (左側パネルレイアウト)
        panel_center_x = 300  # 左側の中心X座標

        # 1. パラメータ入力欄
        self.input_label = "Params (w=5,h=5,p=1...)"
        self.params_input = TextInput(
            rect=(panel_center_x - 200, 100, 400, 40), initial_text="w=5,h=5,p=1"
        )

        # 2. 生成ボタン
        self.generate_btn = Button(
            rect=(panel_center_x - 100, 160, 200, 50),
            text="Generate Map",
            callback=self._on_generate,
        )

        # 3. 保存ボタン
        self.save_btn = Button(
            rect=(panel_center_x - 100, 240, 200, 50),
            text="Save Map",
            callback=self._on_save,
        )

        # 4. 答えをプレイボタン (Test Play -> Play Answer)
        self.play_answer_btn = Button(
            rect=(panel_center_x - 100, 320, 200, 50),
            text="Play Answer",
            callback=self._on_play_answer,
        )

        self.message = ""
        self.message_timer = 0

        # 生成関連
        self.generator = Generator()
        self.is_generating = False
        self.generated_result = None  # {"map_data": ..., "players": ..., "answer": ...}
        self.gen_thread = None
        self.preview_map = None  # TileMap instance

    def _on_generate(self):
        """生成ボタンのコールバック"""
        if self.is_generating:
            return

        params_text = self.params_input.text
        # パラメータ解析 (簡易: w=5,h=5,p=1,warp=0,arrow=0)
        kwargs = {
            "width": 5,
            "height": 5,
            "num_players": 1,
            "num_warp_pairs": 0,
            "num_arrows": 0,
        }

        try:
            parts = params_text.split(",")
            for part in parts:
                if "=" in part:
                    k, v = part.split("=")
                    k = k.strip().lower()
                    v = int(v.strip())
                    if k in ["w", "width"]:
                        kwargs["width"] = v
                    elif k in ["h", "height"]:
                        kwargs["height"] = v
                    elif k in ["p", "player", "players"]:
                        kwargs["num_players"] = v
                    elif k in ["warp", "warps"]:
                        kwargs["num_warp_pairs"] = v
                    elif k in ["arrow", "arrows"]:
                        kwargs["num_arrows"] = v
        except Exception as e:
            self._show_message(f"Param Error: {e}")
            return

        self.is_generating = True
        self._show_message("Generating... Please wait.")
        self.generated_result = None
        self.preview_map = None

        # スレッドで実行
        self.gen_thread = threading.Thread(target=self._run_generator, kwargs=kwargs)
        self.gen_thread.start()

    def _run_generator(self, **kwargs):
        """別スレッドで実行される生成処理"""
        result = self.generator.generate_map(**kwargs)
        self.generated_result = result
        self.is_generating = False

    def _on_save(self):
        """保存ボタンのコールバック"""
        if not self.generated_result:
            self._show_message("No map to save!")
            return

        try:
            save_dir = "d:/game/puzzle/create_stage"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # ファイル名生成 (stage_YYYYMMDD_HHMMSS.json)
            now = datetime.datetime.now()
            filename = f"stage_{now.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(save_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.generated_result, f, indent=2)

            print(f"Map saved to {filepath}")
            self._show_message("Map Saved Successfully!")

        except Exception as e:
            print(f"Save Error: {e}")
            self._show_message(f"Save Error: {e}")

    def _on_play_answer(self):
        """答えをプレイボタンのコールバック"""
        if not self.generated_result:
            self._show_message("No map to play!")
            return

        print("Starting Answer Play...")
        from src.states.play import PlayState

        # 生成されたマップデータを渡してPlayStateに遷移
        self.manager.change_state(
            PlayState(self.manager, stage_data=self.generated_result)
        )

    def _show_message(self, msg):
        self.message = msg
        self.message_timer = 180  # 3秒

    def enter(self):
        print("開発者モードに遷移しました")

    def handle_event(self, event):
        # UIイベント処理
        self.params_input.handle_event(event)

        if not self.is_generating:
            self.generate_btn.handle_event(event)  # 生成中はボタン無効
            self.save_btn.handle_event(event)
            self.play_answer_btn.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if not self.params_input.active:
                if event.key == pygame.K_d:
                    # 生成中なら中断リクエスト
                    if self.is_generating:
                        self.generator.cancel()

                    from src.states.attract import AttractState

                    self.manager.change_state(AttractState(self.manager))

    def update(self, dt):
        self.params_input.update(dt)

        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.message = ""

        # 生成完了・失敗検知（スレッド終了後）
        if self.gen_thread and not self.gen_thread.is_alive():
            if self.generated_result:
                if self.message == "Generating... Please wait.":
                    self._show_message("Generation Success!")

                # プレビュー作成
                if not self.preview_map:
                    self.preview_map = TileMap(self.generated_result["map_data"])
            else:
                if self.message == "Generating... Please wait.":
                    self._show_message("Generation Failed (No unique solution).")
            self.gen_thread = None

    def draw(self, surface):
        surface.fill(COLOR_BLACK)

        panel_center_x = 300

        # タイトル
        title_surf = self.font.render("DEVELOPER MODE", True, COLOR_BLUE)
        title_rect = title_surf.get_rect(center=(panel_center_x, 30))
        surface.blit(title_surf, title_rect)

        # ラベル
        label_surf = self.font.render(self.input_label, True, COLOR_WHITE)
        label_rect = label_surf.get_rect(center=(panel_center_x, 80))
        surface.blit(label_surf, label_rect)

        # UI描画
        self.params_input.draw(surface)
        self.generate_btn.draw(surface)
        self.save_btn.draw(surface)
        self.play_answer_btn.draw(surface)

        # ステータスメッセージ
        if self.message:
            color = (0, 255, 0) if "Success" in self.message else (255, 255, 255)
            if "Failed" in self.message or "Error" in self.message:
                color = (255, 0, 0)
            msg_surf = self.font.render(self.message, True, color)
            msg_rect = msg_surf.get_rect(center=(panel_center_x, 450))
            surface.blit(msg_surf, msg_rect)

        # プレビュー (右側エリア中央)
        if self.preview_map:
            # プレビューエリア：X=600 ~ 1900, Y=0 ~ 1000
            area_start_x = 600
            area_width = SCREEN_WIDTH - area_start_x

            map_w = self.preview_map.width
            map_h = self.preview_map.height

            preview_x = area_start_x + (area_width - map_w) // 2
            preview_y = (SCREEN_HEIGHT - map_h) // 2

            # 枠線
            pygame.draw.rect(
                surface,
                (50, 50, 50),
                (preview_x - 5, preview_y - 5, map_w + 10, map_h + 10),
            )

            # マップ描画
            self.preview_map.draw(surface, preview_x, preview_y)

        # 戻るガイド
        guide_surf = self.font.render(
            "Press 'D' (when not typing) to Return", True, (100, 100, 100)
        )
        guide_rect = guide_surf.get_rect(center=(panel_center_x, SCREEN_HEIGHT - 30))
        surface.blit(guide_surf, guide_rect)
