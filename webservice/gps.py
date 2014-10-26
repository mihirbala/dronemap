__author__ = 'mihir'

import requests
from collections import namedtuple

GPS = namedtuple("GPS", ['lat', 'lng', 'ele'])

API_KEY = "AIzaSyBqTRpHolOOb5d5yC-gfnSY2zHhE1X4caA"

def get_gps(lat, lng, ele=None):
    """
    :param lat: float
    :param lng: float
    :param ele: float
    :return: GPS
    """
    if not ele:
        args = {
            "sensor": "false",
            "key": API_KEY,
            "locations": "{0},{1}".format(lat, lng)
        }
        result = requests.get("https://maps.googleapis.com/maps/api/elevation/json", params=args).json()
        ele =  result["results"][0]["elevation"]
    return GPS(lat, lng, ele)