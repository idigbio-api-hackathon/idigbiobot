from twitter import Twitter, TwitterStream, OAuth
import json
import idigbio
import os

idigbio_api = idigbio.json()

with open("../twitter.conf", "rb") as credf:
    creds = json.load(credf)

loc_pad = 0.01

auth = OAuth(
    creds["access_token"],
    creds["access_token_secret"],
    creds["consumer_key"],
    creds["consumer_secret"]
)

twitter = Twitter(auth=auth)

t_up = Twitter(domain='upload.twitter.com',
    auth=auth)

twitter_stream = TwitterStream(auth=auth, domain="userstream.twitter.com" )

for tweet in twitter_stream.user():
    # print msg

# with open("test.json", "rb") as testf:
#     tweet = json.load(testf)

    # print json.dumps(tweet,indent=2)

    if "place" in tweet and tweet["place"] is not None:
        print "Tweet From", tweet["user"]["screen_name"], tweet["place"]
        bb = tweet["place"]["bounding_box"]
        if bb["type"] == "Polygon":
            min_lat = 90
            max_lat = -90
            min_lon = 180
            max_lon = -180
            for c in bb["coordinates"][0]:
                lon, lat = c
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)
                min_lon = min(min_lon, lon)
                max_lon = max(max_lon, lon)

            loc_query = {
                "geopoint": {
                    "type": "geo_bounding_box",
                    "top_left": {
                        "lat": min(max_lat + loc_pad, 85.0510),
                        "lon": max(min_lon - loc_pad, -179.999)
                    },
                    "bottom_right": {
                        "lat": max(min_lat - loc_pad, -85.0510),
                        "lon": min(max_lon + loc_pad, 179.999)
                    }
                }
            }

            # print json.dumps(loc_query)
            m = idigbio_api.create_map(rq=loc_query, t="points")
            m.save_map_image(str(tweet['id']), zoom, bbox=loc_query["geopoint"])

            with open(str(tweet['id']) + ".png", "rb") as imagefile:
                imagedata = imagefile.read()

            img_id = t_up.media.upload(media=imagedata)["media_id_string"]

            twitter.statuses.update(
                status="Have a Map! @" + tweet["user"]["screen_name"] ,
                in_reply_to_status_id=tweet['id'],
                media_ids=img_id
            )
            os.unlink(str(tweet['id']) + ".png")
            print "Done"