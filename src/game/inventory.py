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
        self.tile_size = TILE_SIZE  # デフォルトサイズ
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
                if self.tile_size != 32:
                    img = pygame.transform.scale(img, (self.tile_size, self.tile_size))
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

    def set_tile_size(self, new_size, max_width=None):
        """タイルサイズを変更し、画像をリロードする"""
        from src.const import INVENTORY_WIDTH

        if max_width is None:
            max_width = INVENTORY_WIDTH

        # マージンを考慮して最大サイズを制限 (左右マージン合計40pxくらいと仮定)
        limit = max_width - 40
        final_size = min(new_size, limit)
        # 下限チェック
        final_size = max(32, final_size)

        self.tile_size = final_size
        self._load_images()

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
            count * self.tile_size + (count - 1) * item_spacing if count > 0 else 0
        )

        # 垂直方向の中央揃えのための開始Y座標
        start_y = inventory_rect.centery - total_height // 2

        # アイテムのX座標（インベントリ領域の中央）
        item_x = inventory_rect.centerx - self.tile_size // 2

        current_y = start_y
        for i, player in enumerate(self.players_data):
            direction = player["direction"]
            img = self.images.get(direction)
            if img:
                surface.blit(img, (item_x, current_y))

                # 矩形を記録
                rect = pygame.Rect(item_x, current_y, self.tile_size, self.tile_size)
                self.drawn_items.append({"rect": rect, "piece": player})

                current_y += self.tile_size + item_spacing

    def get_item_rect(
        self, index: int, inventory_rect: pygame.Rect
    ) -> pygame.Rect | None:
        """指定インデックスのアイテムの矩形を取得"""
        if index < 0 or index >= len(self.players_data):
            return None

        count = len(self.players_data)
        item_spacing = 20
        total_height = (
            count * self.tile_size + (count - 1) * item_spacing if count > 0 else 0
        )

        # 垂直方向の中央揃えのための開始Y座標
        start_y = inventory_rect.centery - total_height // 2

        # アイテムのX座標（インベントリ領域の中央）
        item_x = inventory_rect.centerx - self.tile_size // 2

        current_y = start_y + index * (self.tile_size + item_spacing)

        return pygame.Rect(item_x, current_y, self.tile_size, self.tile_size)
