"""Downloads Youtube videos.

Currently, downloads all videos whose IDs are stored in a CSV in data/videos,
with no option for subsetting the set of downloaded videos.
"""

import os
import sys
from pytube import YouTube
from pprint import pprint
import pandas as pd
import numpy as np
import settings

def listfiles(path):
    for fname in os.listdir(path):
        if os.path.isfile(os.path.join(path, fname)) and not fname.startswith('.'):
            yield fname

# gets list of video IDs to download.
path = os.path.join(settings.DATA_DIR, 'videos')
video_ids = []
for fname in listfiles(path):
    data = pd.read_csv(os.path.join(path, fname))
    video_ids.append(data.video_id.values)
video_ids = np.hstack(video_ids)

# gets list of video IDS that have already been downloaded.
# note: each video ID has a '.mp4' suffix.
output_dir = os.path.join(settings.DATA_DIR, 'videos', 'downloads')
downloaded_videos = [fname for fname in listfiles(output_dir) if not fname.startswith('.')]
:
    data = pd.read_csv(os.path.join(path, fname))
    video_ids.append(data.video_id.values)


# downloads videos by video ID.
msg = 'You are about to attempt to download {0} videos. Do you wish to continue ([y]es/[n]o)?'.format(video_ids)
s = input(msg)
if s in ['yes', 'y']:
    print('downloading videos...')
    base_url = "http://www.youtube.com/watch?v="
    for video_id in video_ids:
        if video_id + '.mp4' in downloaded_videos:
            print('Already downloaded video (ID: {0})'.format(video_id))
            continue
        yt = YouTube(''.join([base_url, video_id]))
        if len(yt.get_videos()) == 0:
            print('Failed to find video for video ID: {0}'.format(video_id))
        if len(yt.filter('mp4')) == 0:
            print('Failed to find MPEG-4 video for video ID: {0}'.format(video_id))

        # print(yt.get_videos())
        # print(yt.filename)

        # set the filename:
        yt.set_filename(video_id)

        # filters MPEG-4 video with highest resolution.
        video = yt.filter('mp4')[-1]

        # downloads video.
        video.download(output_dir)
