# d:/game/puzzle/src/game/generator.py
# マップ生成クラス
# ランダム生成 + Solver検証 (Generate-and-Test) で一意解のマップを作成する
# RELEVANT FILES: src/game/solver.py, src/const.py

import random
import time
from src.const import (
    TILE_NORMAL,
    TILE_NULL,
    TILE_GOAL,
    TILE_UP,
    TILE_DOWN,
    TILE_LEFT,
    TILE_RIGHT,
    TILE_WARP,
)
from src.game.solver import Solver


class Generator:
    def __init__(self):
        self.stop_requested = False

    def generate_map(
        self,
        width=5,
        height=5,
        num_players=1,
        num_warp_pairs=0,
        num_arrows=0,
        timeout=10.0,
    ):
        """
        パラメータに基づいてマップを生成する。
        一意解が見つかれば (map_data, players_config) を返す。
        失敗またはタイムアウトなら None を返す。
        """
        start_time = time.time()

        # プレイヤーの向きテンプレート（ランダムに決定）
        directions = ["up", "down", "left", "right"]

        # 試行ループ
        attempts = 0
        while True:
            if self.stop_requested:
                print("Generation stopped by user.")
                return None

            if time.time() - start_time > timeout:
                print("Generation timed out.")
                return None

            attempts += 1

            # --- 1. ベースマップ作成 ---
            # 外周をNULL（壁）、内部をNORMALで埋める
            map_data = [[TILE_NORMAL for _ in range(width)] for _ in range(height)]
            # 簡易的に、グリッド全体をNORMALで初期化

            available_cells = [(c, r) for r in range(height) for c in range(width)]

            # --- 2. ゴール配置 ---
            # プレイヤー数と同じ数のゴールが必要
            if len(available_cells) < num_players:
                continue

            goals = random.sample(available_cells, num_players)
            for gx, gy in goals:
                map_data[gy][gx] = TILE_GOAL
                available_cells.remove((gx, gy))

            # --- 3. ギミック配置 ---
            # ワープ (ペアで配置)
            curr_warp_id = 0
            for _ in range(num_warp_pairs):
                if len(available_cells) < 2:
                    break
                pair_pos = random.sample(available_cells, 2)
                warp_val = f"008{curr_warp_id:02d}"
                for wx, wy in pair_pos:
                    map_data[wy][wx] = warp_val
                    available_cells.remove((wx, wy))
                curr_warp_id += 1

            # 矢印
            arrow_tiles = [TILE_UP, TILE_DOWN, TILE_LEFT, TILE_RIGHT]
            for _ in range(num_arrows):
                if not available_cells:
                    break
                ax, ay = random.choice(available_cells)
                atype = random.choice(arrow_tiles)
                map_data[ay][ax] = atype
                available_cells.remove((ax, ay))

            # --- 4. プレイヤー構成決定 ---
            players_templates = []
            for _ in range(num_players):
                # 向きをランダムに
                d = random.choice(directions)
                players_templates.append({"direction": d})

            # --- 5. 検証 (Solver) ---
            solver = Solver(map_data, players_templates)

            # 解が「ちょうど1つ」かチェック
            try:
                solutions = solver.solve(limit=2)
                if len(solutions) == 1:
                    print(
                        f"Generator: Success! Attempts={attempts}, Time={time.time() - start_time:.2f}s"
                    )
                    # 解（配置情報）を含めて返す
                    return {
                        "map_data": map_data,
                        "players": players_templates,  # インベントリ用（未配置）
                        "answer": solutions[0],  # テストプレイ用（配置済み正解）
                    }
            except Exception as e:
                print(f"Solver Error: {e}")

        return None

    def cancel(self):
        self.stop_requested = True
