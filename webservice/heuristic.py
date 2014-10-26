__author__ = 'mihir'

from graphinit import Graph, GPS


node_pair_cost_map = {}

def cost_of_path(node, goal):
    '''
    :type node: GPS
    :type goal: GPS
    :return: int
    '''

    #print 'not expensive node pair', node.x, node.y
    dx = abs(node.ele - goal.ele)
    dy = abs(node.ele - goal.ele)
    return dx + dy


def heuristic_estimate(graph):
    '''
    :type graph: Graph
    :return:
    '''

    global node_pair_cost_map
    for node1 in graph.get_nodes():
        for node2 in graph.get_nodes():
            node_pair_cost_map[(node1, node2)] = cost_of_path(node1, node2)

