from django.db import models
import urllib
import urlparse
import requests
import json
import datetime

class UserTweet(models.Model):
    """
    username -> Twitter username.
    last_date_to_crawl -> Crawl since this date.
    """
    username = models.CharField(max_length=80, primary_key=True)
    last_date_to_crawl = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return "%s" % (self.username,)
    
    def __unicode__(self):
        return u"%s" % (self.__str__(),)
    
    def __repr__(self):
        return u"@%s" % (self.__str__(),)
    

class Tweet(models.Model):
    """
    tweet_id -> Tweet unique id.
    username -> Twitter username whom publish it.
    created_at -> Tweet's publish date and time.
    text -> Tweet text.
    retweets -> Retweet count.
    """
    tweet_id = models.BigIntegerField(primary_key=True)
    created_at = models.DateTimeField()
    text = models.TextField(max_length=140)
    retweets = models.IntegerField()
    
    username = models.ForeignKey(UserTweet, related_name='original_poster')
    
    links = models.ManyToManyField('Link', blank=True)
    hashtags = models.ManyToManyField('Hashtag', blank=True)
    user_mentions = models.ManyToManyField(UserTweet, blank=True)
    
    @staticmethod
    def all_tweets(username, max_id):
        """Get the first 200 username's tweets since some max_id from Twitter's API"""
        url = "https://api.twitter.com/1/statuses/user_timeline.json?include_entities=true&screen_name=%s&count=200" % (username,)
        if max_id:
            url = url + "&max_id=" + str(max_id)
        tweets = json.loads(requests.get(url).text)
        return tweets
    
    @staticmethod
    def all_tweets_since(username, since):
        """Crawl for all tweets since some specific date"""
        since = since.replace(tzinfo=None)
        tweets = []
        max_id = 0
        done = False
        while not done:
            tweet_list = Tweet.all_tweets(username, max_id)
            if len(tweet_list) <= 1:
                break
            for tweet in tweet_list:
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
        """Get or create some tweet in the database"""
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
        """Crawl for some username"""
        user = UserTweet.objects.get(username=username)
        since = user.last_date_to_crawl
        tweets = Tweet.all_tweets_since(username, since)
        for tweet in tweets:
            entities = tweet['entities']
            tweet = Tweet.get(tweet['id'], 
                      tweet['retweet_count'],
                      tweet['text'], 
                      tweet['created_at'], 
                      username)
            tweet.save()
            tweet.add(entities)
    
    def add(self, entities):
        hashtags = entities['hashtags']
        for hashtag in hashtags:
            hashtag = Hashtag.objects.get_or_create(hashtag=hashtag['text'])[0]
            self.hashtags.add(hashtag)
            
            
        urls = entities['urls']
        for url in urls:
            link = Link.objects.get_or_create(short_link=url['url'])[0]
            self.links.add(link)
        
        user_mentions = entities['user_mentions']
        for user_mention in user_mentions:
            user_mention = UserTweet.objects.get_or_create(username=user_mention['screen_name'])[0]
            self.user_mentions.add(user_mention)
        
        self.save()
            
    def all_links(self):
        return list(self.links.all())
    
    def all_long_links(self):
        return [link['long_link'] for link in self.links.values('long_link')]
    
    def all_hashtags(self):
        return list(self.hashtags.all())
    
    def all_user_mentions(self):
        return list(self.user_mentions.all())
    
    def __str__(self):
        return "%s" % (self.text,)
    
    def __unicode__(self):
        return u"%s" % (self.__str__(),)


class Link(models.Model):
    short_link = models.CharField(max_length=100, primary_key=True)
    long_link = models.CharField(max_length=256, blank=True, default="")
    
    
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
    
    def __repr__(self):
        return u"%s" % (self.short_link,)
    
class Hashtag(models.Model):
    hashtag = models.CharField(primary_key=True, max_length=140)
    
    def __str__(self):
        return '#%s' % (self.hashtag,)
    
    def __unicode__(self):
        return u'%s' % (self.__str__(),)
    
    def __repr__(self):
        return u"%s" % (self.__str__(),)
    