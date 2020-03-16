import os
import sys
import cv2
import json
from pathlib import Path
from player import Player
from storage import Storage


cv2.namedWindow("window", flags=cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
cv2.moveWindow("window", 250, 150)


dataset_ids = sys.argv[1].split(",")

# Load JSON files
all_data = []
for dataset_id in dataset_ids:
    json_path = os.path.join(Path().parent.absolute(), "exports", dataset_id, "annotations.json")
    with open(json_path) as json_file:
        all_data += json.load(json_file)

i = 0
while i < len(all_data):



