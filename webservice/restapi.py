import os
import urllib

from google.appengine.api import users
from google.appengine.ext.webapp import template
import ndbutils
import webapp2

import logging
import json
import datetime

import gpxpy
import gpxpy.gpx

from dynastar import a_star_search, Limit, Resolution

PRECISION = 6

def handle_404(request, response, exception):
    logging.exception(exception)
    response.write('Page not found.')
    response.set_status(404)

def handle_400(request, response, exception):
    logging.exception(exception)
    response.write('Incorrect parameters.')
    response.set_status(400)

def handle_500(request, response, exception):
    logging.exception(exception)
    response.write('A server error occurred!')
    response.set_status(500)



def compute_gpx_route(route):
    # Converts route of waypoints into GPX format
    gpx = gpxpy.gpx.GPX()

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    for location in route:
        (lat, lng, ele) = location
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lng, elevation=ele))
    
    return gpx.to_xml()

def get_demo_info():
    with open('demo_data.rockies.json', 'r') as infile:
        demo_data = json.load(infile)

    lat_limit = Limit(demo_data['lat_limit'][1], demo_data['lat_limit'][0])
    lng_limit = Limit(demo_data['lng_limit'][1], demo_data['lng_limit'][0])
    resolution = Resolution(*demo_data['resolution'])
    range_in_kilometers = demo_data['range_in_kilometers']
    start_location = tuple(demo_data['start_location'])
    
    location_cost_map = {}
    for row in demo_data['grid']:
        for point in row:
            location_cost_map[(point[0], point[1])] = point[2]

    assert start_location in location_cost_map
    return (lat_limit, lng_limit, resolution, location_cost_map, 
            range_in_kilometers, start_location)


class MainPage(webapp2.RequestHandler):
    
    def get(self):   
        # Hack to reset NDB to prevent multiple copies of the same drone
        ndb.delete_multi(Drone.query().fetch(keys_only=True))


class CreateDroneAndDisplayMap(webapp2.RequestHandler):

    def get(self):
        # Hand of the drone parameters from the request to the map
        drone_name = str(self.request.get('drone_name'))

        range_in_kilometers = str(self.request.get('range_in_kilometers'))

        template_values = {
            'range_in_kilometers' : range_in_kilometers,
            'drone_name' : drone_name
        }

        path = os.path.join(os.path.dirname(__file__), 'directions.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        # Get drone parameters from the index.html web form and save them
        # in NDB
        drone_name = self.request.get('drone_name')
        range_in_kilometers = int(self.request.get('range_in_kilometers'))
        # TODO: store individual API keys for each user along with their drones
        googlemaps_api_key = self.request.get('googlemaps_api_key')

        drone_record = {
            'drone_name' : drone_name,
            'update_time' : datetime.datetime.now(),
            'range_in_kilometers' : range_in_kilometers,
            'location_cost_map' : {}
        }
            
        key = ndbutils.save(drone_name, drone_record)
            
        if key:
            logging.debug('Successfully created drone, key = {0}'.format(key))
            template_values = {
                'range_in_kilometers' : range_in_kilometers,
                'drone_name' : drone_name
            }
            path = os.path.join(os.path.dirname(__file__), 'directions.html')
            self.response.out.write(template.render(path, template_values))
        else:
            logging.error('Creation of drone failed')
            abort(500)


class RouteDrone(webapp2.RequestHandler):

    def get(self):
        # Get the source and target locations from directions.html and
        # invoke A* to calculate the route
        drone_name = str(self.request.get('drone_name'))

        drone_record = ndbutils.retrieve(drone_name)

        range_in_kilometers = drone_record['range_in_kilometers']

        location_cost_map = drone_record['location_cost_map']

        source_coords = self.request.get('source').split(",")
        source_lat, source_lng = float(source_coords[0]), float(source_coords[1])
        source_location = (round(source_lat,PRECISION), round(source_lng,PRECISION))

        target_coords = self.request.get('target').split(",")
        target_lat, target_lng = float(target_coords[0]), float(target_coords[1])
        target_location = (round(target_lat,PRECISION), round(target_lng,PRECISION))

        route, cost_grid, location_cost_map = a_star_search(source_location, target_location, range_in_kilometers, location_cost_map)

        new_drone_record = {
            'drone_name' : drone_name,
            'update_time' : datetime.datetime.now(),
            'range_in_kilometers' : range_in_kilometers,
            'location_cost_map' : location_cost_map
        }
            
        key = ndbutils.save(drone_name, new_drone_record)

        response = {
            'route' : route,
            'gpx_route' : compute_gpx_route(route)
        }

        # TODO: save gpx route to NDB
        #print '====='
        #print response['gpx_route']
        #print '====='

        self.response.out.write(json.dumps(response))

class Demo(webapp2.RequestHandler):

    def get(self):

        target_coords = self.request.get('target').split(",")
        target_lat, target_lng = float(target_coords[0]), float(target_coords[1])
        target_location = (round(target_lat,PRECISION), round(target_lng,PRECISION))

        (lat_limit, lng_limit, resolution, 
            location_cost_map, range_in_kilometers, start_location) = get_demo_info()

        demo_info = {
            'lat_limit' : lat_limit,
            'lng_limit' : lng_limit,
            'resolution' : resolution,
        }

        route, cost_grid, cost_map = a_star_search(start_location, target_location, 
                                                    range_in_kilometers, location_cost_map, demo_info)

        response = {
            'route' : route,
            'gpx_route' : compute_gpx_route(route)
        }

        self.response.out.write(json.dumps(response))



application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create', CreateDroneAndDisplayMap),
    ('/route', RouteDrone),
    ('/demo', Demo)
], debug=True)

application.error_handlers[404] = handle_404
application.error_handlers[500] = handle_500
logging.getLogger().setLevel(logging.DEBUG)