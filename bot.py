from twitter import TwitterStream, OAuth
import json

with open("../twitter.conf","rb") as credf:
    creds = json.load(credf)

twitter_stream = TwitterStream(auth=OAuth(
        creds["access_token"],
        creds["access_token_secret"],
        creds["consumer_key"],
        creds["consumer_secret"]
    ),
    domain="userstream.twitter.com"
)

for msg in twitter_stream.user():
    print msg