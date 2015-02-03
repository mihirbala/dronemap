__author__ = 'mihir'

import sys
import heuristic
from gps import GPS
from graph import Graph


def Astar(start, goal, G):
    """
    :type start: GPS
    :type goal: GPS
    :type G: Graph
    :return: list
    """

    closedset = set()  #set of visited nodes
    openset = {start}  #set of nodes to be evaluated
    came_from = {}  #keeps track of path
    g_score = {}  #the cost from the start to current
    f_score = {}  #the cost of g_score + the heuristic cost of current to goal
    g_score[start] = 0
    f_score[start] = g_score[start] + heuristic.cost_of_path(start,  goal)
    while len(openset) > 0:
        lowest_cost = sys.maxint
        current = None
        for i in openset:  #find cheapest node in openset
            if f_score[i] < lowest_cost:
                lowest_cost = f_score[i]
                current = i
        #TODO Fix side case where starting location is target location
        if current == goal:
            return reconstruct_path(came_from, goal)
        openset.remove(current)
        closedset.add(current)
        if current not in came_from:
            came_from[current] = [current]
        else:
            came_from[current].append(current)
        for neighbor in G.neighbor(current):
            tentative_g_score = g_score_comp(current, came_from) + heuristic.cost_of_path(current,neighbor)
            # if we have processed this node already but current path is cheaper, remove so we add new path
            if neighbor in g_score and tentative_g_score < g_score[neighbor]:
                if neighbor in closedset:
                    closedset.remove(neighbor)
                if neighbor in openset:
                    openset.remove(neighbor)
            if neighbor not in openset and neighbor not in closedset:
                came_from[neighbor] = came_from[current][:]
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score_comp(neighbor,came_from) + heuristic.cost_of_path(neighbor,goal)
                if neighbor not in openset:
                    openset.add(neighbor)


def reconstruct_path(came_from, goal):
    if goal in came_from[goal]:
        return came_from[goal]
    else:
        lst = came_from[goal]
        lst.append(goal)
        return lst
   

def g_score_comp(node, came_from):
    sumcost = 0
    for n in came_from[node]:
        sumcost += n.ele
    return sumcost