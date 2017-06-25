"""

Instructions for setup: http://stackoverflow.com/questions/37083058/programmatically-searching-google-in-python-using-custom-search.

"""

import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import pprint


api_key = ""  # API key
cse_id = ""  # Custom Search Engine ID

def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']

results = google_search('Sammy Mwaita education kenya', api_key, cse_id, num=10)

for result in results:
    print(result['title'])
    print(result['link'])
    print()

for result in results:
    pprint.pprint(result)


result = results[0]
url = result['link']
r = requests.get(url)

soup = BeautifulSoup(r.text, 'html.parser')

# ...


