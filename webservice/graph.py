import logging
import math
import gps

class Graph:
    
    def __init__(self, lat_origin, lng_origin, range_in_miles, gps_increment=0.01):
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
        self.lat_origin = lat_origin
        self.lng_origin = lng_origin


        self.lat_upper_limit = self.lat_origin + (range_in_miles/self.RESOLUTION)
        #TODO: change lng_range conversion to be dependent on latitude
        self.lng_upper_limit = self.lng_origin + (range_in_miles/self.RESOLUTION)
        # start lat and lng at bottom left corner of grid
        self.lat_lower_limit = self.lat_origin - (range_in_miles/self.RESOLUTION)
        self.lng_lower_limit = self.lng_origin - (range_in_miles/self.RESOLUTION)

        #TODO: change lat and lng to lat origin and lng origin

        # add all nodes
        i,j = 0,0
        lat= self.lat_lower_limit
        while lat < self.lat_upper_limit:
            self.grid.append([])
            lng = self.lng_lower_limit
            while lng < self.lng_upper_limit:
                node = (lat, lng)
                self.grid[i].append(node)
                lng += self.gps_increment
                j += 1
            # call get_gps on an entire row so we optimize use of the Elevation API
            self.grid[i] = gps.get_gps(self.grid[i])
            for node in self.grid[i]:
                self.add_node(node)
            lat += self.gps_increment
            i += 1

        
        ROWS, COLUMNS = len(self.grid), len(self.grid[0])
        self.rows, self.columns = ROWS, COLUMNS
        logging.debug('Rows = {0}, Columns = {1}'.format(ROWS, COLUMNS))

        # add all edges
        self.lat_lower_limit, self.lng_lower_limit = self.lat_origin - (range_in_miles/self.RESOLUTION), self.lng_origin - (range_in_miles/self.RESOLUTION)
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
        logging.debug('[{0}, {1}, {2}]'.format(node.lat, node.lng, node.ele))

    def get_location(self, node):
        ''' return this node as a [lat, lng, ele] tuple '''
        return [node.lat, node.lng, node.ele]
            
    def add_node(self, node):
        # self.print_node(node)
        self.nodes.add(node)

    def get_nodes(self):
        return self.grid

    def get_edges(self):
        return self.edges

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

    def get_approx_node(self, lat, lng):
        x, y = None, None
        for i in range(self.rows - 1):
            if lat >= self.grid[i][0].lat and lat <= self.grid[i+1][0].lat:
                if lat - self.grid[i][0].lat > self.grid[i+1][0].lat - lat:
                    x = i + 1
                else:
                    x = i
                break
        for j in range(self.columns - 1):
            if lng >= self.grid[x][j].lng and lng <= self.grid[x][j+1].lng:
                if lng - self.grid[x][j].lng > self.grid[x][j+1].lng - lng:
                    y = j + 1
                else:
                    y = j
                logging.debug('approx grid coordinate for ({0}, {1}) = {2}, {3}'.format(lat, lng, x, y))
                return self.grid[x][y]
        logging.error('ERROR approx grid coordinate not found!')
        abort(500)
        return None

    def neighbor(self, source):
        neighbor_list = []
        for edge in self.node_edge_map[source]:
            neighbor_list.append(edge['target'])
        return neighbor_list

