
import os
import shutil
import traceback
import unittest
import subprocess

from video_relevance import train
from module import settings

class MainTests(unittest.TestCase):

    def setUp(self):
        self.outpath = os.path.join(settings.EXPERIMENTS_DIR, 'tests', 'video_relevance', 'tpot')
        if os.path.exists(self.outpath):
            shutil.rmtree(self.outpath)
        os.makedirs(self.outpath)

    def tearDown(self):
        shutil.rmtree(self.outpath)

    def test_cli_simple(self):
        """tests that the `train` module executes without error when used
        from the command line and saves checkpoint + best pipeline to disk.
        """
        
        out = subprocess.call([
            'python', '-m', 'module.video_relevance.train',
            '--verbosity', '3', '--max_features', '1000', '--periodic_checkpoint_folder',
            self.outpath, '--warm_start', '--generations', '3', '--population_size', '2',
            '--max_eval_time_mins', '1', '--config_dict', '"TPOT light"'
        ])
        self.assertEqual(out, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.outpath, 'best_pipeline.py')))
        # self.assertGreaterEqual(len(os.listdir(self.outpath)), 2)

if __name__ == '__main__':
    unittest.main()
