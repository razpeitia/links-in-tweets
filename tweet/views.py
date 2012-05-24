from django.http import HttpResponse
from django.shortcuts import render_to_response
from tweet.models import Tweet, Link

        
def crawl(request, username=None):
    Tweet.crawl_for(username)
    return HttpResponse("OK")

def extract_all_links(request):
    tweets = list(Tweet.objects.all())
    for tweet in tweets:
        for short_link in tweet.all_links():
            link, _ = \
            Link.objects.get_or_create(short_link=short_link, 
                                       defaults={'long_link':""})
            link.normalize_short_link()
            link.normalize_long_link()
            link.links_in_tweets.add(tweet)
            link.save()
    return HttpResponse("OK")

def expand_all_links(request):
    links = list(Link.objects.all().filter(long_link__exact=""))
    for link in links:
        link.expand()
    return HttpResponse("OK")


def home(request):
    tweets = list(Tweet.objects.all().filter(retweets__gt=0, link__isnull=False))
    d = {}
    for tweet in tweets:
        link = tweet.link_set.all()[0].long_link
        if link == "http://mejorando.la":
            continue
        if link in d:
            d[link].retweets += tweet.retweets
        else:
            d[link] = tweet
            
    response = {'response': sorted(d.items(), key=lambda x: (x[1].retweets, x[1].created_at), reverse=True)}
    return render_to_response('home.html', response)
