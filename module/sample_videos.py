"""selects a random sample of videos and saves the sample to a csv file ondisk.

Usage:

    $ python -m sample_videos
"""

import os
import pandas as pd
import numpy as np
import settings

def main():
    max_date = "2017-08-15"
    sample_size = 500
    np.random.seed(872614)
    inpath = os.path.join(settings.DATA_DIR, 'videos')
    outpath = os.path.join(settings.DATA_DIR, 'generated', 'videos_to_label.csv')
    all_videos = []
    for fname in os.listdir(inpath):
        videos = pd.read_csv(os.path.join(inpath, fname))
        all_videos.append(videos)
    all_videos = pd.concat(all_videos, axis=0)
    assert all_videos.shape[1] == 5, 'there should be five columns'
    assert all_videos.published_at.dtype == 'object'
    videos_to_sample = all_videos[all_videos.published_at < max_date]
    print('loaded {0} videos scraped before 2017-08-15'.format(videos_to_sample.shape[0]))
    # samples N videos.
    sampled_videos = videos_to_sample.sample(n=sample_size, replace=False, axis=0)
    # shuffles the sampled videos.
    sampled_videos = sampled_videos.sample(frac=1).reset_index(drop=True) 
    sampled_videos.to_csv(outpath, index=False)
    print('saved {0} randomly sampled videos to {1}'.format(sampled_videos.shape[0], outpath))
    return 0

if __name__ == '__main__':
    main()

