#!/bin/bash/python
import unittest
from config import DEVELOPER_KEY
from video_scraper import youtube_playlistitems_list, load_videos

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class VideoScraperTest(unittest.TestCase):
    def test_recall(self):
        playlist_result = youtube_playlistitems_list(playlistId="PLHwxLeuZu13LxkNYpiObxv7hr05UKwuhW", part="id,contentDetails,snippet", maxResults=50, max_pages=10)
        playlist_video_ids = [item['contentDetails']['videoId'] for item in playlist_result]
        scraped_videos = load_videos()
        scraped_video_ids = scraped_videos.video_id.tolist()
        num_in_scraped = sum([el in scraped_video_ids for el in playlist_video_ids])
        print(num_in_scraped/float(len(playlist_video_ids)))
        self.assertEqual(num_in_scraped,len(playlist_video_ids))
        # Todo... test to make sure that script discovers all videos on Danny's list.

if __name__ == '__main__':
    unittest.main()