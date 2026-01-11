# d:/game/puzzle/src/game/loader.py
# ステージデータのローダー
# JSONファイルを読み込み、辞書形式で返す
# RELEVANT FILES: src/states/play.py

import json
import os


class StageLoader:
    def __init__(self, stages_dir="stages"):
        self.stages_dir = stages_dir

    def load_stage(self, level: int) -> dict:
        """指定されたレベルのステージJSONを読み込む"""
        filename = f"{level}.json"
        path = os.path.join(self.stages_dir, filename)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Stage file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {path}: {e}")
