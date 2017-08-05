import os
import settings
import pandas as pd
import numpy as np
import isodate

def listfiles(path):
    for fname in os.listdir(path):
        if os.path.isfile(os.path.join(path, fname)) and not fname.startswith('.'):
            yield fname

def get_videos():
    """gets list of videos to download."""
    path = os.path.join(settings.DATA_DIR, 'videos')
    videos = []
    for fname in listfiles(path):
        data = pd.read_csv(os.path.join(path, fname))
        videos.append(data)
    videos = pd.concat(videos, axis=0)
    return videos

def get_video_ids():
    """wrapper to get_videos that only returns an np.array of video IDs."""
    videos = get_videos()
    return videos.video_id.values

def get_speech_video_ids():
    """gets list of video ids to download, but only for video ids that are
    predicted to be speeches.

    Assume that predicted labels are in 'labels.csv' in settings.OUTPUT_DIR.
    """
    data = pd.read_csv(os.path.join(settings.OUTPUT_DIR, 'class_preds.csv'))
    data.columns = ['id', 'label']
    return data.id[data.label == 1]

def duration_str_to_num(durations):
    """converts Youtube video duration from format like "PT11M42S" to float.

    Returns np.array where each element is the duration in seconds.
    """
    durations_seconds = np.array([isodate.parse_duration(d).total_seconds() for d in durations])
    return durations_seconds
