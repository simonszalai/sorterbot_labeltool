import cv2
import sys
from player import Player


class Main:
    def __init__(self):
        self.video_path = sys.argv[1]
        self.player = Player(self.video_path, self.onMouseClick)
        self.player.start()
        self.downX = None
        self.downY = None

    def onMouseClick(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.downX = x
            self.downY = y
            print("Coordinates on MouseDown: X: ", x, "Y: ", y)
        if event == cv2.EVENT_LBUTTONUP:
            self.player.rectangles.append(((self.downX, self.downY), (x, y)))
            print("Coordinates on MouseUp: X: ", x, "Y: ", y)


if __name__ == "__main__":
    Main()


