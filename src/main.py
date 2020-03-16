import os
import sys
from pathlib import Path
from player import Player
from storage import Storage


class Main:
    def __init__(self):
        self.dataset_id = sys.argv[1]
        self.videos_path = os.path.join(Path().parent.absolute(), "videos", self.dataset_id)

        if not os.path.isdir(self.videos_path):
            os.makedirs(self.videos_path, exist_ok=True)

        self.storage = Storage(self.videos_path)

        avi_files = [f.path for f in os.scandir(self.videos_path) if os.path.splitext(f.name)[1] == ".avi"]
        self.player = Player(avi_files[0])
        self.player.start()


if __name__ == "__main__":
    Main()
