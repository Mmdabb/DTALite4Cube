# Modules
import os
import shutil
import pandas as pd
from class_setting import Settings
from user_input import period_title, period_time, net_dir
from user_input import iteration, route, simu, UE_converge, length, speed
from user_input import modes


output_files = ['log.txt', 'summary_log.txt', 'link_performance.csv', 'route_assignment.csv', 'agent.csv',
                'trajectory.csv']
link_type_df = pd.read_csv('link_type_NVTA.csv')
current_dir = os.path.dirname(os.path.realpath(__file__))
network_path = os.path.join(current_dir, net_dir)

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

    os.chdir(network_path)
    shutil.copyfile(f'settings_{time_period}.yml', 'settings.yml')

    # Run DTALite
    os.system('DTALite_0416b_2024.exe')

    # Rename the output files
    period_name = '_' + time_period
    for file_name in output_files:
        base_name, ext = os.path.splitext(file_name)
        new_file_name = f"{base_name}{period_name}{ext}"
        if os.path.exists(file_name):
            shutil.copyfile(file_name, new_file_name)







