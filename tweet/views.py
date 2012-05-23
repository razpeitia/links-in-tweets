from collections import OrderedDict
from django.http import HttpResponse
from django.shortcuts import render_to_response
from tweet.models import Tweet, Link, UserTweet
from urlparse import urlsplit, urlunsplit
import datetime
import json
import re
import requests
import urllib

def all_tweets(username, max_id):
    url = "https://api.twitter.com/1/statuses/user_timeline.json?include_entities=true&screen_name=%s&count=200" % (username,)
    if max_id:
        url = url + "&max_id=" + str(max_id)
    tweets = json.loads(requests.get(url).text)
    return tweets

def all_links_in(tweet):
    r_links = re.compile(r"(http://[^ ]+)")
    links_in_tweet = set(r_links.findall(tweet.text))
    return list(links_in_tweet)

def all_tweets_since(username, since):
    tweets = []
    max_id = 0
    done = False
    while not done:
        for tweet in all_tweets(username, max_id):
            tweet['created_at'] = \
                datetime.datetime.strptime(tweet['created_at'], 
                                           '%a %b %d %H:%M:%S +0000 %Y')
            if tweet['created_at'] < since:
                done = True
                break
            tweets.append(tweet)
            max_id = tweet['id_str']
    return tweets

def anterior_jueves(now):
    _12AM = datetime.time(hour=0)
    _JUE = 3  # Monday=0 for weekday()
    now -= datetime.timedelta((_JUE - now.weekday()) % 7)
    now = now.combine(now.date(), _12AM)
    return now

def crawl_tweets_for(username, since):
    for tweet in all_tweets_since(username, since):
        try:
            tweet_record = Tweet.objects.get(pk=tweet['id'])
            tweet_record.retweets = tweet['retweet_count']
        except Tweet.DoesNotExist:
            tweet_data = {
                      'tweet_id': tweet['id'],
                      'text': tweet['text'], 
                      'created_at': tweet['created_at'], 
                      'retweets': tweet['retweet_count'],
                      'username': UserTweet.objects.get(username=username),
                   }
            tweet_record = Tweet(**tweet_data)
        tweet_record.save()
        
def crawl(request, username=None, year=None, month=None, day=None):
    crawl_tweets_for(username, 
                     datetime.datetime(int(year), int(month), int(day)))
    return HttpResponse("OK")

def extract_all_links(request):
    tweets = list(Tweet.objects.all().order_by('-retweets', '-created_at'))
    for tweet in tweets:
        for short_link in all_links_in(tweet):
            link, created = \
            Link.objects.get_or_create(short_link=normalize(short_link), 
                                       defaults={'long_link':""})
            link.save()
    return HttpResponse("OK")

def expand_all_links(request):
    links = list(Link.objects.all().filter(long_link__exact=""))
    for link in links:
        url = "http://api.longurl.org/v2/expand?&url=%s&format=json" % (link,)
        try:
            response = requests.get(url).text
            long_link = json.loads(response)['long-url']
            link.long_link = normalize(long_link)
            link.save()
        except:
            pass
        
    return HttpResponse("OK")

def normalize(link):
    link = link.rstrip("/")
    scheme, netloc, path, qs, anchor = urlsplit(link)
    netloc = netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = urllib.unquote(path)
    path = urllib.quote(path, '/%')
    qs = urllib.unquote_plus(qs)
    qs = urllib.quote_plus(qs, ':&=')
    return urlunsplit((scheme, netloc, path, qs, anchor))

def home(request):
    tweets = list(Tweet.objects.all().filter(retweets__gt=0).order_by('-retweets', '-created_at'))
    links = list(Link.objects.all())
    translate_links = {link.short_link: link.long_link for link in links}
        
    response = {}
    for tweet in tweets:
        links_in_tweet = [normalize(link) for link in all_links_in(tweet)]
        links_in_tweet = [translate_links[link] for link in links_in_tweet]
        if links_in_tweet and 'http://mejorando.la' not in links_in_tweet:
            links_in_tweet = links_in_tweet[0]
            if links_in_tweet not in response:
                response[links_in_tweet] = tweet
            else:
                response[links_in_tweet].retweets += tweet.retweets
     
    response = {'tweets': sorted(response.items(), key=lambda x: x[1].retweets, reverse=True),}
    return render_to_response('home.html', response)
