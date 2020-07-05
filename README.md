# SorterBot Labeltool
*Note: This repository is still work in progress!*

This repoistory contains two tools. One is a video player, which opens a video recorded by the Pi Camera, and allows the user to draw bounding boxes to it. After fine-tuning the parameters using the sliders at the bottom of the screens, the bounding box positions are automatically calculated for the rest of the frames in the whole video.

The second tool enables to user to verify every picture created by the first tool, and discard the ones that are blurry or the bounding boxes are not correctly placed.

The DeepNote notebook to train the Detectron2 network on teh created dataset can be found [here](https://beta.deepnote.com/project/c8dd74da-b3cc-415c-a801-364e8433357a).

### Usage
To start the tool, from the root folder of the repository:
1. Run 
  ```
  python3 src/main.py [DATASET_NR]
  ```
  where [DATASET_NR] is the folder name where the dataset is saved, typically an integer.
1. Set the radius and angle sliders to an approximated value. Radius represents the distance between the rotating axis of the robot’s base and the center of the camera’s field of view measured in pixels, while the angle represents the angle between the radiuses in the most counter-clockwise and the most clockwise positions measured in degrees.
1. Draw bounding boxes around items, draw bounding boxes around containers while pressing shift.
1. The following keys are available:
  | Key | Action                   |
  |-----|--------------------------|
  | w   | Play                     |
  | s   | Pause                    |
  | a   | 1 frame back             |
  | d   | 1 frame forward          |
  | e   | Export                   |
  | z   | Remove last bounding box |
  | esc | Exit                     |
1. After drawing all the bounding boxes, make sure by moving the progress slider that they align well over the whole video.
1. Using the `Export Interval` and `Export Offset` sliders, align the frame grabs indicated by white bounding boxes to the short pauses in the video, where the arm is not moving. 
1. Press `e` to export the dataset. If there are multiple videos in a dataset, the next will be automatically loaded.
1. Run 
  ```
  python3 src/verify.py [DATASET_NR]
  ```
  where [DATASET_NR] is the folder name where the dataset is saved, typically an integer.
1. This tool will display every image in the dataset with the bounding boxes. Press `+` to keep an image, press any button except `+` and `-` to skip an image, and if you erroneously added an image to the dataset, you can remove it by pressing `-`. You verify what is happening in the command line where you started the tool.
1. After you verified the dataset, it will be automatically uploaded to S3.
