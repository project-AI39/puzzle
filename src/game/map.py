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
        self._load_images()

        # マップのサイズ（タイル数）
        self.rows = len(map_data)
        self.cols = len(map_data[0]) if self.rows > 0 else 0

        # マップ全体のピクセルサイズ
        self.width = self.cols * TILE_SIZE
        self.height = self.rows * TILE_SIZE

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
                # フォールバック: 単色矩形生成など（今回は省略）

    def draw(self, surface, offset_x=0, offset_y=0):
        """マップの描画"""
        for r, row in enumerate(self.map_data):
            for c, tile_id in enumerate(row):
                # タイルIDの前方一致などで柔軟にする必要があれば修正するが、
                # 現状は完全一致で辞書から取得
                # ワープIDなどは "00800", "00801" などバリエーションがあるため、
                # ここでマッピングを少し調整する必要があるかも。
                # 仕様書では "00800" がワープ。 "008xx" でバリエーション。
                # 画像は teleport0_tile.png (00800用) などがあるか確認。
                # 今回は単純化のため、ベースIDで判定するか、そのままキーとして使う。

                # ワープの場合の簡易対応: 008xx なら 00800 の画像を使うなど
                draw_id = tile_id
                if tile_id.startswith("008"):
                    draw_id = TILE_WARP  # 全て同じワープ画像を使う（仮）

                img = self.images.get(draw_id)
                if img:
                    x = offset_x + c * TILE_SIZE
                    y = offset_y + r * TILE_SIZE
                    surface.blit(img, (x, y))
