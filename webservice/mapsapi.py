from google.appengine.api import urlfetch
import json
import logging

K1 = "AIzaSyBqTRpHolOOb5d5yC" # The two pieces of the API key
K2 = "gfnSY2zHhE1X4caA"
API_KEY = K1 + "-" + K2
URL = "https://maps.googleapis.com/maps/api/elevation/json?key=" + API_KEY + "&locations="
MAX_URL_LEN = 2000 # Max URL length to determine how many calls we can make in one dispatch

def get_multi_elevations(location_list):
    # Makes a bulk call to Google Maps elevation API to get the elevation value for
    # all locations in location_list in a single API call
    waypoint_list = []
    url = URL
    url_len = len(URL)
    # Denotes the first location in the list so that the string concatenation
    # places commas appropriately
    first_location = True

    for location in location_list:
        (lat, lng) = location
        location_str = "%f,%f" % (lat, lng)
        if first_location:
            first_location = False
        else:
            # Separate coordinate pairs in the request url
            location_str = "|" + location_str
        location_str_len = len(location_str)
        if url_len + location_str_len <= MAX_URL_LEN:
            # Makes sure that url_len has not exceeded the max url length
            url += location_str 
            url_len += location_str_len 
        else:
            # If url_len does exceed the max url length, dispatch the url to Google Maps
            # Elevation API
            result = urlfetch.fetch(url=url, headers={"Content-Type":"application/json"})
            result_dict = json.loads(result.content)
            if result_dict['status'] != 'OK':
                logging.error('URL Status is' + result_dict['status'])
                raise ValueError('API limit reached')
            for item in result_dict['results']:
                waypoint = (item['location']['lat'], item['location']['lng'], item['elevation'])
                waypoint_list.append(waypoint)
            # Reset the process to make another batch call
            location_str = "%f,%f" % (lat, lng) 
            url = URL + location_str
            url_len = len(URL)
            first_location = False

    if url_len > len(URL):
        # There are often some lat lng pairs left over because
        # the amount of pairs passed in does not divide evenly into the batch calls
        # (e.g. if each batch call takes 100 lat lng pairs and 101 pairs
        # are passed in, the last lat lng pair is left over).  In this case,
        # one more batch call needs to be made to get the left over pairs.
        result = urlfetch.fetch(url=url, headers={"Content-Type":"application/json"})
        result_dict = json.loads(result.content)
        if result_dict['status'] != 'OK':
            logging.error('URL Status is' + result_dict['status'])
            raise ValueError('API limit reached')
        for item in result_dict['results']:
            waypoint = (item['location']['lat'], item['location']['lng'], item['elevation'])
            logging.debug('{0}'.format(waypoint))
            waypoint_list.append(waypoint)

    return waypoint_list

def get_single_elevation(location):
    # Calls the Google Maps elevation API to get the elevation value
    # for a single location
    lat, lng = location[0], location[1]
    location_str = "%f,%f" % (lat, lng)
    url = URL + location_str
    result = urlfetch.fetch(url=url, headers={"Content-Type":"application/json"})
    result_dict = json.loads(result.content)
    if result_dict['status'] != 'OK':
        logging.error('URL Status is' + result_dict['status'])
        raise ValueError('API limit reached')
    assert len(result_dict['results']) == 1
    item = result_dict['results'][0]
    return item['elevation']
