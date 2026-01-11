# d:/game/puzzle/src/core/state_machine.py
# ステートマシンのコアロジック
# 各状態の基底クラス (State) と状態遷移を管理するクラス (StateMachine) を定義
# RELEVANT FILES: src/app.py

import abc


class State(abc.ABC):
    """
    全ての状態（シーン）の基底クラス。
    各状態はこのクラスを継承し、必要なメソッドをオーバーライドする。
    """

    def __init__(self, manager):
        self.manager = manager

    def enter(self):
        """状態に入った時に呼ばれる"""
        pass

    def exit(self):
        """状態から出る時に呼ばれる"""
        pass

    def handle_event(self, event):
        """Pygameイベントを処理する"""
        pass

    def update(self, dt):
        """フレームごとの更新処理"""
        pass

    def draw(self, surface):
        """描画処理"""
        pass


class StateMachine:
    """
    現在の状態を保持し、遷移を管理するクラス。
    メインループからイベント、更新、描画の委譲を受ける。
    """

    def __init__(self, app):
        self.app = app
        self.state = None

    def change_state(self, new_state: State):
        """状態を切り替える。現在の状態のexitと新しい状態のenterを呼ぶ。"""
        if self.state:
            self.state.exit()
        self.state = new_state
        if self.state:
            self.state.enter()

    def handle_event(self, event):
        if self.state:
            self.state.handle_event(event)

    def update(self, dt):
        if self.state:
            self.state.update(dt)

    def draw(self, surface):
        if self.state:
            self.state.draw(surface)
