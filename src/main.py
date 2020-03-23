import os
import sys
from pathlib import Path
from player import Player
from storage import Storage


storage = Storage()
recording_set_id = sys.argv[1]
videos_path = os.path.join(Path().parent.absolute(), "videos", recording_set_id)
storage.download_videos(videos_path=videos_path)

if not os.path.isdir(videos_path):
    os.makedirs(videos_path, exist_ok=True)

avi_files = [f.path for f in os.scandir(videos_path) if os.path.splitext(f.name)[1] == ".avi"]

for avi_file in avi_files:
    Player(avi_file, export_id=recording_set_id).start()
