from performance_summary_functions import get_performance_stats
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
# catalog_dir = sys.argv[1]
# scenario_folders = sys.argv[2]
catalog_dir = r'C:\Users\mabbas10\ASU Dropbox\Mohammad Abbasi\NVTA\test runs\run_results\09-30\DTALite_0930_2024'
# scenario_folders = scenario_folders.split(',')
# scenario_folders_list = [item.strip() for item in scenario_folders]
scenario_folders_list = ['DTALite_LTB1_Final_20mem_BD_TEST', 'DTALite_LTB1_Final_20mem_BD_TEST2_PLF1']
# print(scenario_folders_list)


time_periods = ['am', 'md', 'pm', 'nt']
time_period_duration_list = ['0600_0900', '0900_1500', '1500_1900', '1900_0600']
period_length_dict = {'am': 3, 'md': 6, 'pm': 4, 'nt': 11}


if __name__ == "__main__":
    performance_stats = True
    speed_class_stats = False
    link_performance_comparison = False
    bus_delay_analysis = False

    if performance_stats:
        for scenario in scenario_folders_list:
            network_path = os.path.join(catalog_dir, scenario, 'Outputs', 'DTALite')
            get_performance_stats(network_path, time_periods, time_period_duration_list)


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
