"""
Player module is responsible for reading a video file from disk, display it in a window,
and enable the user to draw rectangles on the video representing bounding boxes.

"""


import cv2
import math


class Player:
    """
    Player class to load a video file, play it and enable drawing of bounding boxes.

    Parameters
    ----------
    video_path : str
        Path of the video file to be loaded. AVI is recommended for optimal performance.

    """

    def __init__(self, video_path):
        self.window = "window"
        self.window_width = 1280.0  # Width of window. Useful if loaded video dimensions exceeds screen resolution.
        self.radius = 1680  # Distance of camera view's center point from from the axis rotation
        self.max_angle = 95.0  # Degrees of rotation between beginning and end of the video
        self.frame = None  # Frame to be displayed
        self.frame_ratio = None  # Width / height ratio of the video
        self.frame_dims = (None, None)
        self.status = "stay"
        self.tracker_position = 0
        self.rectangles = []
        self.downX = None  # Mouse down coordinate
        self.downY = None  # Mouse down coordinate

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
        cv2.setTrackbarPos("Radius", self.window, 1680)

        # Set up trackbar for angle
        cv2.createTrackbar("Angle", self.window, 0, 360, self.update_angle)
        cv2.setTrackbarPos("Angle", self.window, 95)

    # Updater functions for trackbars
    def update_tracker_position(self, new_tracker_position):
        self.tracker_position = new_tracker_position

    def update_radius(self, radius):
        self.radius = radius

    def update_angle(self, angle):
        self.max_angle = angle

    def onMouseClick(self, event, x, y, flags, param):
        """
        Event handler position that records mouse down and mouse up coordinates and adds them as
        drawn bounding boxes together with the current trackbar position.

        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.downX, self.downY = x, y
        if event == cv2.EVENT_LBUTTONUP:
            self.rectangles.append(((self.downX, self.downY), (x, y), self.tracker_position))

    def get_new_position(self, old_rect_points):
        """
        Calculates current bounding bar positions from current trackbar position, original trackbar position,
        and coordinates of top left and bottom right corners.

        Parameters
        ----------
        old_rect_points : tuple
            Contains coordinates of top left corner (index 0), cooridnates of bottom right corner (index 1),
            and trackbar position when the box was srawn (index 2).

        """

        # Retrieve frame dimensions
        half_w, half_h = self.video.get(cv2.CAP_PROP_FRAME_WIDTH) / 2, self.video.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2
        half_w, half_h = self.scale_point((half_w, half_h))  # Account for resized window

        # Retrieve rectangle data
        box_w = old_rect_points[1][0] - old_rect_points[0][0]
        box_h = old_rect_points[1][1] - old_rect_points[0][1]
        old_tracker_position = old_rect_points[2]

        # Convert rackbar position to angle and calculate new angle comapred to beginning of video
        angle_old = self.max_angle * old_tracker_position / self.total_frames
        angle_new = self.max_angle * self.tracker_position / self.total_frames

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
            esc: exit

        """

        while True:
            try:
                # Jump to start when last frame is reached
                if self.tracker_position == self.total_frames:
                    self.tracker_position = 0

                # Set video to new frame
                self.video.set(cv2.CAP_PROP_POS_FRAMES, self.tracker_position)

                # Grab current frame
                frame_grab_success, self.frame = self.video.read()

                # Resize frame
                self.frame_ratio = self.window_width / self.frame.shape[1]
                self.frame_dims = (int(self.window_width), int(self.frame.shape[0] * self.frame_ratio))
                self.frame = cv2.resize(self.frame, self.frame_dims, interpolation=cv2.INTER_AREA)

                # Calculate current ractangle positions
                rectangles = [self.get_new_position(rectangle) for rectangle in self.rectangles]

                # Draw rectangles
                for rectangle in rectangles:
                    cv2.rectangle(
                        self.frame,
                        rectangle[0],
                        rectangle[1],
                        (0, 255, 255),
                        2,
                        8
                    )

                # Display grabbed image
                cv2.imshow(self.window, self.frame)

                # Change status based on key pressed
                self.status = {
                    ord("s"): "stay",
                    ord("w"): "play",
                    ord("a"): "prev_frame",
                    ord("d"): "next_frame",
                    ord("c"): "snap",
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

                # if self.status == "snap":
                #     cv2.imwrite("./" + "Snap_" + str(self.tracker_position) + ".jpg", self.frame)
                #     print("Snap of Frame", self.tracker_position, "Taken!")
                #     self.status = "stay"

                if self.status == "exit":
                    cv2.destroyWindow("image")
                    break

            except KeyError:
                print("Invalid Key was pressed")
