from twitter import Twitter, TwitterStream, OAuth
import json
import idigbio

import math

TILES_WIDE = 4

def level_dic():
    '''
    http://wiki.openstreetmap.org/wiki/Zoom_levels
    '''
    # return data
    data = {0: 360.0,
            1: 180.0,
            2: 90.0,
            3: 45.0,
            4: 22.5,
            5: 11.25,
            6: 5.625,
            7: 2.813,
            8: 1.406,
            9: 0.703,
            10: 0.352,
            11: 0.176,
            12: 0.088,
            13: 0.044,
            14: 0.022,
            15: 0.011,
            16: 0.005,
            17: 0.003,
            18: 0.001,
            19: 0.0005}
    return data

def getzoom(min_lon, max_lon, min_lat, max_lat):
    data = level_dic()  # our presets
    r = 4
    dne = max(round(max_lat - min_lat, r),round(max_lon - min_lon, r))  # ne: North East point
    mylist = [round(i, r) for i in data.values()] + [dne]
    new = sorted(mylist, reverse=True)
    return new.index(dne)


def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

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

    if "place" in tweet:
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

            zoom = getzoom(
                loc_query["geopoint"]["bottom_right"]["lat"],
                loc_query["geopoint"]["top_left"]["lat"],
                loc_query["geopoint"]["top_left"]["lon"],
                loc_query["geopoint"]["bottom_right"]["lon"]
            )

            top_left_tile = deg2num(
                loc_query["geopoint"]["top_left"]["lat"],
                loc_query["geopoint"]["top_left"]["lon"],
                zoom
            )

            bottom_right_tile = deg2num(
                loc_query["geopoint"]["bottom_right"]["lat"],
                loc_query["geopoint"]["bottom_right"]["lon"],
                zoom
            )

            tiles = [
                range(top_left_tile[0],bottom_right_tile[0]+1),
                range(top_left_tile[1],bottom_right_tile[1]+1)
            ]

            # print json.dumps(loc_query)
            m = idigbio_api.create_map(rq=loc_query, t="auto")
            m.save_map_image(str(tweet['id']), zoom, x_tiles=tiles[0], y_tiles=tiles[1])

            with open(str(tweet['id']) + ".png", "rb") as imagefile:
                imagedata = imagefile.read()

            img_id = t_up.media.upload(media=imagedata)["media_id_string"]

            twitter.statuses.update(
                status="Have a Map! @" + tweet["user"]["screen_name"] ,
                in_reply_to_status_id=tweet['id'],
                media_ids=img_id
            )
            print "Done"