# d:/game/puzzle/main.py
# エントリーポイント
# GameAppをインスタンス化して実行するだけのシンプルなスクリプト
# RELEVANT FILES: src/app.py

from src.app import GameApp


def main():
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
