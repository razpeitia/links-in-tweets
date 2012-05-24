from django.db import models
import re
import urllib
import urlparse
import requests
import json
import datetime

class UserTweet(models.Model):
    username = models.CharField(max_length=80, primary_key=True)
    last_date_to_crawl = models.DateTimeField()
    
    def __str__(self):
        return "%s" % (self.username,)
    
    def __unicode__(self):
        return u"%s" % (self.__str__(),)
    

class Tweet(models.Model):
    tweet_id = models.BigIntegerField(primary_key=True)
    username = models.ForeignKey(UserTweet)
    created_at = models.DateTimeField()
    text = models.TextField(max_length=140)
    retweets = models.IntegerField()
    r_links = re.compile(r"(http://[^ ]+)")
    
    @staticmethod
    def all_tweets(username, max_id):
        url = "https://api.twitter.com/1/statuses/user_timeline.json?include_entities=true&screen_name=%s&count=200" % (username,)
        if max_id:
            url = url + "&max_id=" + str(max_id)
        tweets = json.loads(requests.get(url).text)
        return tweets
    
    @staticmethod
    def all_tweets_since(username, since):
        since = since.replace(tzinfo=None)
        tweets = []
        max_id = 0
        done = False
        while not done:
            for tweet in Tweet.all_tweets(username, max_id):
                tweet['created_at'] = \
                    datetime.datetime.strptime(tweet['created_at'], 
                                               '%a %b %d %H:%M:%S +0000 %Y')
                if tweet['created_at'] < since:
                    done = True
                    break
                tweets.append(tweet)
                max_id = tweet['id_str']
        return tweets

    @staticmethod
    def get(tweet_id, retweet_count, text, created_at, username_id):
        try:
            tweet_record = Tweet.objects.get(pk=tweet_id)
            tweet_record.retweets = retweet_count
            return tweet_record
        except Tweet.DoesNotExist:
            tweet_data = {
                      'tweet_id': tweet_id,
                      'text': text, 
                      'created_at': created_at, 
                      'retweets': retweet_count,
                      'username_id': username_id,
                   }
            return Tweet(**tweet_data)
        

    @staticmethod
    def crawl_for(username):
        user = UserTweet.objects.get(username=username)
        since = user.last_date_to_crawl
        for tweet in Tweet.all_tweets_since(username, since):
            tweet = Tweet.get(tweet['id'], 
                      tweet['retweet_count'], 
                      tweet['text'], 
                      tweet['created_at'], 
                      username)
            tweet.save()
    
    def all_links(self):
        links_in_tweet = set(self.r_links.findall(self.text))
        return list(links_in_tweet)
    
    def __str__(self):
        return "%s" % (self.text,)
    
    def __unicode__(self):
        return u"%s" % (self.__str__(),)


class Link(models.Model):
    short_link = models.CharField(max_length=100, primary_key=True)
    long_link = models.CharField(max_length=256, blank=True)
    links_in_tweets = models.ManyToManyField(Tweet)
    
    def __normalize(self, link):
        try:
            link = link.rstrip("/")
            scheme, netloc, path, qs, anchor = urlparse.urlsplit(link)
            netloc = netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            path = urllib.unquote(path)
            path = urllib.quote(path, '/%')
            qs = urllib.unquote_plus(qs)
            qs = urllib.quote_plus(qs, ':&=')
            return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))
        except:
            return link
    
    def expand(self):
        if self.long_link:
            return False
        url = "http://api.longurl.org/v2/expand?&url=%s&format=json" % (self.short_link,)
        try:
            response = requests.get(url).text
            self.long_link = json.loads(response)['long-url']
            self.normalize_long_link()
            self.save()
            return True
        except:
            return False
    
    def normalize_short_link(self):
        self.short_link = self.__normalize(self.short_link)
    
    def normalize_long_link(self):
        self.long_link = self.__normalize(self.long_link)
        
    
    def __str__(self):
        return "%s %s" % (self.short_link, self.long_link)
    
    def __unicode__(self):
        return u"%s" % (self.__str__(),)