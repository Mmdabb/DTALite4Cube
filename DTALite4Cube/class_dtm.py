# Define the DTMs as dictionaries
dtm_1 = {
    'dtm_id': 1,
    'dtm_type': 'lane_closure',
    'from_node_id': 1,
    'to_node_id': 3,
    'final_lanes': 0.5,
    'demand_period': 'am',
    'mode_type': 'info',
    'scenario_index_vector': 0,
    'activate': 0
}

# Append the DTMs into a DTM list
dtm = []

dtm.append(dtm_1)

# Add the DTM list to the DTM dictionary 
dtm_dict = {}
dtm_dict = {'dynamic_traffic_management_data': dtm}