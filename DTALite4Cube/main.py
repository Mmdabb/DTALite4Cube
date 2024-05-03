import os, sys
import shutil
import pandas as pd
from settings import Settings
from cube2gmns import get_gmns_from_cube
from omx2csv import get_gmns_demand_from_omx

dta_lite_wd = sys.argv[1]
# START OF ARGUMENTS

# Network directory
# net_dir = r'LDN034_BD'
net_dir = dta_lite_wd

# Assignment argument
iteration = 20
route = 0
simu = 0
UE_converge = 0.1

# Units arguement
length = 'meter'
speed = 'mph'

# Demand period arguement
period_title = ['am','md','pm', 'nt']
period_time = ['0600_0900','0900_1500','1500_1900','1900_0600']

# Mode type argument
modes = ['apv', 'com', 'hov2', 'hov3', 'sov', 'trk']

# Scenario generation based on demand period
scenario_gen = []
for title in period_title:
    scenario_gen.append('scenario_' + title)

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


output_files = ['log.txt', 'summary_log.txt', 'link_performance.csv', 'route_assignment.csv', 'agent.csv',
                'trajectory.csv']
link_type_df = pd.read_csv(os.path.join(dta_lite_wd,'link_type_NVTA.csv'))
current_dir = dta_lite_wd #os.path.dirname(os.path.realpath(__file__))
network_path = dta_lite_wd #os.path.join(current_dir, net_dir)

dtalite_assignment = True
network_conversion = True
demand_conversion = True

if network_conversion:
    get_gmns_from_cube(network_path, district_id_assignment=True, capacity_adjustment=False)

if demand_conversion:
    get_gmns_demand_from_omx(network_path, period_title)

for time_period, period_time in zip(period_title, period_time):

    setting = Settings(time_period)
    setting.update_dta_basic(iteration, route, simu, UE_converge, length, speed)
    setting.update_mode(modes)
    setting.update_scenario()
    setting.update_demand_periods(period_time)
    setting.update_demand_list(modes, time_period)
    setting.update_demand_subarea()
    setting.update_sensor_data()
    setting.update_dtm()
    setting.update_departure_profile()
    setting.update_link_type(link_type_df)
    setting.yaml_writer(period_time, network_path)

    if dtalite_assignment:
        os.chdir(network_path)
        shutil.copyfile(f'settings_{time_period}.yml', 'settings.yml')

        if os.path.exists('link_qvdf.csv'):
            if time_period == 'nt':  # For 'nt' period we don't have parameters for qvdf function
                try:
                    os.remove(f'link_qvdf_{time_period}.csv')
                except OSError:
                    try:
                        os.rename('link_qvdf.csv', f'link_qvdf_{time_period}.csv')
                    except OSError:
                        # Handle renaming error here
                        pass
            else:
                try:
                    shutil.copyfile('link_qvdf_nt.csv', 'link_qvdf.csv')
                except FileNotFoundError:
                    pass

        # Run DTALite
        os.system(os.path.join(dta_lite_wd, 'DTALite_0416b_2024.exe'))

        # Rename the output files
        period_name = '_' + time_period
        for file_name in output_files:
            base_name, ext = os.path.splitext(file_name)
            new_file_name = f"{base_name}{period_name}{ext}"
            if os.path.exists(file_name):
                shutil.copyfile(file_name, new_file_name)
