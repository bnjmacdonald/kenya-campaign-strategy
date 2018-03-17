"""classes for video text preprocessing.
"""

import datetime
import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import CountVectorizer

from module.utils import get_videos, duration_str_to_num


class Featurizer(BaseEstimator, TransformerMixin):
    """constructs a feature union of text and numeric features for each video.
    """

    def __init__(self, *args, **kwargs):
        self.featurizer = FeatureUnion(
            transformer_list=[
                ('text_title', Pipeline([
                    ('selector', ItemSelector(key='title')),
                    ('count_vectorizer', CountVectorizer(*args, **kwargs)),
                ])),
                ('text_channel_title', Pipeline([
                    ('selector', ItemSelector(key='channel_title')),
                    ('count_vectorizer', CountVectorizer(*args, **kwargs)),
                ])),
                ('numeric', NumericFeatures()),
            ],
            # weight components in FeatureUnion
            transformer_weights={
                'text_title': 1.0,
                'text_channel_title': 1.0,
                'numeric': 1.0,
            },
        )

    def fit(self, X, y=None):
        return self.featurizer.fit(X)

    def transform(self, X):
        return self.featurizer.transform(X).todense()


class ItemSelector(BaseEstimator, TransformerMixin):
    """For data grouped by feature, select subset of data at a provided key.

    The data is expected to be stored in a 2D data structure, where the first
    index is over features and the second is over samples.  i.e.

    >> len(data[key]) == n_samples

    Please note that this is the opposite convention to scikit-learn feature
    matrixes (where the first index corresponds to sample).

    ItemSelector only requires that the collection implement getitem
    (data[key]).  Examples include: a dict of lists, 2D numpy array, Pandas
    DataFrame, numpy record array, etc.

    >>> data = {'a': [1, 5, 2, 5, 2, 8],
               'b': [9, 4, 1, 4, 1, 3]}
    >>> ds = ItemSelector(key='a')
    >>> data['a'] == ds.transform(data)

    ItemSelector is not designed to handle data grouped by sample.  (e.g. a
    list of dicts).  If your data is structured this way, consider a
    transformer along the lines of `sklearn.feature_extraction.DictVectorizer`.

    Arguments:

        key: hashable, required. The key corresponding to the desired value in a mappable.
    """
    def __init__(self, key):
        self.key = key

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.key]


class NumericFeatures(BaseEstimator, TransformerMixin):
    """Extract numeric features from each video."""
    election_date = datetime.datetime(2017, 8, 8)

    def fit(self, videos, y=None):
        seconds = duration_str_to_num(videos.duration.values)
        _, self.bins = pd.qcut(seconds, q=10, retbins=True)
        return self

    def transform(self, videos):
        seconds = duration_str_to_num(videos.duration.values)
        seconds_bin = np.array([np.searchsorted(self.bins, x) - 1 if pd.notnull(x) else np.nan for x in seconds])
        seconds_bin = seconds_bin.clip(self.bins.min(), self.bins.max())
        title_length = videos.title.apply(lambda x: len(x) if pd.notnull(x) else np.nan)
        channel_title_length = videos.channel_title.apply(lambda x: len(x) if pd.notnull(x) else np.nan)
        days_from_election = pd.to_datetime(videos.published_at).apply(lambda x: (x - self.election_date).days if pd.notnull(x) else np.nan).values
        X = np.stack([seconds_bin, title_length, channel_title_length, days_from_election], axis=1)
        # fills NAs with column medians.
        medians = np.nanmedian(X, axis=0)
        inds = np.where(np.isnan(X))
        X[inds] = np.take(medians, inds[1])
        assert np.isnan(X).sum() == 0
        return X

    def get_feature_names(self):
        return ['seconds_bin', 'title_length', 'channel_title_length', 'days_from_election']
