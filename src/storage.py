"""
The storage module is responsible for handling downloads and uploads from/to Amazon S3.

"""


import os
import boto3
import concurrent.futures
from ffmpy import FFmpeg
from pathlib import Path


class Storage:
    """
    The Storage call contains methods to manage uploads and downloads.

    """

    def __init__(self):
        self.videos_bucket = boto3.resource("s3").Bucket("sorterbot-training-videos")
        self.datasets_path = os.path.join(Path().parent.absolute(), "datasets")
        self.datasets_bucket = boto3.resource("s3").Bucket("sorterbot-datasets")

    def download_videos(self, videos_path):
        """
        Lists objects in videos buckets and launches tasks to download them.

        Parameters
        ----------
        videos_path : str
            Absolute path to the folder that should contain the downloaded videos.

        """

        objects = [obj.key for obj in self.videos_bucket.objects.all() if os.path.dirname(obj.key) == os.path.basename(videos_path)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(objects)) as executor:
            for obj in objects:
                executor.submit(self.download_and_convert_video, obj, videos_path)

    def download_and_convert_video(self, obj, videos_path):
        """
        A function to be executed by ThreadPoolExecutor. It checks if the given video exists locally, if not downloads it, and then it checks if it
        was converted to .avi, and if not, converts it.

        Parameters
        ----------
        obj : object
            AWS S3 object to be downloaded.
        videos_path : str
            Absolute path to the folder where the processed videos are stored.

        """

        video_path = os.path.join(videos_path, os.path.basename(obj))
        video_path_avi = Path(video_path).with_suffix('.avi').resolve().as_posix()
        if not os.path.isfile(video_path):
            self.videos_bucket.download_file(obj, video_path)
        if not os.path.isfile(video_path_avi):
            FFmpeg(inputs={video_path: None}, outputs={video_path_avi: "-c:v libx264"}).run()

    def upload_dataset(self, dataset_path, only_json=False):
        """
        Function to upload a ready dataset (images and JSON) to the datasets bucket. It is called after the verify module was used to manually confirm 
        every image in the dataset.

        Parameters
        ----------
        dataset_path : str
            Absolute path to the dataset directory.
        only_json : bool
            Flag ti upload everything / JSON file only. Useful for development to avoid unnecessarily uploading every image in the dataset.

        """

        for root, _, files in os.walk(dataset_path):
            for file in files:
                if only_json and os.path.splitext(file)[1] != ".json":
                    continue
                dataset_type = os.path.basename(dataset_path)
                dataset_id = os.path.basename(os.path.dirname(dataset_path))
                print(file)
                print(f"{dataset_type}/{dataset_id}/{file}")
                self.datasets_bucket.upload_file(os.path.join(root, file), f"{dataset_id}/{dataset_type}/{file}")
            break  # Walk only the root directory
