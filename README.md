links-in-tweets
===============

How does this works?

1. Sync the database
    `python manage.py syncdb`


2. Run the web server

    `python manage.py runserver`


3. Crawl the user since some specific date.

    /crawl/:username/:year/:month/:day


4. Extract all the links in the tweets.

    /extract_all_links/


5. Expand all the links.

    /expand_all_links/
