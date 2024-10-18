import sys

from funclib import get_diff_stats, time_period_duration, performance_summary, link_performance_preprocess, get_performance_stats
from funclib.bus_delay import get_bus_delay
import sys
import os


# location of all the dta lite runs
# catalog_dir = sys.argv[1]
# scenario_folders = sys.argv[2]
catalog_dir = r'C:\Users\mabbas10\Dropbox (ASU)\NVTA\test runs\run_results\09-30\DTALite_0324b'
# scenario_folders = scenario_folders.split(',')
# scenario_folders_list = [item.strip() for item in scenario_folders]
scenario_folders_list = ['DTALite_LTB1_Final_20mem_BD_TEST', 'DTALite_LTB1_Final_20mem_BD_TEST2_PLF1']
# print(scenario_folders_list)


time_periods = ['am', 'md', 'pm', 'nt']
time_period_duration_list = ['0600_0900', '0900_1500', '1500_1900', '1900_0600']
period_length_dict = {'am': 3, 'md': 6, 'pm': 4, 'nt': 11}

if __name__ == "__main__":
    performance_stats = True
    link_performance_comparison = True
    bus_delay_analysis = False

    if link_performance_comparison:
        if len(scenario_folders_list) != 2:
            sys.exit("Error: Exactly two scenario folders must be provided for link performance comparison.")

        if not os.path.exists(catalog_dir):
            sys.exit(f"Error: Directory does not exist: {catalog_dir}")

        time_duration_dict = time_period_duration(time_periods, time_period_duration_list)

        processed_link_performance_dict = {}
        for scenario in scenario_folders_list:
            network_path = os.path.join(catalog_dir, scenario, 'Outputs', 'DTALite')
            processed_link_performance_dict[scenario] = link_performance_preprocess(network_path, time_periods)
            performance_summary(processed_link_performance_dict[scenario], network_path,
                                time_duration_dict)  # Pass the specific scenario, not the entire dict

        bd_net = scenario_folders_list[0]
        nb_net = scenario_folders_list[1]
        output_path = os.path.join(catalog_dir, f'{bd_net}_{nb_net}')

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        get_diff_stats(output_path, processed_link_performance_dict[bd_net], processed_link_performance_dict[nb_net],
                       time_periods)

    elif performance_stats:
        for scenario in scenario_folders_list:
            network_path = os.path.join(catalog_dir, scenario, 'Outputs', 'DTALite')
            combined_link_performance = link_performance_preprocess(network_path, time_periods)
            time_duration_dict = time_period_duration(time_periods, time_period_duration_list)
            performance_summary(combined_link_performance, network_path, time_duration_dict)

    #
    # if performance_stats:
    #     for scenario in scenario_folders_list:
    #         network_path = os.path.join(catalog_dir, scenario, 'Outputs', 'DTALite')
    #         get_performance_stats(network_path, time_periods, time_period_duration_list)
    #
    #
    # if link_performance_comparison:
    #     if len(scenario_folders_list) != 2:
    #         sys.exit("Error: Exactly two scenario folders must be provided for link performance comparison.")
    #
    #     if not os.path.exists(catalog_dir):
    #         sys.exit(f"Error: Directory does not exist: {catalog_dir}")
    #
    #
    #     print("Warning: the first scenario will be considered as build network and the second as non-built")
    #
    #     bd_net = scenario_folders_list[0]
    #     nb_net = scenario_folders_list[1]
    #     bd_net_dir = os.path.join(catalog_dir, bd_net, 'Outputs', 'DTALite')
    #     nb_net_dir = os.path.join(catalog_dir, nb_net, 'Outputs', 'DTALite')
    #     output_path = os.path.join(catalog_dir, f'{bd_net}_{nb_net}')
    #     if not os.path.exists(output_path):
    #         os.makedirs(output_path)
    #
    #     get_diff_stats(output_path, bd_net_dir, nb_net_dir, time_periods)
    #
    #
    # if bus_delay_analysis:
    #     get_bus_delay(new_net_list, time_periods, parent_dir, regional_transit_stats_path)
