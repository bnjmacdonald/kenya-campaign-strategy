#!/bin/bash

source /home/bmacdon/.virtualenvs/kenya-campaign-strategy/bin/activate
home="/home/bmacdon/projects" # /afs/.ir/users/b/m/bmacdon
python3 $home/kenya-campaign-strategy/module/video_scraper.py --max-results 50 --max-pages 5 --region-code KE --relevance-language sw
