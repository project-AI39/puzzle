# d:/game/puzzle/src/game/map.py
# タイルマップの描画クラス
# タイルIDに基づいて画像を読み込み、マップを描画する
# RELEVANT FILES: src/const.py, src/states/play.py

import pygame
import os
from src.const import (
    TILE_SIZE,
    TILE_NULL,
    TILE_NORMAL,
    TILE_GOAL,
    TILE_UP,
    TILE_DOWN,
    TILE_RIGHT,
    TILE_LEFT,
    TILE_WARP,
)


class TileMap:
    def __init__(self, map_data: list[list[str]], img_dir="img"):
        self.map_data = map_data
        self.img_dir = img_dir
        self.images = {}
        self.player_images = {}
        self._load_images()
        self._load_player_images()

        # マップのサイズ（タイル数）
        self.rows = len(map_data)
        self.cols = len(map_data[0]) if self.rows > 0 else 0

        # マップ全体のピクセルサイズ
        self.width = self.cols * TILE_SIZE
        self.height = self.rows * TILE_SIZE

        # 配置された駒のリスト
        # 要素: {"grid_x": int, "grid_y": int, "piece": dict}
        self.placed_pieces = []

        # 描画オフセット（draw呼び出し時に更新）
        self.last_offset_x = 0
        self.last_offset_y = 0

    def _load_images(self):
        """タイル画像の読み込み"""
        # IDとファイル名の対応
        # 32x32の画像を読み込み、TILE_SIZE (64x64) にスケールする
        image_files = {
            TILE_NULL: "null_tile.png",
            TILE_NORMAL: "normal0_tile.png",
            TILE_GOAL: "goal0_tile.png",
            TILE_UP: "uparrow0_tile.png",
            TILE_DOWN: "downarrow0_tile.png",
            TILE_RIGHT: "rightarrow0_tile.png",
            TILE_LEFT: "leftarrow0_tile.png",
            TILE_WARP: "teleport0_tile.png",
        }

        for tile_id, filename in image_files.items():
            path = os.path.join(self.img_dir, filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                # スケーリング
                if TILE_SIZE != 32:
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.images[tile_id] = img
            else:
                print(f"Warning: Image not found for tile {tile_id}: {path}")

    def _load_player_images(self):
        """プレイヤー画像の読み込み（マップ描画用）"""
        directions = ["up", "down", "left", "right"]
        for d in directions:
            filename = f"{d}player0_tile0.png"
            path = os.path.join(self.img_dir, filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if TILE_SIZE != 32:
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.player_images[d] = img

    def get_grid_pos(self, screen_x, screen_y):
        """画面座標をグリッド座標に変換"""
        rel_x = screen_x - self.last_offset_x
        rel_y = screen_y - self.last_offset_y

        grid_x = rel_x // TILE_SIZE
        grid_y = rel_y // TILE_SIZE

        return grid_x, grid_y

    def is_valid_tile(self, grid_x, grid_y):
        """指定されたグリッド座標が有効な配置場所か判定"""
        if 0 <= grid_y < self.rows and 0 <= grid_x < self.cols:
            tile_id = self.map_data[grid_y][grid_x]
            # 既に駒があるかチェック（単純化のため1マス1駒）
            for p in self.placed_pieces:
                if p["grid_x"] == grid_x and p["grid_y"] == grid_y:
                    return False
            # 通常タイルのみ配置可能
            return tile_id == TILE_NORMAL
        return False

    def place_piece(self, grid_x, grid_y, piece):
        """駒を配置"""
        self.placed_pieces.append({"grid_x": grid_x, "grid_y": grid_y, "piece": piece})

    def remove_piece_at(self, grid_x, grid_y) -> dict | None:
        """指定位置の駒を削除して返す"""
        for i, p in enumerate(self.placed_pieces):
            if p["grid_x"] == grid_x and p["grid_y"] == grid_y:
                self.placed_pieces.pop(i)
                return p["piece"]
        return None

    def draw(self, surface, offset_x=0, offset_y=0):
        """マップの描画"""
        self.last_offset_x = offset_x
        self.last_offset_y = offset_y

        # タイル描画
        for r, row in enumerate(self.map_data):
            for c, tile_id in enumerate(row):
                draw_id = tile_id
                if tile_id.startswith("008"):
                    draw_id = TILE_WARP

                img = self.images.get(draw_id)
                if img:
                    x = offset_x + c * TILE_SIZE
                    y = offset_y + r * TILE_SIZE
                    surface.blit(img, (x, y))

        # 配置された駒の描画
        for p in self.placed_pieces:
            grid_x = p["grid_x"]
            grid_y = p["grid_y"]
            piece = p["piece"]

            img = self.player_images.get(piece["direction"])
            if img:
                x = offset_x + grid_x * TILE_SIZE
                y = offset_y + grid_y * TILE_SIZE
                surface.blit(img, (x, y))
