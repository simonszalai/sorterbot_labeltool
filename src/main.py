import os
import sys
from pathlib import Path
from player import Player
from storage import Storage


class Main:
    def __init__(self):
        self.storage = Storage()
        self.recording_set_id = sys.argv[1]
        self.videos_path = os.path.join(Path().parent.absolute(), "videos", self.recording_set_id)
        self.storage.download_videos(videos_path=self.videos_path)

        if not os.path.isdir(self.videos_path):
            os.makedirs(self.videos_path, exist_ok=True)

        avi_files = [f.path for f in os.scandir(self.videos_path) if os.path.splitext(f.name)[1] == ".avi"]

        for avi_file in avi_files:
            Player(avi_file, export_id=self.recording_set_id).start()


if __name__ == "__main__":
    Main()
