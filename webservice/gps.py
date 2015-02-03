from google.appengine.api import urlfetch
from collections import namedtuple
import json
import logging

GPS = namedtuple("GPS", ['lat', 'lng', 'ele'])
K1 = "AIzaSyBqTRpHolOOb5d5yC"
K2 = "gfnSY2zHhE1X4caA"
API_KEY = K1 + "-" + K2
URL = "https://maps.googleapis.com/maps/api/elevation/json?key=" + API_KEY + "&locations="
MAX_URL_LEN = 2000

def get_gps(locations):
    """
    :param locations: list
    :return: list
    """

    gps_locations = []
    url = URL
    url_len = len(URL)
    first_node = True

    for node in locations:
        lat, lng = node[0], node[1]
        node_str = "%f,%f" % (lat, lng)
        if first_node:
            first_node = False
        else:
            node_str = "|" + node_str
        node_str_len = len(node_str)
        if url_len + node_str_len <= MAX_URL_LEN:
            url += node_str
            url_len += node_str_len
        else:
            # print url
            result = urlfetch.fetch(url=url, headers={"Content-Type":"application/json"})
            result_dict = json.loads(result.content)
            if result_dict['status'] != 'OK':
                app.logger.error('URL Status is' + result_dict['status'])
            for item in result_dict['results']:
                gps = GPS(item['location']['lat'], item['location']['lng'], item['elevation'])
                gps_locations.append(gps)
            node_str = "%f,%f" % (lat, lng)
            url = URL + node_str
            url_len = len(URL)
            first_node = False

    if url_len > len(URL):
        # still need to make one more call
        result = urlfetch.fetch(url=url, headers={"Content-Type":"application/json"})
        result_dict = json.loads(result.content)
        if result_dict['status'] != 'OK':
            app.logger.error('URL Status is' + result_dict['status'])
        for item in result_dict['results']:
            gps = GPS(item['location']['lat'], item['location']['lng'], item['elevation'])
            logging.debug('{0}'.format(gps))
            gps_locations.append(gps)

    return gps_locations