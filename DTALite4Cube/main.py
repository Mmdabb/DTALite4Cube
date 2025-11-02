import os, sys
import shutil
import pandas as pd
# from settings import Settings
from settings import time_period_duration, update_agent_types, demand_file_list, generate_setting_csv
from settings import time_period_dict, vot_time_periods, agent_types_dict, link_type_dict
from cube2gmns import get_gmns_from_cube
from omx2csv import get_gmns_demand_from_omx

# dta_lite_wd = sys.argv[1]
# START OF ARGUMENTS

# Network directory
# net_dir = r'LDN034_BD'
# net_dir = dta_lite_wd

# Assignment argument
iteration = 20
route = 0
simu = 0
UE_converge = 0.1
memory_blocks = 20
# scale_factor = 1
# Units arguement
length = 'mile'
speed = 'mph'

# Demand period arguement
period_titles = ['am', 'md', 'pm', 'nt']
period_times = ['0600_0900', '0900_1500', '1500_1900', '1900_0600']
period_scale_factors = {"pm": 1.1}

# period_titles = ['am']
# period_times = ['0600_0900']

# Mode type argument
modes = ['sov', 'hov2', 'hov3', 'com', 'trk', 'apv']

output_files = ['log.txt', 'summary_log.txt', 'link_performance.csv', 'route_assignment.csv', 'agent.csv',
                'trajectory.csv']

# link_type_df = pd.read_csv(os.path.join(dta_lite_wd, 'link_type_NVTA.csv'))
#net_dir = r'C:\Users\mabbas10\ASU Dropbox\Mohammad Abbasi\NVTA\codes\old_version\DTALite4Cube'
# link_type_df = pd.read_csv(os.path.join(net_dir, 'link_type_NVTA.csv'))
# current_dir = dta_lite_wd  # os.path.dirname(os.path.realpath(__file__))
# network_path = dta_lite_wd  # os.path.join(current_dir, net_dir)
network_path = r'LDN034_BD'

dtalite_assignment = False
network_conversion = False
demand_conversion = False

if network_conversion:
    get_gmns_from_cube(network_path, period_titles, length,
                       district_id_assignment=True, capacity_adjustment=False)

if demand_conversion:
    get_gmns_demand_from_omx(network_path, period_titles)

# Input for [assignment] section
assignment_dict = {
    "assignment_mode": "lue",
    "column_generation_iterations": iteration,
    "column_updating_iterations": 0,
    "odme_iterations": -1,
    "simulation_iterations": simu,
    "sensitivity_analysis_iterations": 1,
    "number_of_memory_blocks": memory_blocks
}
time_period_duration_dict = time_period_duration(period_titles, period_times)

try:
    period_scale_factors  # just to check if it exists
except NameError:
    print("[WARN] period_scale_factors not defined. Using scale = 1 for all periods.")
    period_scale_factors = {}

demand_files_dict = demand_file_list(modes, period_titles, period_times, period_scale_factors)

for time_period, period_time in zip(period_titles, period_times):
    update_agent_types(time_period, agent_types_dict, vot_time_periods)
    demand_period_dict = {
        "demand_period_id": time_period_dict[time_period.upper()],
        "demand_period": time_period.upper(),
        "time_period": period_time,
        "time_duration": time_period_duration_dict[time_period.lower()]
    }

    period_demand_files = demand_files_dict[time_period.lower()]

    output_file = os.path.join(network_path, f'settings_{time_period}.csv')
    generate_setting_csv(output_file, assignment_dict, agent_types_dict, link_type_dict, demand_period_dict,
                         period_demand_files, vdf_type='qvdf')

    if dtalite_assignment:
        os.chdir(network_path)
        shutil.copyfile(f'settings_{time_period}.csv', 'settings.csv')
        shutil.copyfile(f'link_{time_period}.csv', 'link.csv')

        os.system('DTALite_0324b.exe')

        # Rename the output files
        period_name = '_' + time_period
        for file_name in output_files:
            base_name, ext = os.path.splitext(file_name)
            new_file_name = f"{base_name}{period_name}{ext}"
            if os.path.exists(file_name):
                shutil.copyfile(file_name, new_file_name)
