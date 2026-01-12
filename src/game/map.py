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
    TILE_PIT,
)


class TileMap:
    def __init__(self, map_data: list[list[str]], img_dir="img"):
        self.map_data = map_data
        self.img_dir = img_dir

        # タイルサイズ (デフォルトは定数)
        self.tile_size = TILE_SIZE

        self.images = {}
        self.frame_image = None
        self.player_images = {}
        self._load_images()
        self._load_player_images()

        # マップのサイズ（タイル数）
        self.rows = len(map_data)
        self.cols = len(map_data[0]) if self.rows > 0 else 0

        # マップ全体のピクセルサイズ
        self.width = self.cols * self.tile_size
        self.height = self.rows * self.tile_size

        # 有効領域の情報 (オフセットx, オフセットy, 幅, 高さ)
        self.valid_area_offset = (0, 0)
        self.valid_area_size = (self.width, self.height)

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
            TILE_PIT: "null_tile.png",
            TILE_NORMAL: "normal0_tile.png",
            TILE_GOAL: "goal0_tile.png",
            TILE_UP: "uparrow0_tile.png",
            TILE_DOWN: "downarrow0_tile.png",
            TILE_RIGHT: "rightarrow0_tile.png",
            TILE_LEFT: "leftarrow0_tile.png",
            # TILE_WARP (00800) is base, but we load teleport0-3 explicitly
            TILE_WARP: "teleport0_tile.png",
            "00801": "teleport1_tile.png",
            "00802": "teleport2_tile.png",
            "00803": "teleport3_tile.png",
        }

        # 枠画像の読み込み
        frame_path = os.path.join(self.img_dir, "frame0.png")
        if os.path.exists(frame_path):
            img = pygame.image.load(frame_path).convert_alpha()
            if self.tile_size != 32:
                img = pygame.transform.scale(img, (self.tile_size, self.tile_size))
            self.frame_image = img

        for tile_id, filename in image_files.items():
            path = os.path.join(self.img_dir, filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.image.load(path).convert_alpha()
                # スケーリング
                if self.tile_size != 32:
                    img = pygame.transform.scale(img, (self.tile_size, self.tile_size))
                self.images[tile_id] = img
            else:
                print(f"Warning: Image not found for tile {tile_id}: {path}")

    def _load_player_images(self):
        """プレイヤー画像の読み込み（マップ描画用）"""
        self.player_images = {}  # dict[str, list[Surface]]
        directions = ["up", "down", "left", "right"]
        for d in directions:
            frames = []
            for i in range(4):
                filename = f"{d}player0_tile{i}.png"
                path = os.path.join(self.img_dir, filename)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    if self.tile_size != 32:
                        img = pygame.transform.scale(
                            img, (self.tile_size, self.tile_size)
                        )
                    frames.append(img)
                else:
                    # 最初のフレームが見つからない場合は警告、それ以外は無視（フレーム数不足許容）
                    if i == 0:
                        print(f"Warning: Player image not found: {path}")

            if frames:
                self.player_images[d] = frames

    def get_grid_pos(self, screen_x, screen_y):
        """画面座標をグリッド座標に変換"""
        rel_x = screen_x - self.last_offset_x
        rel_y = screen_y - self.last_offset_y

        grid_x = rel_x // self.tile_size
        grid_y = rel_y // self.tile_size

        return grid_x, grid_y

    def get_content_info(self):
        """有効領域の情報を返す (off_x, off_y, width, height)"""
        off_x, off_y = self.valid_area_offset
        w, h = self.valid_area_size
        return off_x, off_y, w, h

    def fit_to_area(self, max_width, max_height):
        """指定された領域に収まるようにタイルサイズを調整"""
        # 1. 有効範囲の検出 (PIT/NULL以外)
        min_c, max_c = self.cols, -1
        min_r, max_r = self.rows, -1
        has_valid_tiles = False

        for r, row in enumerate(self.map_data):
            for c, tile_id in enumerate(row):
                if tile_id != TILE_PIT and tile_id != TILE_NULL:
                    if r < min_r:
                        min_r = r
                    if r > max_r:
                        max_r = r
                    if c < min_c:
                        min_c = c
                    if c > max_c:
                        max_c = c
                    has_valid_tiles = True

        if not has_valid_tiles:
            # 有効タイルがない場合は全体を有効とする
            min_r, max_r = 0, self.rows - 1
            min_c, max_c = 0, self.cols - 1

        # 2. 有効範囲のサイズ
        content_cols = max_c - min_c + 1
        content_rows = max_r - min_r + 1

        # 3. 最適サイズの計算
        # マージンを少しとる（例えば各辺20px）
        avail_w = max_width - 40
        avail_h = max_height - 40

        if avail_w <= 0 or avail_h <= 0:
            return  # 領域が小さすぎる

        scale_x = avail_w / content_cols
        scale_y = avail_h / content_rows
        new_size = int(min(scale_x, scale_y))

        # サイズ制限
        new_size = max(32, new_size)

        # 4. 適用
        self.tile_size = new_size
        self.width = self.cols * self.tile_size
        self.height = self.rows * self.tile_size

        self.valid_area_offset = (min_c * self.tile_size, min_r * self.tile_size)
        self.valid_area_size = (
            content_cols * self.tile_size,
            content_rows * self.tile_size,
        )

        print(
            f"Resized Map: tile_size={new_size}, content=({content_cols}x{content_rows})"
        )

        # 画像リロード
        self._load_images()
        self._load_player_images()

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
                x = offset_x + c * self.tile_size
                y = offset_y + r * self.tile_size

                # ゴールやワープの下に床を描画
                if tile_id == TILE_GOAL or tile_id.startswith("008"):
                    normal_img = self.images.get(TILE_NORMAL)
                    if normal_img:
                        surface.blit(normal_img, (x, y))

                # タイル描画
                img = self.images.get(tile_id)
                if img:
                    surface.blit(img, (x, y))

                # 枠描画 (奈落以外)
                if tile_id != TILE_PIT and tile_id != TILE_NULL and self.frame_image:
                    surface.blit(self.frame_image, (x, y))

        # 配置された駒の描画
        for p in self.placed_pieces:
            grid_x = p["grid_x"]
            grid_y = p["grid_y"]
            piece = p["piece"]

            frames = self.player_images.get(piece["direction"])
            if frames and len(frames) > 0:
                # 静止中はフレーム0を表示
                img = frames[0]
                x = offset_x + grid_x * self.tile_size
                y = offset_y + grid_y * self.tile_size
                surface.blit(img, (x, y))

    def reset_pieces(self):
        """配置された駒をリセット"""
        self.placed_pieces = []
