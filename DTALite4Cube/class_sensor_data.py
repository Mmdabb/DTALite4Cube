# Define the sensor data as dictionaries
sensor_1 = {
    'sensor_id': 1,
    'from_node_id': 483,
    'to_node_id': 481,
    'demand_period': 'am',
    'count': 3000.975,
    'scenario_index': 0,
    'activate': 0
}

# Append the sensor data into a sensor data list
sensor_data = []

sensor_data.append(sensor_1)

# Add the sensor data list to the sensor data dictionary 
sensor_data_dict = {}
sensor_data_dict = {'sensor_data': sensor_data}