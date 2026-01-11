# d:/game/puzzle/src/game/solver.py
# パズルソルバー
# 与えられたマップとプレイヤー情報（向き）から、解（スタート位置の組み合わせ）を探索する
# RELEVANT FILES: src/game/simulator.py, src/const.py

import itertools
import copy
from src.game.simulator import Simulator
from src.const import TILE_NORMAL, TILE_GOAL, SIM_STEP_DELAY


class Solver:
    def __init__(self, map_data, players_templates, max_steps=100):
        """
        Args:
            map_data: タイルIDの2次元リスト
            players_templates: プレイヤー情報のリスト [{"direction": "up"}, ...] (座標は不要)
            max_steps: シミュレーションの最大ステップ数（無限ループ防止の保険）
        """
        self.map_data = map_data
        self.players_templates = players_templates
        self.max_steps = max_steps
        self.rows = len(map_data)
        self.cols = len(map_data[0]) if self.rows > 0 else 0

    def solve(self, limit=2):
        """
        解（クリア可能な配置パターン）を探索する。
        limit個見つかった時点で探索を打ち切り、そこまでの解リストを返す。
        Returns:
            list: 解のリスト。各要素は [{"grid_x":.., "piece":..}, ...] の形式。
        """
        start_candidates = self._find_start_candidates()
        num_players = len(self.players_templates)

        if len(start_candidates) < num_players:
            return []

        found_solutions = []

        # 状態の一意性チェック用セット
        # プレイヤーの順序に関わらず、(x,y,dir)の集合が同一なら同じ配置とみなす
        seen_configs = set()

        # 候補座標から人数分の順列を選ぶ（各駒に向きがあるため）
        for positions in itertools.permutations(start_candidates, num_players):
            # 配置を作成
            current_config = []
            for i, pos in enumerate(positions):
                p_data = {
                    "grid_x": pos[0],
                    "grid_y": pos[1],
                    "piece": {"direction": self.players_templates[i]["direction"]},
                }
                current_config.append(p_data)

            # コンフィグのハッシュ化（重複チェック）
            config_signature = frozenset(
                (p["grid_x"], p["grid_y"], p["piece"]["direction"])
                for p in current_config
            )

            if config_signature in seen_configs:
                continue
            seen_configs.add(config_signature)

            # シミュレーション実行
            if self._run_simulation(current_config):
                found_solutions.append(current_config)
                if len(found_solutions) >= limit:
                    break

        return found_solutions

    def count_solutions(self, limit=2):
        """(旧メソッド互換用) 解の個数を返す"""
        return len(self.solve(limit))

    def _find_start_candidates(self):
        """配置可能な座標（通常タイルのみ）のリストを返す"""
        candidates = []
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.map_data[r][c]
                # 配置できるのは通常タイルのみ
                if tile == TILE_NORMAL:
                    candidates.append((c, r))
        return candidates

    def _run_simulation(self, players_state):
        """
        1つの配置でシミュレーションを実行し、クリアできるか判定
        Args:
            players_state: [{"grid_x":, "grid_y":, "piece":...}, ...]
        Returns:
            bool: True if win, False otherwise
        """
        # シミュレーション用にディープコピー
        sim_players = copy.deepcopy(players_state)
        sim = Simulator(self.map_data, sim_players)

        # 状態履歴（無限ループ検知用）
        state_history = set()

        for _ in range(self.max_steps):
            # 現在の状態を記録
            current_state_hash = self._hash_state(sim.players)
            if current_state_hash in state_history:
                return False  # 無限ループ
            state_history.add(current_state_hash)

            status = sim.step()

            if status == "WIN":
                return True
            if status == "LOSE":
                return False

        return False  # ステップ切れでも失敗とみなす

    def _hash_state(self, players):
        """
        プレイヤーの状態リストをハッシュ可能な形式に変換
        順序に依存しないようにソートしてタプル化
        """
        p_list = []
        for p in players:
            item = (
                p["grid_x"],
                p["grid_y"],
                p["piece"]["direction"],
                p.get("waited_on_warp", False),
            )
            p_list.append(item)

        p_list.sort()
        return tuple(p_list)
