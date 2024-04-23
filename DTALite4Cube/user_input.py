import pandas as pd

# START OF ARGUMENTS

# Network directory
net_dir = r'LDN034_BD'

# Assignment argument
iteration = 10
route = 0
simu = 0
UE_converge = 0.1

# Units arguement
length = 'meter'
speed = 'mph'

# Demand period arguement
period_title = ['am','md','pm']
period_time = ['0800_0900','1100_1200','1600_1700','2100_2200']

# Mode type argument
modes = ['apv','com','hov2','hov3','sov','trk']



        
# Scenario generation based on demand period
scenario_gen = []
for title in period_title:
    scenario_gen.append('scenario_' + title)

# Link type generation
df = pd.read_csv('link_type_NVTA.csv')

#sensor data
sensor_1 = {
    'sensor_id': 1,
    'from_node_id': 483,
    'to_node_id': 481,
    'demand_period': 'am',
    'count': 3000.975,
    'scenario_index': 0,
    'activate': 0
}