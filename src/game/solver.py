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

    def count_solutions(self, limit=2):
        """
        解（クリア可能な配置パターン）の個数を数える。
        limit個見つかった時点で探索を打ち切り、limitを返す。
        """
        start_candidates = self._find_start_candidates()
        num_players = len(self.players_templates)

        if len(start_candidates) < num_players:
            return 0

        solutions_found = 0

        # 候補座標から人数分選ぶ組み合わせ (順列ではない。プレイヤーは区別しないが、
        # 実際には「配置スロット」として割り当てるため、
        # players_templates[i] の向きが固定なら「どの座標にどの向きの駒を置くか」は重要。
        # 仕様では「プレイヤーは区別なし。ただし各駒は初期方向が固定」とある。
        # ユーザーはインベントリの「上向き駒」を任意の場所に置ける。
        # つまり、(座標A, 上), (座標B, 下) と (座標A, 下), (座標B, 上) は別の配置。
        # したがって combinations ではなく permutations を考慮する必要があるか、
        # または「上向き駒x2, 下向き駒x1」のようなマルチセットの割り当てになる。
        #
        # ここでは簡易化のため、players_templates の順序が固定（例えば [UP, DOWN]）とし、
        # 選んだ座標の組み合わせに対して、それぞれの並べ替え（permutations）を試す必要がある。
        # ただし、同じ向きの駒同士は区別がないため、重複探索を避ける必要がある。
        #
        # アプローチ:
        # 1. すべての駒の向きリストを取得 (例: ['up', 'down', 'up'])
        # 2. 空きマスから人数分の座標を選ぶ (combinations)
        # 3. 選んだ座標群に対して、向きリストを割り当てる (unique permutations)
        #
        # 実装簡略化:
        # itertools.permutations(start_candidates, num_players) を使い、
        # (pos1, pos2, ...) の順に players_templates[0], [1]... を割り当てる。
        # これだと (A, B) に (UP, UP) を置くのと (B, A) に (UP, UP) を置くのが重複カウントされる可能性があるが、
        # 実際には「座標AにUP、座標BにUP」という状態は同一。
        # Permutations(candidates, k) だと (A, B) != (B, A)。
        # 割り当てが (A:UP, B:UP) と (B:UP, A:UP) で同一になる場合を除く必要がある。
        #
        # 一旦、区別ありとして permutations で探索し、初期状態の状態ハッシュ（セット）で重複チェックするのが安全。
        pass

        # とりあえず permutations で全探索し、セットで重複排除するアプローチ
        # 状態の一意性: frozenset({(x,y,dir), ...})
        seen_configs = set()

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
            # プレイヤー順序は関係なく、"盤面上に存在する駒の状態セット" が重要
            config_signature = frozenset(
                (p["grid_x"], p["grid_y"], p["piece"]["direction"])
                for p in current_config
            )

            if config_signature in seen_configs:
                continue
            seen_configs.add(config_signature)

            # シミュレーション実行
            if self._run_simulation(current_config):
                solutions_found += 1
                if solutions_found >= limit:
                    return limit

        return solutions_found

    def _find_start_candidates(self):
        """配置可能な座標（通常タイルのみ）のリストを返す"""
        candidates = []
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.map_data[r][c]
                # 配置できるのは通常タイルのみ
                # ゴール、ワープ、矢印、穴の上には初期配置不可とする（仕様確認: "ユーザーはプレイヤー駒を通常マスに配置"）
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
        # 各ステップでの全プレイヤーの状態ハッシュ
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
        # 要素: (x, y, dir, waited_on_warp)
        p_list = []
        for p in players:
            item = (
                p["grid_x"],
                p["grid_y"],
                p["piece"]["direction"],
                p.get("waited_on_warp", False),
            )
            p_list.append(item)

        # プレイヤーの並び順が変わっても同じ状態とみなすためソート
        # (衝突判定などで入れ替わりはないが、念のため集合として扱う的な意味合い)
        # ただし、Simulator内のplayersリストのインデックスはゴール判定等では関係ないが、
        # 「Aさんがゴール1、Bさんがゴール2」と「Aさんが2、Bさんが1」は区別されない（全員ゴールすればOK）。
        # 移動ロジック自体はインデックス維持。
        p_list.sort()
        return tuple(p_list)
