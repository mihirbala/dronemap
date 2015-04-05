__author__ = 'mihir'

import collections
import heapq
import random
import mapsapi
from haversine import haversine

NEIGHBOR_DISTANCE = 0.5 # Distance any pair of neighbors in km
PRECISION = 6 # Decimal places for lat lng values

# The lattitude and longitude bounds of the grid
Limit = collections.namedtuple('limit', ['upper', 'lower'])
# Neighbor distance in lat/lng units
Resolution = collections.namedtuple('resolution', ['lat', 'lng'])

class GridWithCosts:
    # Lazily computes a grid of locations ((lat,lng,ele) tuples)

    googlemaps_api_counter = 0 # Counts API requests to google maps 
    
    def __init__(self, lat_limit, lng_limit, resolution):
        self.lat_limit = lat_limit # Lattitude bounds
        self.lng_limit = lng_limit # Longitude bounds
        self.resolution = resolution # Resolution as defined above
        self.location_cost_map = {} # Map of (lat,lng) to elevation
    
    def cost(self, location_a, location_b):
        # The cost of travelling from location a to b
        location_a_cost, location_b_cost = \
            self.get_elevation(location_a), self.get_elevation(location_b)
        return abs(location_a_cost - location_b_cost)

    def in_bounds(self, location):
        # Checks if the location is in the lattitude and longitude bounds
        (lat, lng) = location
        return self.lat_limit.lower <= lat < self.lat_limit.upper \
            and self.lng_limit.lower <= lng < self.lng_limit.upper
    
    def round(self, location):
        # Rounds a given location (lat,lng) to PRECISION
        (lat, lng) = location
        return (round(lat, PRECISION), round(lng, PRECISION))

    def neighbors(self, location):
        # Finds the neighbors around given location
        (lat, lng) = location
        results = [(lat+self.resolution.lat, lng), (lat, lng-self.resolution.lng), 
                (lat-self.resolution.lat, lng), (lat, lng+self.resolution.lng)]
        results = filter(self.in_bounds, results) # Check if neighbors are in bounds
        results = map(self.round, results) # Round all neighbors to PRECISION
        # Set the elevation value for all neighbors from google maps API
        self.set_elevation(results)
        return results

    def set_elevation(self, location_list):
        # Set the elevation value for all locations in location_list that
        # don't already have this value set
        request_list = []
        for location in location_list:
            if location not in self.location_cost_map: 
                request_list.append(location)
        if len(request_list) > 0:
            request_list_with_ele = mapsapi.get_multi_elevations(request_list)
            self.googlemaps_api_counter += 1
            print 'Google maps API call ', self.googlemaps_api_counter, ' ', location
            for location in request_list_with_ele:
                self.location_cost_map[(location[0], location[1])] = location[2]

    def get_elevation(self, location):
        # Get the elevation value for a single location
        if location in self.location_cost_map:
            return self.location_cost_map[location]
        else:
            self.googlemaps_api_counter += 1
            print 'Google maps API call ', self.googlemaps_api_counter, ' ', location
            elevation = mapsapi.get_single_elevation(location)
            self.location_cost_map[location] = elevation
            return elevation

class PriorityQueue:
    # Implements a Priority Queue of locations ordered 
    # by lowest to highest cost

    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self):
        return heapq.heappop(self.elements)[1]

def reconstruct_path(graph, came_from, start, goal):
    # Reconstruct the path from the came_from dict, and in the process
    # convert the (lat, lng) tuples to (lat, lng, elevation) waypoints
    current = goal
    waypoint = (current[0], current[1], graph.get_elevation(current))
    path = [waypoint]
    while current != start:
        current = came_from[current]
        waypoint = (current[0], current[1], graph.get_elevation(current))
        path.append(waypoint)
    return path

def reached_goal(current, goal, resolution):
    # In case the goal does not align with the grid, this function
    # checks if it is within a neighbor distance of current location
    if abs(current[0] - goal[0]) <= resolution.lat \
        and abs(current[1] - goal[1]) <= resolution.lng:
        return True
    return False

def get_limits(start, goal):
    # Computes the lattitude and longitude bounds and resolution
    # in lat lng units
    lat_origin, lng_origin = start[:]
    # Find the distance between the start and goal location using
    # Haversine Formula, determines distance between any two points on earth.
    # This accounts for the spherical nature of earth which causes the
    # distance between longitude points to vary between the poles and
    # the equator
    start_goal_dist = haversine(start, goal) 

    # Find the diff between two lat lines at this lng
    lat_diff = haversine((1, lng_origin), (2, lng_origin)) 
    upper_lat = lat_origin + (start_goal_dist/lat_diff)
    lower_lat = lat_origin - (start_goal_dist/lat_diff)
    # Compute the upper & lower lattitude bounds
    lat_limit = Limit(round(upper_lat,PRECISION), round(lower_lat,PRECISION))

    # Find the diff between two lng lines at this lat
    lng_diff = haversine((lat_origin, 1), (lat_origin, 2)) 
    upper_lng = lng_origin + (start_goal_dist/lng_diff)
    lower_lng = lng_origin - (start_goal_dist/lng_diff)
    # Compute the upper & lower longtitude bounds
    lng_limit = Limit(round(upper_lng,PRECISION), round(lower_lng,PRECISION))

    lat_resolution = NEIGHBOR_DISTANCE/lat_diff # 1.0km as lat and lng resolution
    lng_resolution = NEIGHBOR_DISTANCE/lng_diff
    resolution = Resolution(lat_resolution, lng_resolution)

    print lat_limit, lng_limit
    return lat_limit, lng_limit, resolution

def heuristic(location_a, location_b):
    # Finds the approximate cost of travelling between
    # locations a and b
    (lat1, lng1) = location_a
    (lat2, lng2) = location_b
    return abs(lat1 - lat2) + abs(lng1 - lng2)

def a_star_search(start, goal):
    # Applies a modified A* algorithm to compute the most
    # efficient route from start to goal location.
    # This modification is based on Amit's A* implementation 
    # [http://theory.stanford.edu/~amitp/GameProgramming/],
    # with the following changes:
    #   - Changed cost function to invoke google maps API for elevation data
    #   - Initialized graph with lattitude and longitude bounds
    #   - Used Haversine Formula to get accurate inter-neighbor distances
    #   - Added a reached_goal function to terminate the search when in range
    #     of goal
    #   - Changed grid template from 4 sided square to 6 sided hexagon for
    #     smoother paths (less zig-zagging)
    #   - 
    lat_limit, lng_limit, resolution = get_limits(start, goal)

    graph = GridWithCosts(lat_limit, lng_limit, resolution)

    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    
    while not frontier.empty():
        current = frontier.get()
        
        if reached_goal(current, goal, resolution):
            came_from[goal] = current
            print 'Reached Goal ', current
            print 'start = ', start
            print 'goal = ', goal
            break
        
        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current
    
    return reconstruct_path(graph, came_from, start, goal), cost_so_far
