__author__ = 'mihir'

import os
import flask
from flask import request, json
import pickle
import gps
import graph
import atexit
from astar import Astar

droneDB_path = './droneDB' # this is a pickled dictionary saved to disk
if os.path.exists(droneDB_path):
    droneDB = pickle.load(open(droneDB_path, 'r'))
else:
    droneDB = {}

app = flask.Flask(__name__)

def clean_up():
    pass

def compute_graph(lat, lng, range_in_miles):
    """
    :type lat: float
    :type lng: float
    :type range_in_miles: float
    :return: GPS
    """
    G = graph.Graph(lat, lng, range_in_miles)
    return G

def jsonify_route(route):
    loc_list = []
    for loc in route:
        new_loc = [loc.lat, loc.lng, loc.ele]
        loc_list.append(new_loc)
    return loc_list

def jsonify_graph(G):
    """
    :type G: graph.Graph
    :return:
    """
    node_list = []
    for i,lst in enumerate(G.get_nodes()):
        node_list.append([])
        for node in lst:
            # app.logger.info(G.print_node(node))
            node_list[i].append([node.lat, node.lng, node.ele])
    return node_list

@app.route('/')
def api_help():
    return "PUT /drones/(name) - creates a new drone, or modifies an existing one\n" \
    + "  body is a JSON with required keys: 'range' (drone range in miles)\n" \
    + "  'location' (starting location as a lat, lng list)\n\n "\
    + "  GET /drones/(name)/route?dest=lat,lng - returns a route from the start location to the destination"

@app.route('/drones/<drone>', methods=['PUT'])
def create_drone(drone):
    body = json.loads(request.data)
    if 'range' not in body or 'location' not in body:
        return api_help()

    else:
        range_in_miles = int(body['range'])
        lat,lng = body['location']
        if drone in droneDB and droneDB[drone]['range'] == range_in_miles:
            G = droneDB[drone]['graph']
        else:
            app.logger.info('computing graph')
            G = compute_graph(lat, lng, range_in_miles)
        droneDB[drone] = {
            'name' : drone,
            'range' : range_in_miles,
            'start_location' : gps.get_gps(lat, lng),
            'graph' : G
        }
        # save droneDB back to its pickled file
        pickle.dump(droneDB, open(droneDB_path, 'wb'))

        loc = droneDB[drone]['start_location']
        response = {
            'name' : droneDB[drone]['name'],
            'range' : droneDB[drone]['range'],
            'start_location' : [loc.lat, loc.lng, loc.ele],
            'graph' : jsonify_graph(G)
        }

        return flask.jsonify(response)

@app.route('/drones/<drone>', methods=['GET'])
def get_drone_info(drone):
    loc = droneDB[drone]['start_location']
    response = {
        'name' : droneDB[drone]['name'],
        'range' : droneDB[drone]['range'],
        'start_location' : [loc.lat, loc.lng, loc.ele]
    }
    args = flask.request.args
    if 'action' in args:
        if args['action'] == 'route':
            lat,lng = args['target'].split(',')
            if lat < droneDB[drone]['graph'].lat_limit and lng < droneDB[drone]['graph'].lng_limit:
                target_location = gps.get_gps(float(droneDB[drone]['graph'].get_approx_lat(lat)), float(droneDB[drone]['graph'].get_approx_lng(lng)))
                route = Astar(droneDB[drone]['start_location'], target_location, droneDB[drone]['graph'])
                response['route'] = jsonify_route(route)
            else:
                error = {'Error' : 'Lat and Lng coordinates not in drone range.'}
                response = flask.jsonify(error)
    else:
        # print out graph
        response['graph'] = jsonify_graph(droneDB[drone]['graph'])

    return flask.jsonify(response)


if __name__ == "__main__":
    atexit.register(clean_up)
    app.run(debug=True)
