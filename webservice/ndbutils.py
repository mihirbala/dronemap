from google.appengine.ext import ndb

class Drone(ndb.Model):
    """Models an individual drone."""
    drone_name = ndb.StringProperty(indexed=True)
    range_in_kilometers = ndb.FloatProperty()
    update_time = ndb.DateTimeProperty()
    location_cost_map = ndb.PickleProperty()
    # last_updated = ndb.DateTimeProperty(auto_now_add=True)
    # graph = ndb.PickleProperty()
    # graph_start_node = ndb.PickleProperty()

def save(drone_name, drone_record):

	# temporary fix to key mismatch problem
	ndb.delete_multi(Drone.query().fetch(keys_only=True))

	drone = Drone(
			drone_name=drone_name,
			range_in_kilometers=drone_record['range_in_kilometers'],
			update_time=drone_record['update_time'],
			location_cost_map=drone_record['location_cost_map']
			# graph=drone_record['graph'],
			# graph_start_node=drone_record['graph_start_node']
		)
	# TODO: if drone_name already exists, make sure user wants to update its info
	key = drone.put()
	return key

def retrieve(drone_name):
	result_set = Drone.query(Drone.drone_name == drone_name)
	drones = result_set.fetch(1)
	if len(drones) > 0:
		drone = drones[0]
		drone_dict = {
			'drone_name' : drone.drone_name,
			'range_in_kilometers' : drone.range_in_kilometers,
			'update_time' : drone.update_time,
			'location_cost_map' : drone.location_cost_map
			# 'graph' : drone.graph,
			# 'graph_start_node' : drone.graph_start_node
		}
		return drone_dict
	return None
	

