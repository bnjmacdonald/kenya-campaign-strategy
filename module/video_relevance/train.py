"""searchers for the best classifier through a hyper-parameter search for predicting
whether a Youtube video is "relevant" (1) or "not relevant" for transcription/translation.

A "relevant" video is one that contains some portion of a campaign rally.

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
    X = featurizer.transform(X_train)
    if 'verbosity' in tpot_kwargs and tpot_kwargs['verbosity'] > 0:
        print(f'Beginning hyper-parameter search with training data shape: {X.shape}.')
    tpot = TPOTClassifier(**tpot_kwargs)
    tpot.fit(X, y_train)
    if 'periodic_checkpoint_folder' in tpot_kwargs:
        tpot.export(os.path.join(tpot_kwargs['periodic_checkpoint_folder'], 'best_pipeline.py'))
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
