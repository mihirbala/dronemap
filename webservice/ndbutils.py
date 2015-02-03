from google.appengine.ext import ndb

class Drone(ndb.Model):
    """Models an individual drone."""
    name = ndb.StringProperty(indexed=True)
    range_in_miles = ndb.FloatProperty()
    creation_time = ndb.DateTimeProperty()
    # last_updated = ndb.DateTimeProperty(auto_now_add=True)
    graph = ndb.PickleProperty()
    graph_start_node = ndb.PickleProperty()

def save(drone_name, drone_record):
	drone = Drone(
			name=drone_name,
			range_in_miles=drone_record['range_in_miles'],
			creation_time=drone_record['creation_time'],
			graph=drone_record['graph'],
			graph_start_node=drone_record['graph_start_node']
		)
	# TODO: if drone_name already exists, make sure user wants to update its info
	key = drone.put()
	return key

def retrieve(drone_name):
	result_set = Drone.query(Drone.name == drone_name)
	drones = result_set.fetch(1)
	if len(drones) > 0:
		drone = drones[0]
		drone_dict = {
			'name' : drone.name,
			'range_in_miles' : drone.range_in_miles,
			'creation_time' : drone.creation_time,
			'graph' : drone.graph,
			'graph_start_node' : drone.graph_start_node
		}
		return drone_dict
	return None
	

