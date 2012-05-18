from collections import Counter
from django.shortcuts import render_to_response
import json
import re
import requests
import threading
import Queue
import datetime

def all_tweets(username, max_id):
    url = "https://api.twitter.com/1/statuses/user_timeline.json?include_entities=true&include_rts=true&screen_name=%s&count=200" % (username,)
    if max_id:
        url = url + "&max_id=" + str(max_id)
    tweets = json.loads(requests.get(url).text)
    return tweets

def all_links_in(tweet):
    r_links = re.compile(r"(http://[^ ]+)")
    links_in_tweet = set(r_links.findall(tweet['text']))
    return list(links_in_tweet)

def all_links_since(username, since):
    links = Counter()
    max_id = 0
    done = False
    while not done:
        tweets = all_tweets(username, max_id)
        for tweet in tweets:
            created_at = tweet['created_at']
            created_at = datetime.datetime.strptime(created_at, 
                                            '%a %b %d %H:%M:%S +0000 %Y')
            if created_at >= since:
                links.update(all_links_in(tweet))
            else:
                done = True
                break
            max_id = tweet['id_str']
    return links

def anterior_jueves_4pm(now):
    _4PM = datetime.time(hour=16)
    _JUE = 3  # Monday=0 for weekday()
    old_now = now
    now += datetime.timedelta((_JUE - now.weekday()) % 7)
    now = now.combine(now.date(), _4PM)
    if old_now >= now:
        now += datetime.timedelta(days=7)
    now -= datetime.timedelta(days=14)
    return now


class LongLinkThread(threading.Thread):
    def __init__(self, queue, links):
        threading.Thread.__init__(self)
        self.queue = queue
        self.links = links

    def run(self):
        while True:
            (url, count) = self.queue.get()
            for _ in xrange(5): #Numero de intentos
                try:
                    response = requests.get(url).text
                    long_link = json.loads(response)['long-url']
                    self.links[long_link] += count
                    break
                except:
                    pass
            self.queue.task_done()

def home(request):
    links = Counter()
    
    anterior_jueves = anterior_jueves_4pm(datetime.datetime.now())
    for username in ('cvander', 'freddier'):
        links.update(all_links_since(username, anterior_jueves))

    queue = Queue.Queue()
    long_links = Counter()
    for link, count in links.iteritems():
        t = LongLinkThread(queue, long_links)
        t.setDaemon(True)
        t.start()
        
    for link, count in links.iteritems():
        url = "http://api.longurl.org/v2/expand?&url=%s&format=json" % (link,)
        queue.put((url, count))
    queue.join()
    response = {'links': long_links.most_common()}
    return render_to_response('home.html', response)
