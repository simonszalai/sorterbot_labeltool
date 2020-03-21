import os
import sys
import cv2
import json
import random
from pathlib import Path
from shutil import copyfile
from storage import Storage


class Verify:
    def __init__(self):
        cv2.namedWindow("window", flags=cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow("window", 250, 150)

        self.storage = Storage()
        self.export_ids = sys.argv[1].split(",")
        self.datasets_path = os.path.join(Path().parent.absolute(), "datasets")
        self.verified_data = []

    def run(self):
        self.load_json()
        # self.verify_images()
        self.export_to_dataset()

    def load_json(self):
        self.all_data = []
        for export_id in self.export_ids:
            exports_path = os.path.join(Path().parent.absolute(), "exports", export_id)
            json_paths = [f.path for f in os.scandir(exports_path) if os.path.splitext(f.name)[1] == ".json"]
            for json_path in json_paths:
                with open(json_path) as json_file:
                    self.all_data += json.load(json_file)

    def verify_images(self):
        i = 0
        actions = {}
        while True:
            if i == len(self.all_data):
                break

            img = self.all_data[i]
            key_code = self.display_image(img)

            if key_code == 43:
                # Add to dataset if the pressed key was "+" and move to next image
                self.verified_data.append(img)
                actions[i] = "added"
                print(f"Image {i}/{len(self.all_data)} was added to the dataset!")
                i += 1
            elif key_code == 45:
                # Remove previous image from verified_data only if it was added
                try:
                    if actions[i - 1] == "added":
                        self.verified_data.pop()
                        print(f"Image {i - 1}/{len(self.all_data)} was removed from the dataset!")
                    else:
                        print(f"Moved back to Image {i}!")
                except KeyError:
                    print("Reached beginning of dataset!")
                    continue
                i -= 1
            else:
                # Skip image without adding it to the dataset
                print(f"Image {i}/{len(self.all_data)} was skipped!")
                actions[i] = "skipped"
                i += 1

    def display_image(self, img):
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
        key_code = cv2.waitKey(0)

        return key_code

    def export_to_dataset(self, files_already_copied=True, upload_only_json=False):
        # Construct dataset path and create folder if necessary
        dataset_folder = "-".join(self.export_ids)
        dataset_path = os.path.join(self.datasets_path, dataset_folder)
        os.makedirs(os.path.join(dataset_path, "train"), exist_ok=True)
        os.makedirs(os.path.join(dataset_path, "val"), exist_ok=True)

        if files_already_copied:
            # Get verified data from self.all_data by searching for each file already copied to dataset
            verified_data = []
            for root, _, files in os.walk(dataset_path):
                for file in files:
                    img = next((item for item in self.all_data if os.path.basename(item["file_name"]) == file), None)
                    if img is not None:
                        verified_data.append(img)
                break  # Walk only the root directory
        else:
            # Get verified data from user input
            verified_data = self.verified_data

        data = {"train": [], "val": []}
        for img in verified_data:
            # Decide about each image if it goes to train or val dataset
            set_type = "train" if 0.8 > random.random() else "val"

            # Copy image file to dataset folder (train or val subfolder)
            dest_path = os.path.join(dataset_path, set_type, os.path.basename(img["file_name"]))
            copyfile(img["file_name"], dest_path)
            print(f"Successfully copied to {img['file_name']}!")

            # Replace local file path to a relative path following this pattern: {dataset_id}/{set_type}/{image_file_name}
            img["file_name"] = os.path.join(os.path.basename(dataset_path), set_type, os.path.basename(img["file_name"]))
            data["train"].append(img) if set_type == "train" else data["val"].append(img)

        # Write annotations JSON file for train and val datasets
        for data_type in data:
            self.storage.upload_dataset(dataset_path=os.path.join(dataset_path, data_type), only_json=upload_only_json)
            with open(os.path.join(dataset_path, data_type, "annotations.json"), "w") as outfile:
                json.dump(data[data_type], outfile)

        count_kept = len(data["train"]) + len(data["val"])
        count_total = len(self.all_data)

        print(f"{count_kept} of {count_total} copied to dataset. Kept Ratio: {count_kept / count_total:.2f}%.")


Verify().run()
