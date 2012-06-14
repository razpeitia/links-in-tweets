from django.contrib import admin
from models import Tweet, Link, UserTweet

class TweetAdmin(admin.ModelAdmin):
    list_display = ('username', 'text', 'retweets', 'created_at', 'all_links')

admin.site.register(Tweet, TweetAdmin)
admin.site.register(Link)
admin.site.register(UserTweet)