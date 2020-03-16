import os
import re
import sys
import cv2
import json
from pathlib import Path
from shutil import copyfile


class Verify:
    def __init__(self):
        cv2.namedWindow("window", flags=cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow("window", 250, 150)

        self.export_ids = sys.argv[1].split(",")
        self.datasets_path = os.path.join(Path().parent.absolute(), "datasets")
        self.verified_data = []

    def run(self):
        self.load_json()
        self.display_images()
        self.export_dataset()

    def load_json(self):
        self.all_data = []
        for export_id in self.export_ids:
            json_path = os.path.join(Path().parent.absolute(), "exports", export_id, "annotations.json")
            with open(json_path) as json_file:
                self.all_data += json.load(json_file)

    def display_images(self):
        for img in self.all_data:
            # Get frame
            frame = cv2.imread(img["file_name"])
            frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)

            # Draw rectangles
            for annotation in img["annotations"]:
                bbox = [int(coord) for coord in annotation["bbox"]]
                top_left = (bbox[0], bbox[1])
                bottom_right = (bbox[2], bbox[3])
                cv2.rectangle(
                    frame,
                    top_left,
                    bottom_right,
                    (0, 255, 255),
                    2,
                    8
                )

            cv2.imshow("window", frame)
            key = cv2.waitKey(0)

            # Add to dataset if the pressed key was "+"
            if key == 43:
                self.verified_data.append(img)

    def export_dataset(self):
        os.makedirs(self.datasets_path, exist_ok=True)
        dataset_folder = self.get_dataset_folder()

        with open(os.path.join(dataset_folder, "annotations.json"), "w") as outfile:
            json.dump(self.verified_data, outfile)

        # Copy images
        for img in self.verified_data:
            dest_path = os.path.join(dataset_folder, os.path.basename(img["file_name"]))
            copyfile(img["file_name"], dest_path)
            print(f"Successfully copied to {img['file_name']}!")

    def get_dataset_folder(self):
        # List subfolders in datasets folder or create it in case it does not exist
        try:
            folder_names = [f.name for f in os.scandir(self.datasets_path) if f.is_dir()]
        except FileNotFoundError:
            folder_names = []
            os.mkdir(self.datasets_path)
            next_folder = os.path.join(self.datasets_path, "1")

        # Nauturally sort folder names
        def sorted_alphanumeric(data):
            convert = lambda text: int(text) if text.isdigit() else text.lower()
            alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
            return sorted(data, key=alphanum_key)
        folder_names = sorted_alphanumeric(folder_names)

        # Check if there are any folders in datasets and initialize a folder with number 1 if not
        try:
            next_folder = os.path.join(self.datasets_path, folder_names[-1])
        except IndexError:
            next_folder = os.path.join(self.datasets_path, "1")
            os.mkdir(next_folder)

        # Check if last folder contains any items and create new folder if it does
        if len(os.listdir(next_folder)) != 0:
            next_folder = os.path.join(self.datasets_path, str(int(folder_names[-1]) + 1))
            os.mkdir(next_folder)

        return next_folder


Verify().run()
