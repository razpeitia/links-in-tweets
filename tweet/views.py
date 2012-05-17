from collections import Counter
from django.shortcuts import render_to_response
import json
import re
import requests

def all_links(username):
    r_links = re.compile(r"(http://[^ ]+)")
    url = "https://api.twitter.com/1/statuses/user_timeline.json?include_entities=true&include_rts=true&screen_name=%s&count=200" % (username,)
    tweets = json.loads(requests.get(url).text)
    links = Counter()
    for tweet in tweets:
        links_in_tweet = r_links.findall(tweet['text'])
        links.update(links_in_tweet)
    return links

def home(request):
    links = Counter()
    for username in ('cvander', 'freddier'):
        links.update(all_links(username))
    response = {'links': links.most_common()}
    return render_to_response('home.html', response)
