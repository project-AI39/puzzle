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
        # ※ユーザー指定可能にする場合は引数を増やす
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
            # 簡易的に、外周1マスを壁にするか、あるいはwidth/heightをプレイ可能エリアとするか。
            # 仕様変更が面倒なので、width/heightは「グリッドサイズ」とし、
            # ランダムに穴(NULL)をあける程度にする。
            # 今回はシンプルに「全マスNORMAL」からスタートし、少し穴をあける。

            available_cells = [(c, r) for r in range(height) for c in range(width)]

            # --- 2. ゴール配置 ---
            # プレイヤー数と同じ数のゴールが必要
            if len(available_cells) < num_players:
                continue  # 狭すぎる

            goals = random.sample(available_cells, num_players)
            for gx, gy in goals:
                map_data[gy][gx] = TILE_GOAL
                available_cells.remove((gx, gy))

            # --- 3. ギミック配置 ---
            # ワープ (ペアで配置)
            # TILE_WARP は "00800" だが、ペアごとにIDを変える必要があるなら "00801" 等にする仕様。
            # 仕様0.md: "id-00800を２つと id-00801を２つ配置することで..."
            # src/game/map.pyの読み込みロジックやSimulatorは、"008" で始まるものをワープとみなしている。
            # map.py: startswith("008")
            # simulator.py: startswith("008")
            # ペア判定: find_warp_target は "同じID" を探す。
            # なので、ペアAは "00800", ペアBは "00801" とする必要がある。

            curr_warp_id = 0
            for _ in range(num_warp_pairs):
                if len(available_cells) < 2:
                    break
                pair_pos = random.sample(available_cells, 2)
                warp_val = f"008{curr_warp_id:02d}"  # "00800", "00801"...
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
                count = solver.count_solutions(limit=2)
                if count == 1:
                    print(
                        f"Generator: Success! Attempts={attempts}, Time={time.time() - start_time:.2f}s"
                    )
                    # プレイヤーの正解位置（解）まではSolverから返していない。
                    # 必要ならSolver.count_solutionsを改造して解自体を返すようにするが、
                    # Generatorの戻り値としては「マップ」と「プレイヤー情報（向き）」があればよい。
                    # 「答え」を表示するためには、Solverが解（座標）も返すと便利。
                    # とりあえず今はマップとプレイヤー情報を返す。
                    return {"map_data": map_data, "players": players_templates}
            except Exception as e:
                print(f"Solver Error: {e}")

        return None

    def cancel(self):
        self.stop_requested = True
