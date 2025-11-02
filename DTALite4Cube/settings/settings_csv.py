import csv
from datetime import datetime, timedelta

def get_period_scale(period_title, per_period_sf=None):
    """Return user-defined scale if available, else 1."""
    if not isinstance(per_period_sf, dict):
        return 1
    return per_period_sf.get(period_title.lower(), 1)


def time_period_duration(time_period_list, period_range_list):
    time_period_duration_dict = {}
    for period_title, time_range in zip(time_period_list, period_range_list):
        start_time_str, end_time_str = time_range.split('_')
        start_time =  datetime.strptime(start_time_str, '%H%M')
        end_time = datetime.strptime(end_time_str, '%H%M')
        time_duration = end_time - start_time
        if time_duration.days < 0:
            time_duration = time_duration + timedelta(days=1)
        time_period_duration_dict[period_title.lower()] = time_duration.total_seconds() / 3600
    return time_period_duration_dict


# Function to update values based on time period using enumerate
def update_agent_types(time_period, agent_types, vot_time_periods):
    for idx, agent in enumerate(agent_types):
        agent_types[agent][1] = vot_time_periods[time_period.upper()][idx]


def demand_file_list(modes, period_titles, period_times, period_scale_factors=None, format_type='column'):
    demand_file_list_dict = {}

    if not isinstance(period_scale_factors, dict):
        period_scale_factors = {}

    for time_period, period_duration in zip(period_titles, period_times):
        file_seq_dict = {}
        file_sequence = 1
        sf = get_period_scale(time_period, period_scale_factors)
        for mode in modes:
            file_seq_dict[file_sequence] = [f'{mode}_{time_period}.csv', format_type, time_period.upper(), mode, sf]
            file_sequence += 1
        demand_file_list_dict[time_period] = file_seq_dict
    return demand_file_list_dict


# Function to generate the CSV file
def generate_setting_csv(output_file,  assignment_dict, agent_types_dict, link_type_dict, demand_period_dict, demand_files_dict, vdf_type='bpr'):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')

        # Writing the [assignment] section
        writer.writerow \
            (['[assignment]' ,'assignment_mode', 'column_generation_iterations', 'column_updating_iterations',
                         'odme_iterations', 'simulation_iterations', 'sensitivity_analysis_iterations', 'number_of_memory_blocks'])
        writer.writerow(['', assignment_dict['assignment_mode'], assignment_dict['column_generation_iterations'],
                         assignment_dict['column_updating_iterations'], assignment_dict['odme_iterations'],
                         assignment_dict['simulation_iterations'], assignment_dict['sensitivity_analysis_iterations'], assignment_dict['number_of_memory_blocks']])

        # Writing the [agent_type] section
        writer.writerow([])
        writer.writerow(['[agent_type]', 'agent_type', 'name', 'vot', 'flow_type', 'pce', 'person_occupancy'])
        for agent_type, details in agent_types_dict.items():
            writer.writerow(['', agent_type] + details)

        # Writing the [link_type] section from CSV
        writer.writerow([])
        writer.writerow \
            (['[link_type]', 'link_type', 'link_type_name', 'agent_type_blocklist', 'type_code', 'traffic_flow_code', 'vdf_type'])
        for link_type, link_details in link_type_dict.items():
            writer.writerow(['', link_type] + link_details + [vdf_type])
        #         with open(link_type_file, 'r') as lt_file:
        #             lt_reader = csv.reader(lt_file)
        #             for row in lt_reader:
        #                 writer.writerow([''] + row + vdf_type)

        # Writing the [demand_period] section
        writer.writerow([])
        writer.writerow(['[demand_period]', 'demand_period_id', 'demand_period', 'time_period', ''])
        writer.writerow(['', demand_period_dict['demand_period_id'], demand_period_dict['demand_period'], demand_period_dict['time_period'], demand_period_dict['time_duration']])

        # Writing the [demand_file_list] section
        writer.writerow([])
        writer.writerow \
            (['[demand_file_list]', 'file_sequence_no', 'file_name', 'format_type', 'demand_period', 'agent_type', 'scale_factor'])
        for file_seq, demand_files_details in demand_files_dict.items():
            writer.writerow(['', file_seq] + demand_files_details)

        # Writing the [capacity_scenario] section (currently empty)
        writer.writerow([])
        writer.writerow \
            (['[capacity_scenario]' ,'from_node_id', 'to_node_id', 'time_window', 'time_interval', 'travel_time_delta', 'capacity'])