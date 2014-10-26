__author__ = "mihir"

import math
import gps

class Graph:
    
    def dummy(self, upper_right, lower_left, resolution=1):
        """
        :type upper_right: tuple
        :type lower_left: tuple
        :type resolution: int
        :return:
        """
        self.nodes = set()
        self.edges = []
        self.node_edge_map = {}

        ROWS = int(math.floor((upper_right[0] - lower_left[0])/resolution))
        COLUMNS = int(math.floor((upper_right[1] - lower_left[1])/resolution))

        grid = [[None for i in range(COLUMNS)] for j in range(ROWS)]
        # fill in the grid

        for i in range(ROWS):
            for j in range(COLUMNS):
                lat = lower_left[0] + resolution*i
                lng = lower_left[1] + resolution*j
                grid[i][j] = gps.get_gps(lat, lng)

        for i in range(ROWS):
            for node in grid[i]:
                self.add_node(node)

        for i in range(ROWS):
            for j in range(COLUMNS):
                if j > 0:  # has a left neighbor
                    self.add_edge(grid[i][j], grid[i][j - 1])
                if j < COLUMNS - 1:  # has right neighbor
                    self.add_edge(grid[i][j], grid[i][j + 1])
                if i > 0:  # has top neighbor
                    self.add_edge(grid[i][j], grid[i - 1][j])
                if i < ROWS - 1:  # has bottom neighbor
                    self.add_edge(grid[i][j], grid[i + 1][j])
                if j > 0 and i > 0:  # has top left neighbor
                    self.add_edge(grid[i][j], grid[i - 1][j - 1])
                if j < COLUMNS - 1 and i > 0:  # has top right neighbor
                    self.add_edge(grid[i][j], grid[i - 1][j + 1])
                if j > 0 and i < ROWS - 1:  # has bottom left neighbor
                    self.add_edge(grid[i][j], grid[i + 1][j - 1])
                if j < COLUMNS - 1 and i < ROWS - 1:  # has bottom right neighbor
                    self.add_edge(grid[i][j], grid[i + 1][j + 1])


    def __init__(self, lat_origin, lng_origin, range_in_miles, gps_increment=0.2):
        """
        :type lat_origin: float
        :type lng_origin: float
        :type range_in_miles: float
        :type gps_increment: float
        :return:
        """
        self.nodes = set()
        self.edges = []
        self.node_edge_map = {}
        self.RESOLUTION = 69.2
        self.gps_increment = gps_increment
        self.grid = []

        self.lat_limit = lat_origin + (range_in_miles/self.RESOLUTION)
        #TODO change lng_range conversion to be dependent on latitude
        self.lng_limit = lng_origin + (range_in_miles/self.RESOLUTION)
        # start lat and lng at bottom left corner of grid
        lat, lng = lat_origin - (range_in_miles/self.RESOLUTION), lng_origin - (range_in_miles/self.RESOLUTION)

        # add all nodes
        i = 0
        while lat < self.lat_limit:
            self.grid.append([])
            lng = lng_origin
            while lng < self.lng_limit:
                node = gps.get_gps(lat, lng)
                self.add_node(node)
                self.grid[i].append(node)
                lng += gps_increment
            lat += gps_increment
            i += 1

        ROWS, COLUMNS = len(self.grid), len(self.grid[0])
        print ROWS, COLUMNS

        # add all edges
        lat, lng = lat_origin - (range_in_miles/self.RESOLUTION), lng_origin - (range_in_miles/self.RESOLUTION)
        for i in range(ROWS):
            for j in range(COLUMNS):
                if j > 0:  # has a left neighbor
                    self.add_edge(self.grid[i][j], self.grid[i][j - 1])
                if j < COLUMNS - 1:  # has right neighbor
                    self.add_edge(self.grid[i][j], self.grid[i][j + 1])
                if i > 0:  # has top neighbor
                    self.add_edge(self.grid[i][j], self.grid[i - 1][j])
                if i < ROWS - 1:  # has bottom neighbor
                    self.add_edge(self.grid[i][j], self.grid[i + 1][j])
                if j > 0 and i > 0:  # has top left neighbor
                    self.add_edge(self.grid[i][j], self.grid[i - 1][j - 1])
                if j < COLUMNS - 1 and i > 0:  # has top right neighbor
                    self.add_edge(self.grid[i][j], self.grid[i - 1][j + 1])
                if j > 0 and i < ROWS - 1:  # has bottom left neighbor
                    self.add_edge(self.grid[i][j], self.grid[i + 1][j - 1])
                if j < COLUMNS - 1 and i < ROWS - 1:  # has bottom right neighbor
                    self.add_edge(self.grid[i][j], self.grid[i + 1][j + 1])



    def print_node(self, node):
        print "lat={0}, lng={1}, ele={2}".format(node.lat, node.lng, node.ele)
            
    def add_node(self, node):
        self.print_node(node)
        self.nodes.add(node)

    def get_nodes(self):
        return self.grid

    def get_edges(self):
        return self.edges

    def get_approx_lat(self, lat):
        # lat
        for i,node in enumerate(self.grid):
            if node.lat < lat:
                pass
            else:
                if node.lat-lat > lat-self.grid[i-1][0].lat:
                    lat = self.grid[i-1][0].lat
                else:
                    lat = node.lat
        return lat

    def get_approx_lng(self, lng):
        # lng
        for i,node in enumerate(self.grid[0]):
            if node.lng < lng:
                pass
            else:
                if node.lng-lng > lng-self.grid[0][i-1].lng:
                    lng = self.grid[0][i-1].lng
                else:
                    lng = node.lng
        return lng

    def add_edge(self, source, target):
        edge = {
            'source' : source,
            'target' : target
            }
        self.edges.append(edge)
        if source in self.node_edge_map:
            self.node_edge_map[source].append(edge)
        else:
            self.node_edge_map[source] = [edge]

    def neighbor(self, source):
        neighbor_list = []
        for edge in self.node_edge_map[source]:
            neighbor_list.append(edge['target'])
        return neighbor_list

