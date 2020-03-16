import os
import boto3
import concurrent.futures
from ffmpy import FFmpeg
from pathlib import Path


class Storage:
    def __init__(self, video_folder):
        self.videos_path = os.path.join(Path().parent.absolute(), "videos", video_folder)
        self.bucket = boto3.resource("s3").Bucket("sorterbot-training-videos")
        self.objects = [obj.key for obj in self.bucket.objects.all() if os.path.dirname(obj.key) == os.path.basename(video_folder)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.objects)) as executor:
            for obj in self.objects:
                executor.submit(self.download_and_convert_video, obj)

    def download_and_convert_video(self, obj):
        video_path = os.path.join(self.videos_path, os.path.basename(obj))
        video_path_avi = Path(video_path).with_suffix('.avi').resolve().as_posix()
        if not os.path.isfile(video_path):
            self.bucket.download_file(obj, video_path)
        if not os.path.isfile(video_path_avi):
            FFmpeg(inputs={video_path: None}, outputs={video_path_avi: "-c:v libx264"}).run()
