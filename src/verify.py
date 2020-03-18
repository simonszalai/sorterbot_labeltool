import os
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
        self.verify_images()
        self.export_dataset()

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
        while True:
            if i == len(self.all_data):
                break

            img = self.all_data[i]
            key_code = self.display_image(img)

            if key_code == 43:
                # Add to dataset if the pressed key was "+" and move to next image
                self.verified_data.append(img)
                print(f"Image {i} was added to the dataset!")
                i += 1
            elif key_code == 45:
                # Remove last image from verified_data and move back to previous image
                self.verified_data.pop()
                print(f"Image {i - 1} was removed from the dataset!")
                i -= 1
            else:
                # Skip image without adding it to the dataset
                print(f"Image {i} was skipped!")
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

    def export_dataset(self):
        dataset_folder = os.path.join(self.datasets_path, "-".join(self.export_ids))
        os.makedirs(dataset_folder, exist_ok=True)

        with open(os.path.join(dataset_folder, "annotations.json"), "w") as outfile:
            json.dump(self.verified_data, outfile)

        # Copy images
        for img in self.verified_data:
            dest_path = os.path.join(dataset_folder, os.path.basename(img["file_name"]))
            copyfile(img["file_name"], dest_path)
            print(f"Successfully copied to {img['file_name']}!")


Verify().run()
