import simplejson as json
import urllib
from haversine import haversine
import webbrowser
import random

ELEVATION_API_BASE_URL = 'https://maps.googleapis.com/maps/api/elevation/json'
CHARTS_API_BASE_URL = 'http://chart.apis.google.com/chart'
NEIGHBOR_DISTANCE = 0.1 #km


def display_elevation_chart(waypoints, show_points=False):
  """
  Use the Google Charts API to draw an elevation chart of the list of waypoints.
  Set show_points to True to see each data point on the elevation chart.
  """

  assert len(waypoints) > 1
  start, end = (waypoints[0], waypoints[-1])
  start_location = (start['lat'], start['lng'])
  end_location = (end['lat'], end['lng'])
  distance_in_km = haversine.haversine(start_location, end_location)

  elevation_data = []
  elevation_total = 0
  for waypoint in waypoints:
    elevation = waypoint['ele']
    elevation_data.append(elevation)
    elevation_total += elevation

  chart_data = 't:' + ','.join(str(x) for x in elevation_data)
  avg_elevation = elevation_total / len(waypoints)

  chart_args = {
    'cht': 'lc', # chart type
    'chs': '800x160', # chart size
    'chco': '0000FF', # series color
    'chds': 'a', # chart data scale
    'chxt': 'x,x,y,y',
    'chxr': '0,%d,%d' % (0, int(distance_in_km)), # x axis labels
    'chxl': '1:|Distance (Km)|3:|Elevation (m)|',
    'chxp': '1,50|3,%d' % int(avg_elevation)
  }

  chart_args['chd'] = chart_data
  if show_points:
    chart_args['chm'] = 'o,000000,0,-1,3'

  chart_url = CHARTS_API_BASE_URL + '?' + urllib.urlencode(chart_args)

  # display the chart in a browser tab
  webbrowser.open_new_tab(chart_url)

def get_demo_data(start, range_in_kilometers, samples):
    lat_origin, lng_origin = start[:]

    # Find the diff between two lat lines at this lng
    lat_diff = haversine((1, lng_origin), (2, lng_origin)) 
    upper_lat = lat_origin + (range_in_kilometers/lat_diff)
    lower_lat = lat_origin - (range_in_kilometers/lat_diff)

    # Find the diff between two lng lines at this lat
    lng_diff = haversine((lat_origin, 1), (lat_origin, 2)) 
    upper_lng = lng_origin + (range_in_kilometers/lng_diff)
    lower_lng = lng_origin - (range_in_kilometers/lng_diff)

    assert lower_lat < upper_lat
    assert lower_lng < upper_lng

    lat_resolution = (haversine((lower_lat, lower_lng), (upper_lat, lower_lng))/samples)/lat_diff
    lng_resolution = (haversine((lower_lat, lower_lng), (lower_lat, upper_lng))/samples)/lng_diff

    # A two dimensional array of waypoints; grid is in increasing order of lat and lng
    grid = [] 

    lat = lower_lat
    while lat <= upper_lat:
      row = get_waypoints_for_path((lat, lower_lng), (lat, upper_lng), samples)
      grid.append(row)
      lat += lat_resolution

    demo_data = {
      'start_location' : start,
      'lat_limit' : [lower_lat, upper_lat],
      'lng_limit' : [lower_lng, upper_lng],
      'resolution' : [lat_resolution, lng_resolution],
      'grid' : grid
    }

    return demo_data

def get_waypoints_for_path(startLocation, endLocation, samples, precision=4):
  """
  Use the Google Maps Elevation API to get the elevation data for
  'samples' evenly spaced points on the path between 'start' and 'end'
  locations. Return the result as a list of waypoints, where each waypoint
  is a tuple with 'lat', 'lng', 'ele' and 'resolution'. 'resolution' is
  the error in the elevation data - any location within a 'resolution' diameter
  (in meters) of the location will have the same 'elevation' value.
  """

  start = "%s,%s" % startLocation
  end = "%s,%s" % endLocation
  path = start + "|" + end

  api_args = {
    'path': path,
    'samples': samples
  }

  url = ELEVATION_API_BASE_URL + '?' + urllib.urlencode(api_args)
  response = json.load(urllib.urlopen(url))

  status = response['status']

  if status == 'OK':
    waypoints = []
    for item in response['results']:
      lat = round(item['location']['lat'], precision)
      lng = round(item['location']['lng'], precision)
      ele = round(item['elevation'], precision)
      # resolution key may not be present in returned data if it is
      # not known, so use the value -1.0 as the default if its missing
      resolution = round(item.get('resolution', -1.0), precision)
      waypoint = (lat, lng, ele, resolution)
      waypoints.append(waypoint)
    return waypoints
  else:
    raise ValueError(status)


# Test from command line
if __name__ == '__main__':
  start_location = (-13.391182, -72.528585)
  end_location = (-13.111240, -72.370674)
  samples = 100
  range_in_kilometers = 5

  demo_data = get_demo_data(start_location, range_in_kilometers, samples)
  assert len(demo_data['grid']) <= (samples+1)

  with open('demo_data.json', 'w') as fp:
    json.dump(demo_data, fp, indent=2)
  #display_elevation_chart(waypoints)
