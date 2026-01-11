# d:/game/puzzle/src/game/simulator.py
# ゲームシミュレータークラス
# マップとプレイヤーの移動ロジック、衝突判定、勝利/敗北判定を行う
# RELEVANT FILES: src/const.py, src/game/map.py

from src.const import (
    TILE_NORMAL,
    TILE_GOAL,
    TILE_WARP,
    TILE_UP,
    TILE_DOWN,
    TILE_RIGHT,
    TILE_LEFT,
    TILE_NULL,
    TILE_PIT,  # 奈落ID (const.pyに追加が必要)
)


class Simulator:
    def __init__(self, map_data, players_state):
        """
        Args:
            map_data: タイルIDの2次元リスト
            players_state: プレイヤーの状態リスト [{"grid_x": int, "grid_y": int, "piece": dict}, ...]
                           (TileMap.placed_pieces と同じ形式を想定)
        """
        self.map_data = map_data
        self.players = players_state
        self.status = "CONTINUE"  # CONTINUE, WIN, LOSE
        self.rows = len(map_data)
        self.cols = len(map_data[0]) if self.rows > 0 else 0

    def step(self):
        """シミュレーションを1ステップ進める"""
        if self.status != "CONTINUE":
            return self.status

        # 1. 各プレイヤーの次の位置を計算 (まだ移動させない)
        next_positions = []
        for p in self.players:
            nx, ny = self._get_next_pos(
                p["grid_x"], p["grid_y"], p["piece"]["direction"]
            )
            next_positions.append({"x": nx, "y": ny, "player": p})

        # 2. 移動先の内容確認と移動実行
        # 衝突判定のため、全員同時に移動したと仮定してチェックする

        # まず移動先に更新
        # Note: 実際にはタイル効果で移動前に向きが変わる等の仕様がある場合ここで処理
        # 仕様: "矢印: プレイヤーの向きを変更" -> 着地後に変わると解釈するか、乗った瞬間に変わるか。
        # 仕様: "ワープ: 到達すると...テレポート" -> 着地後にテレポート

        collision_detected = False
        goal_count = 0

        # 一時的に新しい座標を保存
        new_states = []

        for i, np in enumerate(next_positions):
            p = self.players[i]
            nx, ny = np["x"], np["y"]

            # マップ外判定 (奈落扱い)
            if not self._is_within_bounds(nx, ny):
                self.status = "LOSE"
                return self.status

            tile_id = self._get_tile_at(nx, ny)

            # 奈落判定
            # "00100" が奈落 (const.pyでTILE_PIT定義要)
            if tile_id == TILE_PIT:
                self.status = "LOSE"
                return self.status

            # 壁判定（無効なタイル）: 通常、ゴール、矢印、ワープ以外は壁とみなす
            # 簡易的に、NULLタイルは壁として移動しないことにする？
            # 仕様書には壁の挙動詳細がないが、「置けるマス」以外は移動不可とすると詰む。
            # ここでは「移動はできるが、不正なマスなら落ちる」あるいは「壁なら止まる」
            # 仕様書: "奈落: 00100"
            # 00200(通常), 00300(ゴール), 004~700(矢印), 00800(ワープ)
            # それ以外は？ とりあえず壁として「移動せず停止」とするか、「移動してLOSE」か。
            # 今回は "移動して、そのタイルの効果を受ける" とする。
            # タイルIDが未知なら壁として移動しない処理を入れる
            if tile_id == TILE_NULL:
                # 移動キャンセル（壁）
                nx, ny = p["grid_x"], p["grid_y"]

            # 状態更新準備
            new_states.append(
                {
                    "grid_x": nx,
                    "grid_y": ny,
                    "piece": p["piece"],  # 参照
                }
            )

        # 3. 衝突判定 (Player vs Player)
        # 同じ座標に2人以上いるか
        pos_counts = {}
        for ns in new_states:
            pos_key = (ns["grid_x"], ns["grid_y"])
            pos_counts[pos_key] = pos_counts.get(pos_key, 0) + 1

        for count in pos_counts.values():
            if count > 1:
                self.status = "LOSE"  # 衝突
                return self.status

        # 正面衝突 (Swap) 判定
        # Aが(0,0)->(0,1), Bが(0,1)->(0,0) のようなケース
        for i, ns in enumerate(new_states):
            old_p = self.players[i]
            old_pos = (old_p["grid_x"], old_p["grid_y"])
            new_pos = (ns["grid_x"], ns["grid_y"])

            # 全探索で他のプレイヤーとの入れ替わりチェック
            for j, other_ns in enumerate(new_states):
                if i == j:
                    continue
                other_old_p = self.players[j]
                other_old_pos = (other_old_p["grid_x"], other_old_p["grid_y"])
                other_new_pos = (other_ns["grid_x"], other_ns["grid_y"])

                if old_pos == other_new_pos and new_pos == other_old_pos:
                    self.status = "LOSE"  # 正面衝突
                    return self.status

        # 4. 座標確定とタイル効果適用
        for i, ns in enumerate(new_states):
            # 座標更新
            self.players[i]["grid_x"] = ns["grid_x"]
            self.players[i]["grid_y"] = ns["grid_y"]

            # タイル効果適用
            tile_id = self._get_tile_at(ns["grid_x"], ns["grid_y"])

            # ゴール判定
            if tile_id == TILE_GOAL:
                goal_count += 1

            # 矢印判定
            if tile_id == TILE_UP:
                self.players[i]["piece"]["direction"] = "up"
            elif tile_id == TILE_DOWN:
                self.players[i]["piece"]["direction"] = "down"
            elif tile_id == TILE_RIGHT:
                self.players[i]["piece"]["direction"] = "right"
            elif tile_id == TILE_LEFT:
                self.players[i]["piece"]["direction"] = "left"

            # ワープ判定
            # "008xx"
            if tile_id.startswith("008"):
                self._handle_warp(i, tile_id)

        # 5. 勝利判定
        if goal_count == len(self.players):
            self.status = "WIN"

        return self.status

    def _get_next_pos(self, x, y, direction):
        if direction == "up":
            return x, y - 1
        elif direction == "down":
            return x, y + 1
        elif direction == "left":
            return x - 1, y
        elif direction == "right":
            return x + 1, y
        return x, y

    def _is_within_bounds(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows

    def _get_tile_at(self, x, y):
        if self._is_within_bounds(x, y):
            return self.map_data[y][x]
        return TILE_NULL

    def _handle_warp(self, player_index, warp_id):
        # 同じIDを持つ別の座標を探す
        current_x = self.players[player_index]["grid_x"]
        current_y = self.players[player_index]["grid_y"]

        for r in range(self.rows):
            for c in range(self.cols):
                if (r != current_y or c != current_x) and self.map_data[r][
                    c
                ] == warp_id:
                    # ワープ先発見
                    self.players[player_index]["grid_x"] = c
                    self.players[player_index]["grid_y"] = r

                    # ワープ先に誰かいたら衝突（単純化のためここで判定してもよいが、
                    # 次のステップの衝突判定に任せるか？
                    # 仕様では「瞬時に移動」なので、移動直後に重なっていたらLOSEにすべき
                    # ここで簡易チェック
                    for i, p in enumerate(self.players):
                        if i != player_index:
                            if p["grid_x"] == c and p["grid_y"] == r:
                                self.status = "LOSE"
                    return
