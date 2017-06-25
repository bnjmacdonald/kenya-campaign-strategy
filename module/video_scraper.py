#!/usr/bin/python
"""Searches Youtube videos for campaign speeches using Youtube API.

Usage
-----

[example] Request videos since 1 April 2017::
    
    python3 video_scraper.py --max-results 50 --published-after "2017-04-01T00:00:00Z" --max-pages 5 --region-code KE --relevance-language sw

[example] Request videos over past week::
    
    python3 video_scraper.py --max-results 50 --max-pages 5 --region-code KE --relevance-language sw    

Test::
    
    python3 video_scraper.py --max-results 5 --max-pages 1 --region-code KE --relevance-language sw

Search procedure
----------------

(1) Get and filter recent uploads from several channels that tend to post full speeches.

(2) Get and filter related videos on videos extracted in (1).

(3) Keyword search for other videos not found via (1) or (2).

This code is based on the Youtube API code sample here: 
https://developers.google.com/youtube/v3/docs/search/list.

Youtube API code samples and tutorials
--------------------------------------

https://developers.google.com/youtube/v3/docs/search

https://developers.google.com/youtube/v3/docs/search/list#try-it

https://developers.google.com/youtube/v3/code_samples/python

https://github.com/youtube/api-samples/tree/master/python

"""

# import sys
# sys.path.append('.')
import os
import settings
import json
import datetime
import csv
import pandas as pd
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
from config import DEVELOPER_KEY

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def youtube_search_list(max_pages=5, **kwargs):
    """calls YouTube data API search.list method."""
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(**kwargs).execute()
    # print(search_response)
    # print(search_response.keys())

    # Extract video ids
    results = search_response['items'][:]
    # video_ids = [search_result["id"]["videoId"] for search_result in search_response['items']]
    page = 1
    while 'nextPageToken' in search_response and len(search_response['nextPageToken']) and page < max_pages:
        search_response = youtube.search().list(pageToken=search_response['nextPageToken'], **kwargs).execute()
        for search_result in search_response['items']:
            results.append(search_result)
        page += 1
        # print(len(results))
    # if verbose:
    #     video_ids = [r["id"]["videoId"] for r in results]
    #     print('Ids: {0}'.format(','.join(video_ids)))
    #     print('Number of unique ids: {0}'.format(len(set(video_ids))))
    return results

def youtube_videos_list(video_ids, **kwargs):
    """calls YouTube data API videos.list method."""
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        developerKey=DEVELOPER_KEY)

    # Call the videos.list method to retrieve details for each video.
    video_response = youtube.videos().list(id=",".join(video_ids), **kwargs).execute()

    # Add each result to the list.
    video_results = []
    for video_result in video_response['items']:
        video_results.append(video_result)

    return video_results

# def youtube_channel_sections_list(channel_id):
#     youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
#         developerKey=DEVELOPER_KEY)
#     channel_sections_list_response = youtube.channelSections().list(
#         part="id,snippet,contentDetails",
#         channelId=channel_id
#     ).execute()
#     return channel_sections_list_response

def youtube_playlistitems_list(max_pages=5, **kwargs):
    """calls YouTube data API playlistitems.list method."""
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    playlistitems_response = youtube.playlistItems().list(**kwargs).execute()
    # print(playlistitems_response)
    # print(playlistitems_response.keys())

    # Extract video ids
    results = playlistitems_response['items'][:]
    # video_ids = [search_result["id"]["videoId"] for search_result in playlistitems_response['items']]
    page = 1
    while 'nextPageToken' in playlistitems_response and len(playlistitems_response['nextPageToken']) and page < max_pages:
        playlistitems_response = youtube.playlistItems().list(pageToken=playlistitems_response['nextPageToken'], **kwargs).execute()
        for search_result in playlistitems_response['items']:
            results.append(search_result)
        page += 1
        # print(len(results))
    # if verbose:
    #     video_ids = [r["id"]["videoId"] for r in results]
    #     print('Ids: {0}'.format(','.join(video_ids)))
    #     print('Number of unique ids: {0}'.format(len(set(video_ids))))
    return results

def load_videos():
    """loads existing videos from csv."""
    path = os.path.join(settings.DATA_DIR, 'videos')
    scraped_videos = []
    for fname in os.listdir(path):
        if fname.endswith('.csv') and not fname.startswith('.'):
            print('loading existing videos from: {0}'.format(fname))
            scraped_videos_batch = pd.read_csv(os.path.join(path, fname))
            # print(scraped_videos_batch.head(2))
            scraped_videos.append(scraped_videos_batch)
    if len(scraped_videos):
        scraped_videos = pd.concat(scraped_videos, axis=0)
    else:
        scraped_videos = pd.DataFrame()
    return scraped_videos

def dedupe_video_ids(search_results, video_ids=[]):
    """dedupes search_results based on list of existing video IDs."""
    search_results_dedupe = []
    # removes any duplicate videos
    for search_result in search_results:
        # print(related_result['snippet']['title'])
        video_id = search_result["id"]["videoId"]
        if video_id not in video_ids:
            video_ids.append(video_id)
            search_results_dedupe.append(search_result)
    print('Deduplication: removed {0} of {1} search results'.format(len(search_results) - len(search_results_dedupe), len(search_results)))
    return search_results_dedupe, video_ids

if __name__ == "__main__":
    one_week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime(format="%Y-%m-%dT%H:%M:%SZ")
    argparser.add_argument("--max-results", help="Max results", type=int, default=50)
    argparser.add_argument("--published-after", help="Published after (e.g. '2017-04-01T00:00:00Z'. Default is one week ago", type=str, default=one_week_ago)
    argparser.add_argument("--max-pages", help="Max pages", type=int, default=10)
    argparser.add_argument("--region-code", help="Region code'", type=str, default="US")
    argparser.add_argument("--relevance-language", help="Relevance language'", type=str, default="en")
    args = argparser.parse_args()
    verbose = True
    # class args(object):
    #     max_results = 50
    #     published_after = "2017-04-01T00:00:00Z"
    #     max_pages = 2
    #     region_code = "KE"
    #     relevance_language = "sw"

    base_kws = {
        'maxResults': args.max_results,
        'publishedAfter': args.published_after,
        'regionCode': args.region_code,
        'relevanceLanguage': args.relevance_language
    }
    
    # loads existing videos.
    scraped_videos = load_videos()
    orig_video_ids = []
    if scraped_videos.shape[0]:
        orig_video_ids = scraped_videos.video_id.tolist()
    video_ids = orig_video_ids[:]
    print('Loaded {0} existing videos'.format(len(video_ids)))

    # loads channels to search.
    with open(os.path.join(settings.DATA_DIR, 'youtube_channels.json'), 'r') as f:
        channels = json.load(f)

    try:
        print('Searching for videos published after {0}'.format(args.published_after))
        # (1) Get and filter recent uploads from several channels that tend to post full speeches.
        channel_ids = [ch['channelId'] for ch in channels if ch['mostly_speeches'] == True]
        kwargs = {
            "type": "video",
            "part": "id,snippet",
            "order": "date",
        }
        kwargs.update(base_kws)
        channel_results = []
        for channel_id in channel_ids:
            print('Looking for videos on channel: {0}'.format(channel_id))
            kwargs['channelId'] = channel_id
            channel_results_batch = youtube_search_list(max_pages=args.max_pages, **kwargs)
            kwargs['channelId'] = None
            channel_results.extend(channel_results_batch)

        channel_results_dedupe, video_ids = dedupe_video_ids(channel_results, video_ids)
        print('Found {0} videos from channel searching.'.format(len(channel_results_dedupe)))

        # (2) Get and filter related videos based on videos extracted in (1).
        kwargs = {
            'type': 'video',
            'part': 'id,snippet',
        }
        kwargs.update(base_kws)
        related_results = []
        for channel_result in channel_results_dedupe:
            print('Searching videos related to: "{0}"'.format(channel_result['snippet']['title'].encode('ascii', 'ignore').decode()))
            kwargs['relatedToVideoId'] = channel_result['id']['videoId']
            related_results_batch = youtube_search_list(max_pages=args.max_pages, **kwargs)
            kwargs['relatedToVideoId'] = None
            related_results.extend(related_results_batch)

        related_results_dedupe, video_ids = dedupe_video_ids(related_results, video_ids)
        print('Found {0} videos from related videos searching.'.format(len(related_results_dedupe)))
        
        # (3) Keyword search for other videos not found via (1) or (2).
        with open(os.path.join(settings.DATA_DIR, 'search_terms.json'), 'r') as f:
            search_terms = json.load(f)
        keywords = [' '.join([x,y]) for x in search_terms['entity_terms_primary'] for y in search_terms['campaign_terms_primary']]
        kwargs = {
            "type": "video",
            "part": "id,snippet",
            # "q": args.q,
        }
        kwargs.update(base_kws)
        search_results = []
        for kw in keywords:
            print('Searching keyword: {0}'.format(kw))
            kwargs['q'] = kw
            search_results_batch = youtube_search_list(max_pages=args.max_pages, **kwargs)
            kwargs['q'] = None
            search_results.extend(search_results_batch)

        search_results_dedupe, video_ids = dedupe_video_ids(search_results, video_ids)
        print('Found {0} videos from keyword searching.'.format(len(search_results_dedupe)))

        # concatenates all search results and requests content details for
        # each video.
        video_results = search_results_dedupe + related_results_dedupe + channel_results_dedupe
        new_video_ids = list(set([vr['id']['videoId'] for vr in video_results]))
        assert all([video_id not in orig_video_ids for video_id in new_video_ids])
        kwargs = {
            'part': 'id,snippet,contentDetails'
        }
        video_results_detail = []
        for i in range(0, len(new_video_ids), 50):
            # print(i)
            video_results_detail_batch = youtube_videos_list(video_ids=new_video_ids[i:i+50], **kwargs)
            video_results_detail.extend(video_results_detail_batch)
        assert len(new_video_ids) == len(video_results_detail)

        # combines the results into a dataframe.
        results = []
        for video_result in video_results_detail:
            results.append([video_result['id'], video_result['snippet']['title'].encode('ascii', 'ignore').decode(), video_result['snippet']['publishedAt'], video_result['snippet']['channelTitle'].encode('ascii', 'ignore').decode(), video_result['contentDetails']['duration']])
        results = pd.DataFrame(results, columns=['video_id', 'title', 'published_at', 'channel_title', 'duration'])
        results.sort_values('published_at', ascending=False, inplace=True)
        # results = sorted(results, key=lambda x: x[2], reverse=True)
        assert results.shape[0] == len(new_video_ids)

        # saves video results to file.
        dt = datetime.datetime.strftime(datetime.datetime.now(), format="%Y-%m-%dT%H-%M-%SZ")
        fname = "youtube_search_results_{0}.csv".format(dt)
        pd.DataFrame.to_csv(results, os.path.join(settings.DATA_DIR, 'videos', fname), header=True, index=False, quoting=csv.QUOTE_ALL)
        print('Saved {0} new videos to {1}'.format(results.shape[0], fname))
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))

