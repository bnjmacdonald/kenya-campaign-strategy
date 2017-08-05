"""Downloads Youtube videos.

"""

import os
import sys
from pytube import YouTube
from pprint import pprint
import settings
import utils

# gets list of video IDS that have already been downloaded.
# note: each video ID has a '.mp4' suffix.
output_dir = os.path.join(settings.DATA_DIR, 'videos', 'downloads')
downloaded_videos = [fname for fname in utils.listfiles(output_dir) if not fname.startswith('.')]

# loads all video IDs that are predicted to be speeches.
# video_ids = utils.get_speech_video_ids()

# TEMPORARY: loads all video IDs from the channel "Raila Odinga vs Uhuru Kenyatta 2017"
videos = utils.get_videos()
video_ids = videos[videos.channel_title == "Raila Odinga vs Uhuru Kenyatta 2017"].video_id

# downloads videos by video ID.
msg = 'You are about to attempt to download {0} videos. Do you wish to continue ([y]es/[n]o)?'.format(video_ids.shape[0])
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

        # filters MPEG-4 video with lowest resolution.
        video = yt.filter('mp4')[0]

        # downloads video.
        video.download(output_dir)
