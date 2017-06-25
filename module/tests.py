#!/bin/bash/python
import unittest

from video_scraper import youtube_playlistitems_list


class VideoScraperTest(unittest.TestCase):
    def test_recall():
        playlist_result = youtube_playlistitems_list(playlistId="PLHwxLeuZu13LxkNYpiObxv7hr05UKwuhW", part="id,contentDetails,snippet", maxResults=50, max_pages=10)
        playlist_video_ids = [item['contentDetails']['videoId'] for item in playlist_result]
        # Todo... test to make sure that script discovers all videos on Danny's list.

if __name__ == '__main__':
    unittest.main()