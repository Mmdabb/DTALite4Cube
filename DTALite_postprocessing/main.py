from perf_based_stats import perf_based_stat
from link_perf_comparison import get_period_diff
from spd_class_statistics import getspdstat
from bus_delay import get_bus_delay
import pandas as pd
import numpy as np
import os
# import shutil
import csv
import time


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
    time_periods = ['am', 'md', 'pm']
    period_length_dict = {'am': 3, 'md': 6, 'pm': 4, 'nt': 11, 'pm_r': 4}
    performance_stats = False
    speed_class_stats = False
    link_performance_comparison = False
    bus_delay_analysis = False

    parent_dir = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\Python codes\nets_test'
    regional_transit_stats_path = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. ' \
                                  r'Projects\NVTA\3_Subarea_analysis\Python ' \
                                  r'codes\DTALite4Cube\DTALite4Cube\transit_regional_assignment '

    # sub_net_list = ['CMP001', 'FFX134_BD','FFX134_NB', 'FFX138_BD', 'FFX138_NB',
    #               'LDN029_BD', 'LDN029_NB', 'LDN033_BD', 'LDN033_NB', 'LDN034', 'MAN003', 'PWC040_BD', 'PWC040_NB']
    sub_net_list = [item for item in os.listdir(parent_dir) if
                    os.path.isdir(os.path.join(parent_dir, item)) and not "statistics" in item]
    new_net_list = creat_pair_net(sub_net_list)



    if performance_stats:
         perf_based_stat(time_periods, parent_dir, sub_net_list)



    if speed_class_stats:
        period_length_dict = {'am': 3, 'md': 6, 'pm': 4, 'nt': 11, 'pmr': 4}

        statistics_folder = os.path.join(parent_dir, "statistics")
        if not os.path.exists(statistics_folder):
            os.makedirs(statistics_folder)

        for pair in new_net_list:
            if len(pair) > 1:
                bd_net = pair[0]
                nb_net = pair[1]
                bd_net_dir = os.path.join(parent_dir, bd_net)
                nb_net_dir = os.path.join(parent_dir, nb_net)
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
                bd_net_dir = os.path.join(parent_dir, bd_net)
                nb_net_dir = os.path.join(parent_dir, nb_net)
                output_path = os.path.join(statistics_folder, f'{bd_net}_{nb_net}')
                if not os.path.exists(output_path):
                    os.makedirs(output_path)

                get_period_diff(time_periods, period_length_dict, output_path, nb_net_dir, bd_net_dir)



    if bus_delay_analysis:
        get_bus_delay(new_net_list, time_periods, parent_dir, regional_transit_stats_path)
