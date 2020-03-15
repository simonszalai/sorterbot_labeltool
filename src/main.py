import sys
from player import Player


class Main:
    def __init__(self):
        self.video_path = sys.argv[1]
        self.player = Player(self.video_path)
        self.player.start()


if __name__ == "__main__":
    Main()
