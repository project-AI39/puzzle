# d:/game/puzzle/src/game/simulator.py
# ゲームシミュレータークラス
# マップとプレイヤーの移動ロジック、衝突判定、勝利/敗北判定を行う
# RELEVANT FILES: src/const.py, src/game/map.py

from src.const import (
    TILE_GOAL,
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

        # 1. 各プレイヤーの次の位置を計算
        new_states = []

        for i, p in enumerate(self.players):
            current_x, current_y = p["grid_x"], p["grid_y"]
            current_tile = self._get_tile_at(current_x, current_y)

            # 状態更新用の一時辞書
            state_update = {
                "grid_x": current_x,
                "grid_y": current_y,
                "piece": p[
                    "piece"
                ].copy(),  # pieceも変更する可能性があるためコピー推奨 (方向転換)
                "waited_on_warp": p.get(
                    "waited_on_tile", False
                ),  # 後方互換性のため一旦 waited_on_warp キーを使うが、意味は waited_on_tile
                "just_warped": False,  # 今回のステップでワープしたか
            }

            # A. ワープ判定 (乗っていて、かつ待機済みフラグがない場合)
            if current_tile.startswith("008") and not p.get("waited_on_warp", False):
                # ワープ実行
                target_pos = self._find_warp_target(current_tile, current_x, current_y)
                if target_pos:
                    state_update["grid_x"] = target_pos[0]
                    state_update["grid_y"] = target_pos[1]
                    state_update["waited_on_warp"] = True  # ワープ先で待機状態にする
                    state_update["just_warped"] = True
                else:
                    # ワープ先が見つからない場合はその場に留まる（またはエラー？）
                    pass

            # B. 矢印判定 (乗っていて、かつ待機済みフラグがない場合)
            elif current_tile in (
                TILE_UP,
                TILE_DOWN,
                TILE_LEFT,
                TILE_RIGHT,
            ) and not p.get("waited_on_warp", False):
                # 方向転換実行 (移動はしない)
                if current_tile == TILE_UP:
                    state_update["piece"]["direction"] = "up"
                elif current_tile == TILE_DOWN:
                    state_update["piece"]["direction"] = "down"
                elif current_tile == TILE_RIGHT:
                    state_update["piece"]["direction"] = "right"
                elif current_tile == TILE_LEFT:
                    state_update["piece"]["direction"] = "left"

                state_update["waited_on_warp"] = True
                # 座標は維持

            # B. ゴール判定 (乗っていたら停止)
            elif current_tile == TILE_GOAL:
                # 移動しない
                pass

            # C. 通常移動
            else:
                nx, ny = self._get_next_pos(
                    current_x, current_y, p["piece"]["direction"]
                )

                # 範囲外なら移動許可（後にLOSE判定になる）、範囲内のみ壁判定
                if self._is_within_bounds(nx, ny):
                    # 壁判定 (NULLは壁とみなす -> 移動しない)
                    next_tile = self._get_tile_at(nx, ny)
                    if next_tile == TILE_NULL:
                        nx, ny = current_x, current_y  # 壁ドン停止

                state_update["grid_x"] = nx
                state_update["grid_y"] = ny

                # ワープなどの待機フラグは移動を試みたらリセット
                state_update["waited_on_warp"] = False

            new_states.append(state_update)

        # 2. 衝突判定 & マップ外/奈落判定
        # 判定結果を一時保存し、座標更新は必ず行う
        next_status_candidate = "CONTINUE"

        # 座標の検証 (マップ外と奈落)
        for ns in new_states:
            if not self._is_within_bounds(ns["grid_x"], ns["grid_y"]):
                next_status_candidate = "LOSE"

            tile_id = self._get_tile_at(ns["grid_x"], ns["grid_y"])
            if tile_id == TILE_PIT:
                next_status_candidate = "LOSE"

        # 衝突判定 (Player vs Player)
        # 同じ座標に2人以上いるか
        pos_counts = {}
        for ns in new_states:
            pos_key = (ns["grid_x"], ns["grid_y"])
            pos_counts[pos_key] = pos_counts.get(pos_key, 0) + 1

        for count in pos_counts.values():
            if count > 1:
                next_status_candidate = "LOSE"  # 衝突

        # 正面衝突 (Swap) 判定
        for i, ns in enumerate(new_states):
            old_p = self.players[i]
            old_pos = (old_p["grid_x"], old_p["grid_y"])
            new_pos = (ns["grid_x"], ns["grid_y"])

            for j, other_ns in enumerate(new_states):
                if i == j:
                    continue
                other_old_p = self.players[j]
                other_old_pos = (other_old_p["grid_x"], other_old_p["grid_y"])
                other_new_pos = (other_ns["grid_x"], other_ns["grid_y"])

                if old_pos == other_new_pos and new_pos == other_old_pos:
                    next_status_candidate = "LOSE"  # 正面衝突

        # 3. 座標確定とタイル効果適用
        goal_count = 0

        for i, ns in enumerate(new_states):
            # 座標更新
            self.players[i]["grid_x"] = ns["grid_x"]
            self.players[i]["grid_y"] = ns["grid_y"]
            self.players[i]["waited_on_warp"] = ns["waited_on_warp"]
            self.players[i]["piece"] = ns["piece"]  # 方向転換の適用

            # タイル効果適用
            tile_id = self._get_tile_at(ns["grid_x"], ns["grid_y"])

            # ゴール判定（勝利条件チェック用）
            if tile_id == TILE_GOAL:
                goal_count += 1

        # 4. 勝利・敗北判定の確定
        if next_status_candidate == "LOSE":
            self.status = "LOSE"
        elif goal_count == len(self.players):
            self.status = "WIN"
        else:
            self.status = "CONTINUE"

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

    def _find_warp_target(self, warp_id, current_x, current_y):
        """指定されたワープIDのペアとなる座標を探す"""
        for r in range(self.rows):
            for c in range(self.cols):
                if (r != current_y or c != current_x) and self.map_data[r][
                    c
                ] == warp_id:
                    return (c, r)
        return None
