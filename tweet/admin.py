from django.contrib import admin
from models import Tweet, Link, UserTweet, Hashtag

class TweetAdmin(admin.ModelAdmin):
    list_display = ('username', 'text', 'retweets', 'created_at', 'all_links', 'all_hashtags', 'all_user_mentions')
    filter_horizontal = ('links', 'hashtags', 'user_mentions')

admin.site.register(Tweet, TweetAdmin)
admin.site.register(Link)
admin.site.register(UserTweet)
admin.site.register(Hashtag)