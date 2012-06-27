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

def home(request):
    """Show all the tweets that have at least one link in the tweet"""
    users = list(UserTweet.objects.filter(last_date_to_crawl__isnull=False))
    tweets = [Tweet.objects.filter(retweets__gt=0, links__isnull=False, username__username=user, created_at__gte=user.last_date_to_crawl) for user in users]
    
    tweets = reduce(lambda x, y: x | y, tweets)
    
    tweets.order_by('-retweets', '-created_at')
    d = {}
    for tweet in tweets:
        links = tweet.all_long_links()
        if "http://mejorando.la" in links:
            continue
        for link in links:
            if link in d:
                d[link].retweets += tweet.retweets
            else:
                d[link] = tweet
            
    response = {'response': sorted(d.items(), key=lambda x: (x[1].retweets, x[1].created_at), reverse=True)}
    return render_to_response('home.html', response)
