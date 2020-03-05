import cv2


def flick(x):
    pass


class Player:
    def __init__(self, video_path, onMouseClick):
        # Initialize variables
        self.window = "window"
        self.frame = None
        self.status = "stay"
        self.tracker_position = 0
        self.rectangles = []

        # Set up Video Window
        cv2.namedWindow(self.window, flags=cv2.WINDOW_GUI_NORMAL + cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow(self.window, 250, 150)
        cv2.setMouseCallback(self.window, onMouseClick)

        # Create video capture object
        self.video = cv2.VideoCapture(video_path)

        # Get number of total frames
        self.total_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)

        # Set up trackbar for player position
        cv2.createTrackbar("P", self.window, 0, int(self.total_frames) - 1, flick)
        cv2.setTrackbarPos("P", self.window, 0)

    def start(self):
        while True:
            try:
                # Jump to start when last frame is reached
                if self.tracker_position == self.total_frames - 1:
                    self.tracker_position = 0

                # Set video to new frame
                self.video.set(cv2.CAP_PROP_POS_FRAMES, self.tracker_position)

                # Grab current frame
                frame_grab_success, self.frame = self.video.read()

                # Draw rectangles
                for rectangle in self.rectangles:
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

                if self.status == "exit":
                    cv2.destroyWindow("image")
                    break

                if self.status == "prev_frame":
                    self.tracker_position -= 1
                    cv2.setTrackbarPos("P", self.window, self.tracker_position)
                    self.status = "stay"

                if self.status == "next_frame":
                    self.tracker_position += 1
                    cv2.setTrackbarPos("P", self.window, self.tracker_position)
                    self.status = "stay"

                if self.status == "snap":
                    cv2.imwrite("./" + "Snap_" + str(self.tracker_position) + ".jpg", self.frame)
                    print("Snap of Frame", self.tracker_position, "Taken!")
                    self.status = "stay"

            except KeyError:
                print("Invalid Key was pressed")
