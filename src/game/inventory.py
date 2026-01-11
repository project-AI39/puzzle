# d:/game/puzzle/src/game/inventory.py
# インベントリ（手持ちの駒）の描画クラス
# プレイヤー画像を表示する
# RELEVANT FILES: src/const.py, src/states/play.py

import pygame
import os
from src.const import TILE_SIZE, COLOR_DARK_GRAY


class Inventory:
    def __init__(self, players_data: list[dict], img_dir="img"):
        self.players_data = players_data
        self.img_dir = img_dir
        self.images = {}
        self._load_images()
        # 描画したアイテムの矩形を保持するリスト (hit test用)
        # 要素: {"rect": pygame.Rect, "piece": dict}
        self.drawn_items = []

    def _load_images(self):
        """プレイヤー画像の読み込み"""
        # 方向ごとの画像: up, down, left, right
        # ここでは *_tile0.png を使用
        directions = ["up", "down", "left", "right"]

        for d in directions:
            filename = f"{d}player0_tile0.png"
            path = os.path.join(self.img_dir, filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if TILE_SIZE != 32:
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.images[d] = img
            else:
                print(f"Warning: Player image not found: {path}")

    def get_piece_at(self, pos: tuple[int, int]) -> dict | None:
        """指定座標にある駒を取得し、インベントリから削除して返す"""
        for item in self.drawn_items:
            if item["rect"].collidepoint(pos):
                piece = item["piece"]
                self.remove_piece(piece)
                return piece
        return None

    def add_piece(self, piece: dict):
        """駒をインベントリに追加"""
        self.players_data.append(piece)

    def remove_piece(self, piece: dict):
        """駒をインベントリから削除"""
        if piece in self.players_data:
            self.players_data.remove(piece)

    def draw(self, surface, inventory_rect: pygame.Rect):
        """インベントリの描画
        Arguments:
            inventory_rect: インベントリ全体の描画エリア
        """
        # 背景描画
        pygame.draw.rect(surface, COLOR_DARK_GRAY, inventory_rect)

        # hit test用リストをクリア
        self.drawn_items = []

        # アイテム数とタイルのサイズから全体の高さを計算
        count = len(self.players_data)
        item_spacing = 20
        total_height = (
            count * TILE_SIZE + (count - 1) * item_spacing if count > 0 else 0
        )

        # 垂直方向の中央揃えのための開始Y座標
        start_y = inventory_rect.centery - total_height // 2

        # アイテムのX座標（インベントリ領域の中央）
        item_x = inventory_rect.centerx - TILE_SIZE // 2

        current_y = start_y
        for i, player in enumerate(self.players_data):
            direction = player["direction"]
            img = self.images.get(direction)
            if img:
                surface.blit(img, (item_x, current_y))

                # 矩形を記録
                rect = pygame.Rect(item_x, current_y, TILE_SIZE, TILE_SIZE)
                self.drawn_items.append({"rect": rect, "piece": player})

                current_y += TILE_SIZE + item_spacing
