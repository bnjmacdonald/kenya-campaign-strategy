"""searchers for the best classifier through a hyper-parameter search for predicting
whether a Youtube video is "relevant" (1) or "not relevant" for transcription/translation.

A "relevant" video is one that contains some portion of a campaign rally.

This module is designed to be used from the command line. Any keyword arguments
that `sklearn.feature_extraction.text.CountVectorizer` or `tpot.TPOTClassifier`
take can be passed as command line arguments.

Example usage::

    python -m module.video_relevance.train \
        --verbosity 3 \
        --max_features 1000  --stop_words english --binary \
        --periodic_checkpoint_folder $OUTPATH \
        --generations 200 --population_size 25 \
        --scoring f1_macro --cv 5 \
        --n_jobs 1 --max_eval_time_mins 5 \
        --warm_start
"""

import os
import sys
import argparse
import inspect
import datetime
from typing import List, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tpot import TPOTClassifier

from module.utils import get_videos, parse_unknown_args
from module.video_relevance.preprocessing import Featurizer
from module import settings

# random seed used to ensure train/dev/test split is the same on every run.
SEED = 531992

# train/test sizes
TRAIN_SIZE = 0.8

# path to where labels are saved.
LABELS_PATH = os.path.join(settings.DATA_DIR, 'manual', 'video_relevance')


def main(**kwargs) -> None:
    # divides kwargs between `Featurizer` and `TPOTClassifier` kwargs.
    tpot_kwargs = {}
    keys = list(kwargs.keys())
    for k in keys:
        if k in inspect.getargspec(TPOTClassifier).args:
            tpot_kwargs[k] = kwargs.pop(k)
    # loads all data into memory.
    paths = [os.path.join(LABELS_PATH, fname) for fname in os.listdir(LABELS_PATH)]
    X_raw, y = load_data(paths)
    X_raw.title.fillna('', inplace=True)
    X_raw.channel_title.fillna('', inplace=True)
    # splits data into train and test sets.
    X_train, X_test, y_train, y_test = train_test_split(X_raw, y,
        random_state=SEED, train_size=TRAIN_SIZE, test_size=1-TRAIN_SIZE, shuffle=True)
    # KLUDGE: preprocesses text deterministically (i.e. NOT part of the TPOT hyperparameter
    # optimization pipeline).
    featurizer = Featurizer(**kwargs)
    featurizer.fit(X_train)
    X_train = featurizer.transform(X_train)
    if 'verbosity' in tpot_kwargs and tpot_kwargs['verbosity'] > 0:
        print(f'Beginning hyper-parameter search with training data shape: {X_train.shape}.')
    tpot = TPOTClassifier(**tpot_kwargs)
    tpot.fit(X_train, y_train)
    if 'periodic_checkpoint_folder' in tpot_kwargs:
        tpot.export(os.path.join(tpot_kwargs['periodic_checkpoint_folder'], 'best_pipeline.py'))
    if 'verbosity' in tpot_kwargs and tpot_kwargs['verbosity'] > 0:
        X_test = featurizer.transform(X_test)
        print(f'Train set score: {tpot.score(X_train, y_train).round(4)}')
        print(f'Test set score: {tpot.score(X_test, y_test).round(4)}')
    return None


def load_data(paths: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """loads labels and unprocessed features.

    Returns:

        y, X_raw: Tuple[pd.DataFrame, pd.DataFrame]
    """
    videos = get_videos().set_index('video_id')
    labels = []
    for path in paths:
        these_labels = pd.read_csv(path).set_index('video_id').label
        labels.append(these_labels)
    y = pd.concat(labels, axis=0)
    y = y[y.notnull()]
    X_raw = videos.loc[y.index.values]
    assert (y.index == X_raw.index).all()
    assert y.shape[0] == X_raw.shape[0]
    return X_raw, y


if __name__ == '__main__':
    args = parse_unknown_args(sys.argv[1:])
    main(**args.__dict__)
