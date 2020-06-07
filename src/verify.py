"""
The Verify module provides a way to manually verify every picture in the dataset. When a higher-end robotic arm is used which is capable of very accurate and
consistent movement, this module might not be needed, but for a low-end arm, driven with servos, a relatively high number of images might end up blurred
or the objects out of their bounding boxes due to inconsistent movements of the arm. To avoid these ending up in the final dataset, this module is used.
It can process multiple export folders at once. The IDs for these folders has to be provided at startup. After all the files in these folder are read in,
a UI will appear showing the first picture and the generated bounding boxes over the objects. If the picture looks alright, press Num+, and it will be added
to the dataset. If a picture was added by mistake, press Num-, and the last picture will be removed and show again to revise the decision. If any other key
is pressed (Num Enter conveniently), the current picture is skipped and the next one is shown. After every picture has been added or skipped, the images
will be copied to the dataset folder (divided into train and validation set) and one JSON file will be created for the training and validation sets.
At the end of the process, the generated dataset will be uploaded to the datasets S3 bucket.

"""

import os
import sys
import cv2
import json
import random
from pathlib import Path
from shutil import copyfile
from storage import Storage


class Verify:
    """
    Verify class to contain functions which verify and combine multiple exports into one dataset.

    """

    def __init__(self):
        cv2.namedWindow("window", flags=cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow("window", 250, 50)

        self.storage = Storage()
        self.export_ids = sys.argv[1].split(",")
        self.datasets_path = os.path.join(Path().parent.absolute(), "datasets")
        self.verified_data = []

    def run(self, manual_verification=True):
        """
        Function to run the verification process.

        Parameters
        ----------
        manual_verification : bool
            Flag to manually verify images or just generate JSON and upload it from previosly verified images that
            were already copied to the dataset folder.

        """

        self.load_json()
        if manual_verification:
            self.verify_images()
        self.export_to_dataset(manual_verification=manual_verification)

    def load_json(self):
        """
        Function that loads every JSON file in the specified exports folders and loads the data stored in them.

        """

        self.all_data = []
        for export_id in self.export_ids:
            exports_path = os.path.join(Path().parent.absolute(), "exports", export_id)
            json_paths = [f.path for f in os.scandir(exports_path) if os.path.splitext(f.name)[1] == ".json"]
            for json_path in json_paths:
                with open(json_path) as json_file:
                    self.all_data += json.load(json_file)

    def verify_images(self):
        """
        Function that loops through the images from the loaded JSON files, shows them on the screen one by one, and based on the user input,
        saves them to the dataset or skips them.

        """

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
        """
        Shows the provided image on screen and draws the bounding boxes on it.

        Parameters
        ----------
        img : object
            Img object from the loaded JSON file. Contains the full path to the image under "file_name" key and
            the annotations including bounding boxes under "annotations" key.

        Returns
        -------
        key_code : int
            Code of the pressed key.

        """

        # Get frame
        frame = cv2.imread(img["file_name"])
        frame_ratio = frame.shape[0] / frame.shape[1]
        resized_frame_dims = (1280, int(frame.shape[0] * frame_ratio))

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

        frame = cv2.resize(frame, resized_frame_dims, interpolation=cv2.INTER_AREA)

        cv2.imshow("window", frame)
        key_code = cv2.waitKey(0)

        return key_code

    def export_to_dataset(self, manual_verification, train_ratio=0.8):
        """
        A function that aggregates images from one more more exports into a single dataset. There ware 2 ways to get which images from an export should be kept:
        From user input or from images already copied to the dataset folder. The second way is useful for development, when clicking though the images one by one
        is better avoided. The "file_name" for every image are updated to relative paths, they are devided into train and validation sets, copied to the dataset
        folder and finally uploaded to S3.

        Parameters
        ----------
        manual_verification : bool
            Flag to enable manual verification. Disabling it results in loading data from images copied to dataset folder. Useful for development.
        train_ratio : float
            Defines the proportion of the train and validation sets. E.g.: train_ratio=0.8 ==> ~80% of images to train set, ~20% to validation set.

        """

        # Construct dataset path and create folder if necessary
        dataset_folder = "-".join(self.export_ids)
        dataset_path = os.path.join(self.datasets_path, dataset_folder)
        os.makedirs(os.path.join(dataset_path, "train"), exist_ok=True)
        os.makedirs(os.path.join(dataset_path, "val"), exist_ok=True)

        if not manual_verification:
            # Instead of user input, get verified data from self.all_data by searching for each file already copied to dataset
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
            set_type = "train" if train_ratio > random.random() else "val"

            # Copy image file to dataset folder (train or val subfolder)
            dest_path = os.path.join(dataset_path, set_type, os.path.basename(img["file_name"]))
            copyfile(img["file_name"], dest_path)
            print(f"Successfully copied to {img['file_name']}!")

            # Replace local file path to a relative path following this pattern: {dataset_id}/{set_type}/{image_file_name}
            img["file_name"] = os.path.join(os.path.basename(dataset_path), set_type, os.path.basename(img["file_name"]))
            data["train"].append(img) if set_type == "train" else data["val"].append(img)

        # Write annotations JSON file for train and val datasets and upload dataset
        for data_type in data:
            self.storage.upload_dataset(dataset_path=os.path.join(dataset_path, data_type), only_json=not manual_verification)
            with open(os.path.join(dataset_path, data_type, "annotations.json"), "w") as outfile:
                json.dump(data[data_type], outfile)

        count_kept = len(data["train"]) + len(data["val"])
        count_total = len(self.all_data)

        print(f"{count_kept} of {count_total} copied to dataset. Kept Ratio: {count_kept / count_total:.2f}.")


Verify().run()
