import cv2
import math


class Player:
    def __init__(self, video_path):
        # Initialize variables
        self.window = "window"
        self.radius = 800
        self.max_degrees = 160.0
        self.frame = None
        self.status = "stay"
        self.tracker_position = 0
        self.rectangles = [((300, 400), (500, 600), 0)]
        self.downX = None
        self.downY = None

        # Set up Video Window
        cv2.namedWindow(self.window, flags=cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow(self.window, 250, 150)
        cv2.setMouseCallback(self.window, self.onMouseClick)

        # Create video capture object
        self.video = cv2.VideoCapture(video_path)

        # Get number of total frames
        self.total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)

        # Set up trackbar for player position
        cv2.createTrackbar("P", self.window, 0, int(self.total_frames) - 1, self.seek)
        cv2.setTrackbarPos("P", self.window, 0)

    def onMouseClick(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.downX = x
            self.downY = y
        if event == cv2.EVENT_LBUTTONUP:
            self.rectangles.append(((self.downX, self.downY), (x, y), self.tracker_position))

    def get_new_position(self, old_rect_points):
        half_w = self.video.get(cv2.CAP_PROP_FRAME_WIDTH) / 2
        half_h = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2

        old_tracker_position = old_rect_points[2]

        angle_old = self.max_degrees * old_tracker_position / self.total_frames
        angle_new = self.max_degrees * self.tracker_position / self.total_frames

        box_w = old_rect_points[1][0] - old_rect_points[0][0]
        box_h = old_rect_points[1][1] - old_rect_points[0][1]

        x_old = old_rect_points[0][0]
        y_old = old_rect_points[0][1]

        # Calculate old point coordinates in polar system
        gamma_old = math.atan((half_w - x_old) / (self.radius + half_h - y_old + 0.000001))
        gamma_old_deg = math.degrees(gamma_old)
        polar_radius = (half_w - x_old) / (math.sin(gamma_old) + 0.000001)

        # Calculate new gamma
        gamma_new_deg = gamma_old_deg - (angle_new - angle_old)
        gamma_new = math.radians(gamma_new_deg)

        # Calculate new point coordinates in Cartesian system
        x_new = half_w - math.sin(gamma_new) * polar_radius
        y_new = self.radius + half_h - (math.cos(gamma_new) * polar_radius)

        return [(int(x_new), int(y_new)), (int(x_new) + box_w, int(y_new) + box_h)]

    def seek(self, new_tracker_position):
        self.tracker_position = new_tracker_position

    def start(self):
        while True:
            try:
                # Jump to start when last frame is reached
                if self.tracker_position == self.total_frames:
                    self.tracker_position = 0

                # Set video to new frame
                self.video.set(cv2.CAP_PROP_POS_FRAMES, self.tracker_position)

                # Grab current frame
                frame_grab_success, self.frame = self.video.read()

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
                    # self.update_reactangles(self.tracker_position + 1)
                    self.tracker_position += 1
                    cv2.setTrackbarPos("P", self.window, self.tracker_position)
                    continue

                if self.status == "stay":
                    self.tracker_position = cv2.getTrackbarPos("P", self.window)

                if self.status == "exit":
                    cv2.destroyWindow("image")
                    break

                if self.status == "prev_frame":
                    # self.update_reactangles(self.tracker_position - 1)
                    self.tracker_position -= 1
                    cv2.setTrackbarPos("P", self.window, self.tracker_position)
                    self.status = "stay"

                if self.status == "next_frame":
                    # self.update_reactangles(self.tracker_position + 1)
                    self.tracker_position += 1
                    cv2.setTrackbarPos("P", self.window, self.tracker_position)
                    self.status = "stay"

                if self.status == "snap":
                    cv2.imwrite("./" + "Snap_" + str(self.tracker_position) + ".jpg", self.frame)
                    print("Snap of Frame", self.tracker_position, "Taken!")
                    self.status = "stay"

            except KeyError:
                print("Invalid Key was pressed")
