"""Classifies videos into "speech" or "not speech" using active learning.

How to use this script:

Simply run the code from the command line (`python classify_videos.py`) and
follow the prompts. It will save your hand labels and the predictions to
'output/'.


To watch a video with a specific YouTube ID, visit::

    https://www.youtube.com/watch?v=[id]

where you replace [id] with the video ID.

Notes on labeling:

Criteria for being labeled as a speech:
- any video that has a political candidate speaking, whether this is in front
    of a crowd at a rally, in front of a TV microphones, on a radio show, or
    as a short clip from a news segment.


Excluded videos:
- videos of rallies/events that include no speech. If we want to simply
    find location data later, we should do an entirely separate web-scraping
    search.


Notes:
- for full-length news episodes (e.g. 20 minutes), I generally skimmed to look
    for significant footage of candidates, but if there was nothing
    significant I marked as "non-speech".
"""

import os
import settings
import utils
import pandas as pd
import numpy as np
from actlearn.learner import BinaryActiveLearner
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion

def main():
    videos = utils.get_videos()
    videos.published_at = pd.to_datetime(videos.published_at)

    # filters videos to only include those from 2017.
    videos = videos[videos.published_at.apply(lambda x: x.year) == 2017]
    assert videos.published_at.min().year == 2017

    # raw documents.
    documents = videos.apply(lambda x: "{0}: {1} ({2}) -- {3})".format(x.video_id, x.channel_title, x.duration, x.title), axis=1).values

    # video IDs.
    ids = videos.video_id.tolist()

    # converts video title to bag of words representation.
    vectorizer = CountVectorizer(min_df=6, stop_words="english", lowercase=True)
    bow = vectorizer.fit_transform(videos.title.values)
    print(bow.shape)

    # extracts duration of each video.
    duration = utils.duration_str_to_num(videos.duration)
    # discretizes channel_count into a 0-4 ranking.
    duration = pd.qcut(pd.Series(duration), q=5).cat.codes.values.reshape(-1, 1)

    # constructs count of appearances for each channel.
    # note: since many titles only appear once
    videos.channel_title = videos.channel_title.fillna('')
    channel_count = videos.groupby('channel_title').channel_title.size()
    channel_count.name = 'channel_count'
    videos = pd.merge(videos, channel_count.reset_index(), on='channel_title', how='left')
    min_channel_count = videos.channel_count.quantile(0.25)
    videos.channel_title[videos.channel_count <= min_channel_count] = 'other'
    assert videos.channel_title.value_counts().min() > min_channel_count

    # discretizes channel_count into a 0-4 ranking.
    channel_count = pd.qcut(videos.channel_count, q=5).cat.codes
    channel_count = channel_count.astype(np.int32).values.reshape(-1, 1)


    # consructs dummy variable for channel title.
    channel_title_dummies = pd.get_dummies(videos.channel_title).astype(np.int32).values

    feature_arrays = [bow.toarray(), duration, channel_count, channel_title_dummies]
    assert all([arr.shape[0] == bow.shape[0] for arr in feature_arrays])
    X = np.hstack(feature_arrays)

    labels_dict = {0: 'not_speech', 1: 'speech'}

    # outcome variable.
    # try:
    #     y = pd.read_csv('speech_labels.csv').values
    # except FileNotFoundError as e:
    #     y = np.zeros((X.shape[0],))

    # creates the active learner.
    learner = BinaryActiveLearner(documents=documents, ids=ids, out_path=settings.OUTPUT_DIR, X=X, labels_dict=labels_dict, verbose=1)
    learner.model.n_jobs = 1  # the package is buggy, so this is helpful.

    # learns.
    learner.update(manual_only=True)
    learner.run()

    learner.update(manual_only=True)
    print(np.bincount(learner.class_preds))
    learner.sample(5)

    # to "fix" a specific id:
    # learner.fix_label("VIDEO_ID", LABEL)
    # learner.fix_label("ZbOstw7iE2k", 0)

    # saves predictions to disk.
    learner.save_preds(os.path.join(settings.OUTPUT_DIR, 'class_preds.csv'))

    # quick gut check on performance: checks what % of videos from the Raila
    # Odinga vs Uhuru Kenyatta 2017 have been classified as speeches.
    channel_videos_pos = videos[videos.channel_title == "Raila Odinga vs Uhuru Kenyatta 2017"].index.tolist()
    np.bincount(learner.class_preds[channel_videos_pos])
    # excellent, close to 100% of these videos have been classified as speeches.

if __name__ == '__main__':
    main()
