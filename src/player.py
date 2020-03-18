"""
Player module is responsible for reading a video file from disk, display it in a window,
and enable the user to draw rectangles on the video representing bounding boxes.

"""

import os
import cv2
import math
import json
from pathlib import Path


class Player:
    """
    Player class to load a video file, play it and enable drawing of bounding boxes.

    Parameters
    ----------
    video_path : str
        Path of the video file to be loaded. AVI is recommended for optimal performance.
    export_id : str
        Id of the current dataset which corresponds to the folder names where the videos and exported data is stored.
    window_width: float
        Width of the window. Useful if loaded video dimensions exceeds screen resolution.
    radius : int
        Distance of camera view's center point from from the axis rotation.
    max_angle : float
        Degrees of rotation between beginning and end of the video.
    export_interval : int
        Number of skipped frames between saved frames when creating the dataset.

    """

    def __init__(self, video_path, export_id, window_width=1280.0, radius=1680.0, max_angle=143.0, export_interval=18, export_offset=3):
        self.video_path = video_path
        self.window_width = window_width
        self.export_id = export_id

        # Load config JSON if it exists
        self.json_config_path = os.path.join(os.path.dirname(self.video_path), f"{os.path.basename(video_path)}_config.json")
        try:
            with open(self.json_config_path) as json_file:
                config = json.load(json_file)
                config_found = True
        except FileNotFoundError:
            config_found = False

        self.radius = config["radius"] if config_found else radius
        self.max_angle = config["max_angle"] if config_found else max_angle
        self.export_interval = config["export_interval"] if config_found else export_interval
        self.export_offset = config["export_offset"] if config_found else export_offset

        self.window = video_path
        self.status = "stay"
        self.tracker_position = 0
        self.prev_position = None
        self.rerender = False
        self.rectangles = []

        # Set up Video Window
        cv2.namedWindow(self.window, flags=cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow(self.window, 250, 150)
        cv2.setMouseCallback(self.window, self.onMouseClick)

        # Create video capture object
        self.video = cv2.VideoCapture(video_path)

        # Get number of total frames
        self.total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)

        # Set up trackbar for player position
        cv2.createTrackbar("P", self.window, 0, int(self.total_frames) - 1, self.update_tracker_position)
        cv2.setTrackbarPos("P", self.window, 0)

        # Set up trackbar for radius
        cv2.createTrackbar("Radius", self.window, 0, 5000, self.update_radius)
        cv2.setTrackbarPos("Radius", self.window, int(self.radius))

        # Set up trackbar for angle
        cv2.createTrackbar("Angle", self.window, 0, 360, self.update_angle)
        cv2.setTrackbarPos("Angle", self.window, int(self.max_angle))

        # Set up trackbar for export interval
        cv2.createTrackbar("Export Interval", self.window, 0, 100, self.update_interval)
        cv2.setTrackbarPos("Export Interval", self.window, int(self.export_interval))

        # Set up trackbar for export offset
        cv2.createTrackbar("Export Offset", self.window, 0, 100, self.update_offset)
        cv2.setTrackbarPos("Export Offset", self.window, int(self.export_offset))

    # Updater functions for trackbars
    def update_tracker_position(self, new_tracker_position):
        self.tracker_position = new_tracker_position

    def update_radius(self, radius):
        self.radius = radius
        self.rerender = True

    def update_angle(self, angle):
        self.max_angle = angle
        self.rerender = True

    def update_interval(self, export_interval):
        self.export_interval = export_interval
        self.rerender = True

    def update_offset(self, export_offset):
        self.export_offset = export_offset
        self.rerender = True

    def onMouseClick(self, event, x, y, flags, param):
        """
        Event handler position that records mouse down and mouse up coordinates and adds them as
        drawn bounding boxes together with the current trackbar position.

        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.downX, self.downY = x, y
        if event == cv2.EVENT_LBUTTONUP:
            self.rectangles.append(((self.downX, self.downY), (x, y), self.tracker_position))

        # Set flag to redraw frame after new rectangle added
        self.rerender = True

    def calc_new_rectangle_position(self, old_rect_points, tracker_position=None, scale=True):
        """
        Calculates current bounding bar positions from current trackbar position, original trackbar position,
        and coordinates of top left and bottom right corners.

        Parameters
        ----------
        old_rect_points : tuple
            Contains coordinates of top left corner (index 0), cooridnates of bottom right corner (index 1),
            and trackbar position when the box was srawn (index 2).
        tracker_position : int
            Tracker position (frame index) for which the rectangle position will be calculated.
        scale : bool
            Flag whether or not the rectangle should be scaled to match the resized window. Should be false
            for exporting since it exports full sized frames

        """

        if tracker_position is None:
            tracker_position = self.tracker_position

        # Retrieve frame dimensions
        half_w, half_h = self.video.get(cv2.CAP_PROP_FRAME_WIDTH) / 2, self.video.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2

        # Account for resized window
        if scale:
            half_w, half_h = self.scale_point((half_w, half_h))

        # Retrieve rectangle data
        box_w = old_rect_points[1][0] - old_rect_points[0][0]
        box_h = old_rect_points[1][1] - old_rect_points[0][1]
        tracker_position_when_drawn = old_rect_points[2]

        # Convert rackbar position to angle and calculate new angle comapred to beginning of video
        angle_old = self.max_angle * tracker_position_when_drawn / self.total_frames
        angle_new = self.max_angle * tracker_position / self.total_frames

        # Calculate center point of rectangle to move
        x1 = old_rect_points[0][0] + box_w / 2
        y1 = old_rect_points[0][1] + box_h / 2

        # Calculate old point coordinates in polar coordinate system
        gamma_old = math.atan((half_w - x1) / (self.radius + half_h - y1 + 0.000001))
        gamma_old_deg = math.degrees(gamma_old)
        polar_radius = (half_w - x1) / (math.sin(gamma_old) + 0.000001)

        # Calculate new gamma
        gamma_new_deg = gamma_old_deg + (angle_new - angle_old)
        gamma_new = math.radians(gamma_new_deg)

        # Calculate new center point coordinates in Cartesian coordinate system
        x2 = half_w - math.sin(gamma_new) * polar_radius
        y2 = self.radius + half_h - (math.cos(gamma_new) * polar_radius)

        # Calculate top left and bottom right corners from center, width and heigh
        return [(int(x2 - box_w / 2), int(y2 - box_h / 2)), (int(x2 + box_w / 2), int(y2 + box_h / 2))]

    def scale_point(self, point):
        """
        Function to account for the potentially resized window.

        Parameters
        ----------
        point : tuple
            Coordinates of a point to be rescaled.

        """

        x2 = point[0] * self.frame_dims[0] / self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
        y2 = point[1] * self.frame_dims[1] / self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)

        return int(x2), int(y2)

    def start(self):
        """
        This function starts video playback, calculates bounding boxes, draws them on the frame and
        allows the user to draw bounding boxes. It also watches keyboard to control playback:
            w: start playback
            s: stop playback
            a: previous frame
            d: next frame
            z: undo last rectangle draw
            esc: exit

        """

        while True:
            try:
                # Jump to start when last frame is reached
                if self.tracker_position == self.total_frames:
                    self.tracker_position = 0

                if self.rerender or self.tracker_position != self.prev_position:
                    # Set video to new frame
                    self.video.set(cv2.CAP_PROP_POS_FRAMES, self.tracker_position)

                    # Grab current frame
                    frame_grab_success, self.frame = self.video.read()

                    # Resize frame
                    self.frame_ratio = self.window_width / self.frame.shape[1]
                    self.frame_dims = (int(self.window_width), int(self.frame.shape[0] * self.frame_ratio))
                    self.frame = cv2.resize(self.frame, self.frame_dims, interpolation=cv2.INTER_AREA)

                    # Calculate current ractangle positions
                    rectangles = [self.calc_new_rectangle_position(rectangle) for rectangle in self.rectangles]

                    # Hide rectangles out of viewport bounds
                    rectangles = [rectangle for rectangle in rectangles if self.is_rect_in_bounds(rectangle, self.frame_dims)]

                    # Change color of bounding boxes when it will be exported
                    bbox_color = (255, 255, 255) if (self.export_offset + self.tracker_position) % self.export_interval == 0 else (0, 255, 255)

                    # Draw rectangles
                    for rectangle in rectangles:
                        cv2.rectangle(
                            self.frame,
                            rectangle[0],
                            rectangle[1],
                            bbox_color,
                            2,
                            8
                        )

                    # Display grabbed image
                    cv2.imshow(self.window, self.frame)

                    # Reset flag
                    self.rerender = False

                # Save position for comparison in next iteration
                self.prev_position = self.tracker_position

                # Change status based on key pressed
                self.status = {
                    ord("s"): "stay",
                    ord("w"): "play",
                    ord("a"): "prev_frame",
                    ord("d"): "next_frame",
                    ord("e"): "export",
                    ord("z"): "remove_last",
                    -1: self.status,
                    27: "exit",
                }[cv2.waitKey(10)]

                if self.status == "play":
                    self.tracker_position += 1
                    cv2.setTrackbarPos("P", self.window, self.tracker_position)
                    continue

                if self.status == "stay":
                    self.tracker_position = cv2.getTrackbarPos("P", self.window)

                if self.status == "prev_frame":
                    self.tracker_position -= 1
                    cv2.setTrackbarPos("P", self.window, self.tracker_position)
                    self.status = "stay"

                if self.status == "next_frame":
                    self.tracker_position += 1
                    cv2.setTrackbarPos("P", self.window, self.tracker_position)
                    self.status = "stay"

                if self.status == "export":
                    print("Exporting frames...")
                    exported_frames_count = self.export()
                    print(f"Successfully exported {exported_frames_count} frames!")
                    self.status = "exit"

                if self.status == "remove_last":
                    self.rectangles.pop()
                    self.status = "stay"

                if self.status == "exit":
                    cv2.destroyWindow(self.window)
                    break

            except Exception as e:
                print("Invalid Key was pressed", e)

    def is_rect_in_bounds(self, rectangle, frame_dims):
        return rectangle[0][0] > 0 and rectangle[0][1] > 0 and rectangle[1][0] < frame_dims[0] and rectangle[1][1] < frame_dims[1]

    def export(self):
        export_path = os.path.join(Path().parent.absolute(), "exports", self.export_id)
        os.makedirs(export_path, exist_ok=True)

        frame_w, frame_h = self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)

        video_name = os.path.basename(self.video_path)

        exported_frames_count = 0
        dataset_dicts = []
        for frame_index in range(int(self.total_frames)):
            if (self.export_offset + frame_index) % self.export_interval == 0:
                self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                frame_grab_success, frame = self.video.read()

                rectangles = [self.calc_new_rectangle_position(rectangle, tracker_position=frame_index) for rectangle in self.rectangles]

                # Filter out bounding boxes that are out of viewport bounds
                rectangles = [rectangle for rectangle in rectangles if self.is_rect_in_bounds(rectangle, (frame_w, frame_h))]

                # Do not export if there are no rectangles within the viewport
                if len(rectangles) == 0:
                    continue

                file_path = os.path.join(export_path, f"{video_name}_{frame_index}.jpg")

                dataset_dict = {
                    "file_name": file_path,
                    "width": frame_w,
                    "height": frame_h,
                    "image_id": f"{video_name}_{frame_index}",
                    "annotations": [{
                        "bbox": [float(rect[0][0]), float(rect[0][1]), float(rect[1][0]), float(rect[1][1])],
                        "bbox_mode": 0,
                        "category_id": 0
                    } for rect in rectangles]
                }
                dataset_dicts.append(dataset_dict)

                if frame_grab_success:
                    cv2.imwrite(file_path, frame)
                    exported_frames_count += 1
                    print(f"Successfully exported {video_name}_{frame_index}.jpg!")
                else:
                    raise Exception(f"Frame grab failed at index {frame_index} while exporting.")

        # Write dataset JSON
        with open(os.path.join(export_path, f"{video_name}.json"), "w") as outfile:
            print("Writing JSON dataset file...")
            json.dump(dataset_dicts, outfile)
            print("JSON dataset write finished!")

        # Write config JSON
        with open(self.json_config_path, "w") as outfile:
            print("Writing JSON config file...")
            config = {
                "rectangles": self.rectangles,
                "radius": self.radius,
                "max_angle": self.max_angle,
                "export_interval": self.export_interval,
                "export_offset": self.export_offset
            }
            json.dump(config, outfile)
            print("JSON config write finished!")

        return exported_frames_count
