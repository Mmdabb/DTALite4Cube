import pandas as pd

# START OF ARGUMENTS

# Network directory
# net_dir = r'LDN034_BD'
net_dir = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\Python codes\nets_test\LDN034_BD'

# Assignment argument
iteration = 20
route = 0
simu = 0
UE_converge = 0.1

# Units arguement
length = 'meter'
speed = 'mph'

# Demand period arguement
period_title = ['am', 'md', 'pm']
period_time = ['0600_0900', '0900_1500', '1500_1900', '1900_0600']

# Mode type argument
modes = ['apv', 'com', 'hov2', 'hov3', 'sov', 'trk']

# Scenario generation based on demand period
scenario_gen = []
for title in period_title:
    scenario_gen.append('scenario_' + title)

# Link type generation
df = pd.read_csv('link_type_NVTA.csv')

# sensor data
sensor_1 = {
    'sensor_id': 1,
    'from_node_id': 483,
    'to_node_id': 481,
    'demand_period': 'am',
    'count': 3000.975,
    'scenario_index': 0,
    'activate': 0
}
