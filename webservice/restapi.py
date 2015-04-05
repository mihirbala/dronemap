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

from dynastar import a_star_search


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


class MainPage(webapp2.RequestHandler):
    
    def get(self):   
        # Hack to reset NDB to prevent multiple copies of the same drone
        ndb.delete_multi(Drone.query().fetch(keys_only=True))


class CreateDroneAndDisplayMap(webapp2.RequestHandler):

    def get(self):

        drone_name = str(self.request.get('drone_name'))

        range_in_kilometers = str(self.request.get('range_in_kilometers'))

        template_values = {
            'range_in_meters' : range_in_kilometers*1000,
            'drone_name' : drone_name
        }

        path = os.path.join(os.path.dirname(__file__), 'directions.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):

        drone_name = self.request.get('drone_name')
        range_in_meters = int(self.request.get('range_in_kilometers'))*1000
        googlemaps_api_key = self.request.get('googlemaps_api_key')

        drone_record = {
            'drone_name' : drone_name,
            'update_time' : datetime.datetime.now(),
            'range_in_meters' : range_in_meters
        }
            
        key = ndbutils.save(drone_name, drone_record)
            
        if key:
            logging.debug('Successfully created drone, key = {0}'.format(key))
            template_values = {
                'range_in_meters' : range_in_meters,
                'drone_name' : drone_name
            }
            path = os.path.join(os.path.dirname(__file__), 'directions.html')
            self.response.out.write(template.render(path, template_values))
        else:
            logging.error('Creation of drone failed')
            abort(500)


class RouteDrone(webapp2.RequestHandler):

    def get(self):

        drone_name = str(self.request.get('drone_name'))

        drone_record = ndbutils.retrieve(drone_name)

        range_in_meters = drone_record['range_in_meters']

        source_coords = self.request.get('source').split(",")
        source_lat, source_lng = float(source_coords[0]), float(source_coords[1])
        source_location = (round(source_lat,6), round(source_lng,6))

        target_coords = self.request.get('target').split(",")
        target_lat, target_lng = float(target_coords[0]), float(target_coords[1])
        target_location = (round(target_lat,6), round(target_lng,6))

        route, cost_grid = a_star_search(source_location, target_location)

        response = {
            'route' : route,
            'gpx_route' : compute_gpx_route(route)
        }

        # TODO: save gpx route to NDB
        #print '====='
        #print response['gpx_route']
        #print '====='

        self.response.out.write(json.dumps(response))


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create', CreateDroneAndDisplayMap),
    ('/route', RouteDrone),
], debug=True)

application.error_handlers[404] = handle_404
application.error_handlers[500] = handle_500
logging.getLogger().setLevel(logging.DEBUG)