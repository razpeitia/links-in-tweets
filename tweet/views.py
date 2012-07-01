from django.http import HttpResponse
from django.shortcuts import render_to_response
from tweet.models import Tweet, Link, UserTweet
from multiprocessing.pool import ThreadPool

        
def crawl(request, username=None):
    """Given some twitter username get all the tweets since some specific date"""
    Tweet.crawl_for(username)
    return HttpResponse("OK")

def expand_all_links(request):
    """For all the shorten urls expand that url, using 4 worker threads"""
    links = list(Link.objects.all().filter(long_link__exact=""))

    def get_long_link(link):
        for _ in xrange(5):
            try:
                link.expand()
                break
            except Exception:
                pass
    
    number_of_threads = 0
    if links:
        if len(links) >= 4:
            number_of_threads = 4
        else:
            number_of_threads = len(links)
    else:
        return "OK"
    p = ThreadPool(number_of_threads)
    p.map(get_long_link, links)
    
    return HttpResponse("OK")


def update(request):
    """Crawl for all tweets -> Extract all the links -> Expand the links"""
    users = list(UserTweet.objects.filter(last_date_to_crawl__isnull=False))
    for user in users:
        crawl(request, user.username)
    expand_all_links(request)
    return HttpResponse("OK")

def mentions(request):
    users = UserTweet.toCrawl()
    tweets = [Tweet.objects.filter(retweets__gt=0, user_mentions__isnull=False, username=user, created_at__gte=user.last_date_to_crawl) for user in users]
    tweets = reduce(lambda x, y: x | y, tweets)
    tweets = list(set(tweets))
    
    d = {}
    for tweet in tweets:
        user_mentions = tweet.all_user_mentions()
        for user_mention in user_mentions:
            if user_mention in d:
                d[user_mention].append(tweet)
            else:
                d[user_mention] = [tweet]
    
    for user_mention, tweets in d.iteritems():
        retweets = sum(tweet.retweets for tweet in tweets)
        tweet = min(tweets, key=lambda tweet: tweet.created_at)
        d[user_mention] = {'tweet': tweet, 'retweets': retweets}
    response = {'response': sorted(d.items(), key=lambda tweet: (tweet[1]['retweets'], tweet[1]['tweet'].created_at), reverse=True)}
    
    return render_to_response('mentions.html', response)

def user_mentions(request, username=None):
    username = UserTweet(pk=username)
    users = UserTweet.toCrawl()
        
    tweets = [Tweet.objects.filter(retweets__gt=0, user_mentions__in=[username], username=user, created_at__gt=user.last_date_to_crawl) for user in users]
    tweets = reduce(lambda x, y: x | y, tweets)
    tweets = list(set(tweets))
    tweets = sorted(tweets, key=lambda tweet: (tweet.retweets, tweet.created_at), reverse=True) 
    response = {'response': zip([username] * len(tweets), tweets)}
    return render_to_response('user_mentions.html', response)
        
        

def hashtags(request):
    users = UserTweet.toCrawl()
    tweets = [Tweet.objects.filter(retweets__gt=0, hashtags__isnull=False, username=user, created_at__gte=user.last_date_to_crawl) for user in users]
    tweets = reduce(lambda x, y: x | y, tweets)
    tweets = list(set(tweets))
    
    d = {}
    for tweet in tweets:
        hashtags = tweet.all_hashtags()
        for hashtag in hashtags:
            if hashtag in d:
                d[hashtag].append(tweet)
            else:
                d[hashtag] = [tweet]
    
    for hashtag, tweets in d.iteritems():
        retweets = sum(tweet.retweets for tweet in tweets)
        tweet = min(tweets, key=lambda tweet: tweet.created_at)
        d[hashtag] = {'tweet': tweet, 'retweets': retweets} 
    
    response = {'response': sorted(d.items(), key=lambda tweet: (tweet[1]['retweets'], tweet[1]['tweet'].created_at), reverse=True)}
    return render_to_response('hashtags.html', response)

def hashtag(request, hashtag):
    users = UserTweet.toCrawl()
    tweets = [Tweet.objects.filter(retweets__gt=0, hashtags__in=[hashtag], username=user, created_at__gte=user.last_date_to_crawl) for user in users]
    tweets = reduce(lambda x, y: x | y, tweets)
    tweets = list(set(tweets))
    tweets = sorted(tweets, key=lambda tweet: (tweet.retweets, tweet.created_at), reverse=True)
    
    response = {'response': zip([hashtag] * len(tweets), tweets)}
    
    return render_to_response('hashtag.html', response)

def links(request):
    """Show all the tweets that have at least one link in the tweet"""
    users = UserTweet.toCrawl()
    tweets = [Tweet.objects.filter(retweets__gt=0, links__isnull=False, username=user, created_at__gte=user.last_date_to_crawl) for user in users]
    tweets = reduce(lambda x, y: x | y, tweets)
    tweets = list(set(tweets))
    
    d = {}
    for tweet in tweets:
        links = tweet.all_long_links()
        for link in links:
            if link in d:
                d[link].append(tweet)
            else:
                d[link] = [tweet]
    
    for link, tweets in d.iteritems():
        retweets = sum(tweet.retweets for tweet in tweets)
        tweet = min(tweets, key=lambda tweet: tweet.created_at)
        d[link] = {'tweet': tweet, 'retweets': retweets}
    response = {'response': sorted(d.items(), key=lambda x: (x[1]['retweets'], x[1]['tweet'].created_at), reverse=True)}
    return render_to_response('links.html', response)

def link(request, link):
    users = UserTweet.toCrawl()
    tweets = [Tweet.objects.filter(retweets__gt=0, links__long_link__in=[link], username=user, created_at__gte=user.last_date_to_crawl) for user in users]
    tweets = reduce(lambda x, y: x | y, tweets)
    tweets = list(set(tweets))
    tweets = sorted(tweets, key=lambda tweet: (tweet.retweets, tweet.created_at), reverse=True)
    response = {'response': zip([link] * len(tweets), tweets)}
    return render_to_response('link.html', response)

def home(request):
    """Show all the tweets that have at least one link in the tweet"""
    users = UserTweet.toCrawl()
    tweets = [Tweet.objects.filter(retweets__gt=0, links__isnull=False, username=user, created_at__gte=user.last_date_to_crawl) for user in users]
    tweets = reduce(lambda x, y: x | y, tweets)
    tweets = list(set(tweets))
    
    d = {}
    for tweet in tweets:
        links = tweet.all_long_links()
        for link in links:
            if link in d:
                d[link].append(tweet)
            else:
                d[link] = [tweet]
    
    for link, tweets in d.iteritems():
        retweets = sum(tweet.retweets for tweet in tweets)
        tweet = min(tweets, key=lambda tweet: tweet.created_at)
        d[link] = {'tweet': tweet, 'retweets': retweets}
    response = {'response': sorted(d.items(), key=lambda x: (x[1]['retweets'], x[1]['tweet'].created_at), reverse=True)}
    return render_to_response('home.html', response)
