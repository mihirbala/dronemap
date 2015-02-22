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
        
        pass

class CreateDrone(webapp2.RequestHandler):

    def post(self):

        body = {
            'name' : self.request.get('name'),
            'range_in_miles' : self.request.get('range_in_miles'),
            'start_location' : self.request.get('start_location').split(',')
        }

        # body = json.loads(self.request.body)
        drone_name = body['name']

        if 'range_in_miles' not in body or 'start_location' not in body:
            logging.error('range_in_miles = {0}, start_location = {1}'.format(range_in_miles, start_location))
            abort(400)
        else:
            range_in_miles = int(body['range_in_miles'])
            lat, lng = body['start_location']
            start_lat, start_lng = float(lat), float(lng)
            drone_dict = ndbutils.retrieve(drone_name)
            if drone_dict and drone_dict['range_in_miles'] == range_in_miles:
                logging.debug('Found drone {0}'.format(drone_name))
                drone_graph = drone_dict['graph']
                creation_time = drone_dict['creation_time']
                graph_start_node = drone_dict['graph_start_node']
            else:
                logging.debug('Creating new drone {0}'.format(drone_name))
                creation_time = datetime.datetime.now()
                drone_graph = compute_graph(start_lat, start_lng, range_in_miles)
                graph_start_node = drone_graph.get_approx_node(start_lat, start_lng)

            
            drone_record = {
                'name' : drone_name,
                'creation_time' : creation_time,
                'range_in_miles' : range_in_miles,
                'graph' : drone_graph,
                'graph_start_node' : graph_start_node
            }
            
            key = ndbutils.save(drone_name, drone_record)
            
            if key:
                logging.debug('Save succeeded, key = {0}'.format(key))
            else:
                logging.error('Save failed')
                abort(500)

            record = ndbutils.retrieve(drone_name)

            response = {
                'success' : True,
                'name' : record['name'],
                'creation_time' : record['creation_time'].isoformat(),
                'range_in_miles' : record['range_in_miles'],
                'start_location' : drone_graph.get_location(record['graph_start_node']),
                'graph' : jsonify_graph(record['graph'])
            }

            range_in_meters = drone_dict['range_in_miles']*1609.34

            template_values = {
                'lat' : drone_dict['graph_start_node'].lat,
                'lng' : drone_dict['graph_start_node'].lng,
                'range' : range_in_meters,
                'name' : drone_dict['name'],
            }

            #self.response.headers['Content-Type'] = 'application/json'   
            #self.response.out.write(json.dumps(response, indent=2))
            path = os.path.join(os.path.dirname(__file__), 'directions.html')
            self.response.out.write(template.render(path, template_values))


class RouteDrone(webapp2.RequestHandler):

    def get(self):

        drone_name = str(self.request.get('name'))
        target_location = self.request.get('target_location').split(",")
        target_lat, target_lng = float(target_location[0]), float(target_location[1])

        drone_dict = ndbutils.retrieve(drone_name)
        drone_graph = drone_dict['graph']
        graph_start_node = drone_dict['graph_start_node']
        response = {
            'success' : True, 
            'name' : drone_dict['name'],
            'range_in_miles' : drone_dict['range_in_miles'],
            'start_location' : drone_graph.get_location(graph_start_node)
        }

        if target_lat <= drone_graph.lat_upper_limit and target_lat >= drone_graph.lat_lower_limit \
                and target_lng <= drone_graph.lng_upper_limit and target_lng >= drone_graph.lng_lower_limit:
            graph_end_node = drone_graph.get_approx_node(target_lat, target_lng)
            route = Astar(graph_start_node, graph_end_node, drone_graph)
            response['adjusted_end_location'] = drone_graph.get_location(graph_end_node)
            route_request_time = datetime.datetime.now()
            response['route_request_time'] = route_request_time.isoformat()
            response['computed_route'] = jsonify_route(route)
            
            range_in_meters = drone_dict['range_in_miles']*1609.34

            organized_route = []

            for gps in route:
                coord = [gps.lat, gps.lng]
                organized_route.append(coord)

            template_values = {
                'route' : organized_route,
                'lat' : drone_dict['graph_start_node'].lat,
                'lng' : drone_dict['graph_start_node'].lng,
                'range' : range_in_meters,
                'name' : drone_dict['name'],
                'last_node' : route[(len(route)-1)]
            }
            

            self.response.out.write(json.dumps(template_values))

        else:
            # target_lat, target_lng does not fall within drone_graph boundary, so return error
            response = {
                'success' : False,
                'error_message' : 'Target coordinates {0}, {1} out of drone range brounds.'.format(target_lat, target_lng),
                'drone_range_bounds' : {
                    'lat_lower_limit' : drone_graph.lat_lower_limit,
                    'lat_upper_limit' : drone_graph.lat_upper_limit,
                    'lng_lower_limit' : drone_graph.lng_lower_limit,
                    'lng_upper_limit' : drone_graph.lng_upper_limit
                }
            }

            self.response.headers['Content-Type'] = 'application/json'     
            self.response.out.write(json.dumps(response, indent=2))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create', CreateDrone),
    ('/route', RouteDrone),
], debug=True)

application.error_handlers[404] = handle_404
application.error_handlers[500] = handle_500
logging.getLogger().setLevel(logging.DEBUG)