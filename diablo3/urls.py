from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'tweet.views.home'),
    url(r'^links/$', 'tweet.views.links'),
    url(r'^links/(?P<link>.+)/$', 'tweet.views.link'),
    url(r'^hashtags/$', 'tweet.views.hashtags'),
    url(r'^hashtag/(?P<hashtag>[^/]+)/$', 'tweet.views.hashtag'),
    url(r'^mentions/$', 'tweet.views.mentions'),
    url(r'^mentions/(?P<username>[^/]+)/$', 'tweet.views.user_mentions'),
    url(r'^update/$', 'tweet.views.update'),
    url(r'^crawl/(?P<username>[^/]+)/$', 'tweet.views.crawl'),
    #url(r'^extract_all_links/$', 'tweet.views.extract_all_links'),
    url(r'^expand_all_links/$', 'tweet.views.expand_all_links'),
    # url(r'^diablo3/', include('diablo3.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
