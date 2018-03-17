
import os
import re
import argparse
from typing import List
import pandas as pd
import numpy as np
import isodate

from module import settings

def listfiles(path):
    for fname in os.listdir(path):
        if os.path.isfile(os.path.join(path, fname)) and not fname.startswith('.'):
            yield fname

def get_videos():
    """gets list of videos to download."""
    path = os.path.join(settings.DATA_DIR, 'videos')
    videos = []
    for fname in listfiles(path):
        data = pd.read_csv(os.path.join(path, fname))
        videos.append(data)
    videos = pd.concat(videos, axis=0)
    return videos

def get_video_ids():
    """wrapper to get_videos that only returns an np.array of video IDs."""
    videos = get_videos()
    return videos.video_id.values

def get_speech_video_ids():
    """gets list of video ids to download, but only for video ids that are
    predicted to be speeches.

    Assume that predicted labels are in 'labels.csv' in settings.OUTPUT_DIR.
    """
    data = pd.read_csv(os.path.join(settings.OUTPUT_DIR, 'class_preds.csv'))
    data.columns = ['id', 'label']
    return data.id[data.label == 1]

def duration_str_to_num(durations):
    """converts Youtube video duration from format like "PT11M42S" to float.

    Returns np.array where each element is the duration in seconds.
    """
    durations_seconds = np.array([isodate.parse_duration(d).total_seconds() if pd.notnull(d) else np.nan for d in durations])
    return durations_seconds

def parse_unknown_args(args: List[str]) -> argparse.Namespace:
    """parses unknown args returned from second element of parser.parse_known_args().

    Arguments:

        args: List[str]. Unparsed arguments.

    Returns:

        parsed_args: argparse.Namespace. Namespace of parsed arguments.

    Example::

        >>> args = ['-f', '1', '--foo', 'abcd dfd edd', '--bar', 'adv', '--bar2', '--foo2', '1.5', '--foo3', '"a b c"']
        >>> parse_unknown_args(args)
        Namespace(bar='adv', bar2=True, f=1, foo=['abcd', 'dfd', 'edd'], foo2=1.5, foo3='a b c')
    """
    parsed_args = {}
    arg = None
    while len(args) > 0:
        el = args.pop(0)
        if is_arg(el):
            arg = re.sub(r'^-{1,2}', '', el)
            if len(args) == 0 or (len(args) > 0 and is_arg(args[0])):
                parsed_args[arg] = True
        else:
            while len(args) > 0 and not is_arg(args[0]):
                el += ' ' + args.pop(0)
            assert arg is not None, '{0} value encountered before arg name.'.format(el)
            el = el.strip()
            if re.search(r'^[\'"].+[\'"]$', el):
                vals = [el[1:-1]]
            else:
                vals = el.split(' ')
            parsed_val = []
            for val in vals:
                try:
                    if '.' in val:
                        val = float(val)
                    elif el in ['True', 'False']:
                        val = val == 'True'
                    else:
                        val = int(val)
                except ValueError:
                    pass
                parsed_val.append(val)
            assert arg not in parsed_args, '{0} arg was passed twice. Each arg can only be passed once.'
            parsed_args[arg] = parsed_val if len(parsed_val) > 1 else parsed_val[0]
    return argparse.Namespace(**parsed_args)


def is_arg(s):
    """given a string (s), returns True if s is a command-line argument (i.e.
    prefixed with '--' or '-'). False otherwise."""
    return bool(re.search(r'^-{1,2}', s))
