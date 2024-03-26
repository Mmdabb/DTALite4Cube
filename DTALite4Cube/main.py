# Modules
import os
import shutil
import pandas as pd
import ruamel_yaml as yaml
from class_basic import basic_dict
from class_mode import mode_types_dict
from class_scenario import scenario_dict
from class_demand_period import demand_period_dict
from class_demand_file import demand_file_dict
from class_demand_subarea import demand_subarea_dict
from class_sensor_data import sensor_data_dict
from class_dtm import dtm_dict
from class_departure_profile import departure_profile_dict
from class_link_type import link_type_dict
from user_input import period_title, net_dir
from cube2gmns import get_gmns_from_cube
from omx2csv import get_gmns_demand_from_omx


# YAML Generator function
def YAML_writer():
    # Merge all the classes to a single dataset
    data = {}
    data.update(basic_dict)
    data.update(mode_types_dict)
    data.update(scenario_dict)
    data.update(demand_period_dict)
    data.update(demand_file_dict)
    data.update(demand_subarea_dict)
    data.update(sensor_data_dict)
    data.update(dtm_dict)
    data.update(departure_profile_dict)
    data.update(link_type_dict)

    # Write into a YAML file
    with open('settings.yml', 'w') as file:
        yaml.dump(data, file, Dumper=yaml.RoundTripDumper)


# Read the network files
net_files = os.listdir(net_dir)
scenario_files = []

for item in net_files:
    # Check if the item is a directory, if yes, add to the list
    full_path = os.path.join(net_dir, item)
    if os.path.isdir(full_path):
        scenario_files.append(item)

# DTALite loop for each network and demand period   
output_files = ['log.txt', 'summary_log.txt', 'link_performance.csv', 'route_assignment.csv', 'agent.csv',
                'trajectory.csv']

# Network loop (Outer loop)
for network in scenario_files:
    network_path = os.path.join(net_dir, network)

    get_gmns_from_cube(network_path)
    get_gmns_demand_from_omx(network_path, period_title)

    os.chdir(network_path)

    # Read the link file
    df_link = pd.read_csv('link.csv')

    # Generate the YML setting file
    YAML_writer()

    # Demand period loop (Inner loop)
    for i in range(len(period_title)):

        # Activate/deactivate the scenario for the demand period in a loop
        with open('settings.yml', 'r') as file:
            config = yaml.safe_load(file)

        if i != 0:
            config['scenarios'][i - 1]['activate'] = 0
        config['scenarios'][i]['activate'] = 1

        with open('settings.yml', 'w') as file:
            yaml.dump(config, file, Dumper=yaml.RoundTripDumper)

        # Initialize DTALite parameters
        df_link['lanes'] = df_link['lanes' + str(i + 1)]
        df_link['VDF_plf'] = df_link['VDF_plf' + str(i + 1)]
        df_link['VDF_cap'] = df_link['VDF_cap' + str(i + 1)]
        df_link['VDF_alpha'] = df_link['VDF_alpha' + str(i + 1)]
        df_link['VDF_beta'] = df_link['VDF_beta' + str(i + 1)]
        df_link['link_type'] = df_link['link_type' + str(i + 1)]
        df_link['vdf_code'] = df_link['vdf_code' + str(i + 1)]

        # Run DTALite
        os.system('DTALite_03_06_b_2024.exe')

        # Rename the output files
        period_name = '_' + period_title[i]
        for file_name in output_files:
            new_file_name = file_name.split('.')[0] + period_name + '.' + file_name.split('.')[1]
            # Check if the file exists before renaming
            if os.path.exists(file_name):
                # os.rename(file_name, new_file_name)
                shutil.copyfile(file_name, new_file_name)
