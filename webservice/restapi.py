import os
import urllib

import graph

from google.appengine.api import users

from google.appengine.ext.webapp import template

import logging
import webapp2
import json
import datetime

import ndbutils

from astar import Astar


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

def compute_graph(lat, lng, range_in_miles):
    """
    :type lat: float
    :type lng: float
    :type range_in_miles: float
    :return: GPS
    """
    drone_graph = graph.Graph(lat, lng, range_in_miles)
    return drone_graph

def jsonify_graph(drone_graph):
    """
    :type drone_graph: graph.Graph
    :return:
    """
    node_list = []
    for i, lst in enumerate(drone_graph.get_nodes()):
        node_list.append([])
        for node in lst:
            node_list[i].append(drone_graph.get_location(node))
    return node_list

def jsonify_route(route):
    loc_list = []
    for loc in route:
        new_loc = [loc.lat, loc.lng, loc.ele]
        loc_list.append(new_loc)
    return loc_list


class MainPage(webapp2.RequestHandler):
    
    def get(self):
        
        # delete all entities from NDB
        ndb.delete_multi(Drone.query().fetch(keys_only=True))


class InitializeGrid(webapp2.RequestHandler):

    def post(self):

        drone_name = self.request.get("drone_name")
        start_lat, start_lng = self.request.get("source").split(",")

        start_lat, start_lng = float(start_lat), float(start_lng)
        
        record = ndbutils.retrieve(drone_name)

        range_in_meters = record['range_in_meters']

        logging.debug('range_in_meters = {0}'.format(range_in_meters))

        drone_graph = compute_graph(start_lat, start_lng, range_in_meters*0.000621371)

        graph_start_node = drone_graph.get_approx_node(start_lat, start_lng)
        
        drone_record = {
            'drone_name' : drone_name,
            'update_time' : datetime.datetime.now(),
            'range_in_meters' : range_in_meters,
            'graph' : drone_graph,
            'graph_start_node' : graph_start_node
        }
        
        key = ndbutils.save(drone_name, drone_record)
        
        if key:
            logging.debug('Save succeeded, key = {0}'.format(key))
        else:
            logging.error('Save failed')
            abort(500)


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

        drone_record = {
            'drone_name' : drone_name,
            'update_time' : datetime.datetime.now(),
            'range_in_meters' : range_in_meters,
            'graph' : None,
            'graph_start_node' : None
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
        target_location = self.request.get('target').split(",")
        target_lat, target_lng = float(target_location[0]), float(target_location[1])

        drone_dict = ndbutils.retrieve(drone_name)
        drone_graph = drone_dict['graph']
        graph_start_node = drone_dict['graph_start_node']
        # print target_lat, target_lng
        graph_end_node = drone_graph.get_approx_node(target_lat, target_lng)

        route = Astar(graph_start_node, graph_end_node, drone_graph)
        
        organized_route = []

        # transform namedtuple route into json array of arrays

        for gps in route:
            coord = [gps.lat, gps.lng]
            organized_route.append(coord)

        response = {
            'route' : organized_route
        }

        self.response.out.write(json.dumps(response))



application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create', CreateDroneAndDisplayMap),
    ('/route', RouteDrone),
    #('/display', DisplayMap),
    ('/initialize', InitializeGrid)
], debug=True)

application.error_handlers[404] = handle_404
application.error_handlers[500] = handle_500
logging.getLogger().setLevel(logging.DEBUG)