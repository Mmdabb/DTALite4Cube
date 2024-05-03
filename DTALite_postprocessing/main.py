from perf_based_stats import perf_based_stat
from link_perf_comparison import get_period_diff
from spd_class_statistics import getspdstat
from bus_delay import get_bus_delay
import pandas as pd
import numpy as np
import os, sys
# import shutil
import csv
import time
import re

# location of all the dta lite runs
catalog_dir = sys.argv[1]
scenario_folders = sys.argv[2]
scenario_folders = scenario_folders.split(',')
scenario_folders_list = [item.strip() for item in scenario_folders]
print(scenario_folders_list)

def creat_pair_net(net_list):
    organized_data = {}

    for item in net_list:
        name = item.rstrip('_BD').rstrip('_NB')
        if name not in organized_data:
            organized_data[name] = []
            organized_data[name].append([item])

        else:
            organized_data[name][0].append(item)

    final_list = [value[0] for value in organized_data.values()]
    return final_list


if __name__ == "__main__":

    time_periods = ['am', 'md', 'pm', 'nt']
    period_length_dict = {'am': 3, 'md': 6, 'pm': 4, 'nt': 11} 
    performance_stats = True
    speed_class_stats = True
    link_performance_comparison = True
    bus_delay_analysis = False

    parent_dir = catalog_dir
    
    sub_nets = [item for item in os.listdir(parent_dir) if
                    os.path.isdir(os.path.join(parent_dir, item)) and not "statistics" in item]
    sub_net_list =  []
    for nets in sub_nets:
        if nets in scenario_folders_list:
           sub_net_list.append(nets) 
    print(sub_net_list)
    
    new_net_list = creat_pair_net(sub_net_list)

    print(new_net_list)

    if performance_stats:
         perf_based_stat(time_periods, parent_dir, sub_net_list)

    if speed_class_stats:
        period_length_dict = {'am': 3, 'md': 6, 'pm': 4, 'nt': 11}

        statistics_folder = os.path.join(parent_dir, "statistics")
        if not os.path.exists(statistics_folder):
            os.makedirs(statistics_folder)

        for pair in new_net_list:
            if len(pair) > 1:
                bd_net = pair[0]
                nb_net = pair[1]
                bd_net_dir = os.path.join(parent_dir, bd_net, 'Outputs', 'DTALite')
                nb_net_dir = os.path.join(parent_dir, nb_net, 'Outputs', 'DTALite')
                output_path = os.path.join(statistics_folder, f'{bd_net}_{nb_net}')
                if not os.path.exists(output_path):
                    os.makedirs(output_path)

                getspdstat(output_path, nb_net_dir, bd_net_dir, time_periods, period_length_dict)

    if link_performance_comparison:
        statistics_folder = os.path.join(parent_dir, "statistics")
        if not os.path.exists(statistics_folder):
            os.makedirs(statistics_folder)

        for pair in new_net_list:
            if len(pair) > 1:
                bd_net = pair[0]
                nb_net = pair[1]
                bd_net_dir = os.path.join(parent_dir, bd_net, 'Outputs', 'DTALite')
                nb_net_dir = os.path.join(parent_dir, nb_net, 'Outputs', 'DTALite')
                output_path = os.path.join(statistics_folder, f'{bd_net}_{nb_net}')
                if not os.path.exists(output_path):
                    os.makedirs(output_path)

                get_period_diff(time_periods, period_length_dict, output_path, nb_net_dir, bd_net_dir)


    if bus_delay_analysis:
        get_bus_delay(new_net_list, time_periods, parent_dir, regional_transit_stats_path)
