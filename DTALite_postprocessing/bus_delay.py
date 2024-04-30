import pandas as pd
import csv
import numpy as np
import os


def bus_delay(tst_link_performance_df, tfc_link_performance_df, link_df, route_df, assignment_period, output_file_name):
    route_df['pair'] = route_df.apply(lambda x: (x.from_node_id, x.to_node_id), axis=1)
    tst_link_performance_df = tst_link_performance_df[tst_link_performance_df.link_type_name == 'service_links']
    tst_id_vol_dict = dict(zip(tst_link_performance_df.link_id, tst_link_performance_df.volume))
    route_df['transit_volume'] = route_df.apply(lambda x: tst_id_vol_dict.setdefault(x.trace_id, -1), axis=1)
    transit_vol_dict = dict(zip(route_df.pair, route_df.transit_volume))

    length_dict = dict(zip(link_df.link_id, link_df.length_in_mile))
    free_speed_dict = dict(zip(link_df.link_id, link_df.free_speed))
    tfc_link_performance_df['pair'] = tfc_link_performance_df.apply(lambda x: (x.from_node_id, x.to_node_id), axis=1)
    tfc_link_performance_df['transit_volume'] \
        = tfc_link_performance_df.apply(lambda x: transit_vol_dict.setdefault(x.pair, 0), axis=1)
    tfc_link_performance_df['length_in_mile'] = tfc_link_performance_df.apply(
        lambda x: length_dict.setdefault(x.link_id, -1), axis=1)
    tfc_link_performance_df['free_speed'] = tfc_link_performance_df.apply(
        lambda x: free_speed_dict.setdefault(x.link_id, -1), axis=1)
    tfc_link_performance_df['FFTT'] \
        = tfc_link_performance_df['length_in_mile'] / tfc_link_performance_df['free_speed']
    # unit in hours
    tfc_link_performance_df['TT'] \
        = tfc_link_performance_df['length_in_mile'] / tfc_link_performance_df['speed_mph']
    # unit in hours
    tfc_link_performance_df['delay'] \
        = tfc_link_performance_df['length_in_mile'] / tfc_link_performance_df['speed_mph'] - tfc_link_performance_df['FFTT']

    tfc_link_performance_df['person_delay'] = tfc_link_performance_df.transit_volume * tfc_link_performance_df.delay
    tfc_link_performance_df['person_hour'] = tfc_link_performance_df.transit_volume * tfc_link_performance_df.TT
    tfc_link_performance_df[
        'person_mile'] = tfc_link_performance_df.transit_volume * tfc_link_performance_df.length_in_mile

    mile_over_hour_nb = tfc_link_performance_df.person_mile.sum() / tfc_link_performance_df.person_hour.sum()
    delay_over_hour_nb = tfc_link_performance_df.person_delay.sum() / tfc_link_performance_df.person_hour.sum()

    row = []
    row.append([output_file_name, 'Transit', assignment_period, format(tfc_link_performance_df.delay.sum(), ".7f"),
                format(tfc_link_performance_df.person_delay.sum(), ".7f"),
                format(tfc_link_performance_df.person_hour.sum(), ".7f"),
                format(tfc_link_performance_df.person_mile.sum(), ".7f"),
                format(mile_over_hour_nb, ".7f"), format(delay_over_hour_nb, ".7f")])

    return row


def get_bus_delay(net_pair_list, time_periods, net_dir, regional_transit_stats_path):
    header = ['network', 'analysis_type', 'time_period', 'delay', 'person_delay', 'person_hour', 'person_mile',
              'mile/hour', 'delay/hour']

    statistics_dir = os.path.join(net_dir, "statistics")
    if not os.path.exists(statistics_dir):
        os.makedirs(statistics_dir)

    total_net_transit_stats = []
    for subnets_pair in net_pair_list:

        print('============================================================')
        if len(subnets_pair) > 1:
            bd_net = subnets_pair[0]
            nb_net = subnets_pair[1]
            output_file_name = f'{bd_net}_{nb_net}'
            output_dir = os.path.join(statistics_dir, output_file_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

        else:
            output_file_name = f'{subnets_pair[0]}'
            output_dir = os.path.join(statistics_dir, output_file_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

        for subnet in subnets_pair:
            subnet_dir = os.path.join(net_dir, subnet)
            subnet_name = f'{subnet}'

            print('network =', subnet)

            subnet_transit_stats = []
            total_subnet_transit_stats = []
            for time_period in time_periods:
                link_performance_df = pd.read_csv(
                    os.path.join(subnet_dir, f'link_performance_{time_period.lower()}.csv'))
                link_df = pd.read_csv(os.path.join(subnet_dir, 'link.csv'))
                link_df = link_df[['link_id', 'length_in_mile', 'free_speed']]

                route_mapping_df = pd.read_csv(
                    os.path.join(regional_transit_stats_path, f'route_{time_period.lower()}.csv'))
                na_values = {'link_type_code': ['']}
                transit_stat_dtypes = {'link_type_name': 'str', 'link_type_code': 'str', 'density': 'float',
                                       'TT_0': 'float'}
                transit_assignment = pd.read_csv(
                    os.path.join(regional_transit_stats_path, f'static_link_performance_{time_period.lower()}.csv'),
                    dtype=transit_stat_dtypes, na_values=na_values)

                assignment_period = f'{time_period.upper()}'
                transit_stat = bus_delay(transit_assignment, link_performance_df, link_df, route_mapping_df,
                                         assignment_period, subnet_name)
                subnet_transit_stats.extend(transit_stat)

            total_subnet_transit_stats.extend(subnet_transit_stats)
            if len(time_periods) > 1:
                subnet_transit_df = pd.DataFrame(subnet_transit_stats, columns=header)
                print(subnet_transit_df)

                numeric_columns = ['person_mile', 'person_hour', 'delay', 'person_delay']  # Add other columns as needed
                subnet_transit_df[numeric_columns] = subnet_transit_df[numeric_columns].apply(pd.to_numeric,
                                                                                              errors='coerce')

                total_mile_over_hour = subnet_transit_df.person_mile.sum() / np.maximum(
                    subnet_transit_df.person_hour.sum(), 0.1)
                total_delay_over_hour = subnet_transit_df.person_delay.sum() / np.maximum(
                    subnet_transit_df.person_hour.sum(), 0.1)

                total_subnet_transit_stats.append([subnet_name, 'Transit', 'total',
                                                   format(subnet_transit_df.delay.sum(), ".7f"),
                                                   format(subnet_transit_df.person_delay.sum(), ".7f"),
                                                   format(subnet_transit_df.person_hour.sum(), ".7f"),
                                                   format(subnet_transit_df.person_mile.sum(), ".7f"),
                                                   format(total_mile_over_hour, ".7f"),
                                                   format(total_delay_over_hour, ".7f")
                                                   ])

            total_net_transit_stats.extend(total_subnet_transit_stats)
        if len(subnets_pair) > 1:
            subnet_stats = pd.DataFrame(total_net_transit_stats, columns=header)

            subnet_bd = subnets_pair[0]
            subnet_nb = subnets_pair[1]
            subnet_name = subnet_bd.rsplit('_', 1)[0]

            subnet_bd_df = subnet_stats[subnet_stats['network'] == subnet_bd].reset_index(drop=True)
            subnet_nb_df = subnet_stats[subnet_stats['network'] == subnet_nb].reset_index(drop=True)

            numeric_columns = ['delay', 'person_delay', 'person_hour', 'person_mile',
                               'mile/hour', 'delay/hour']  # Add other columns as needed
            subnet_bd_df[numeric_columns] = subnet_bd_df[numeric_columns].apply(pd.to_numeric, errors='coerce')
            subnet_nb_df[numeric_columns] = subnet_nb_df[numeric_columns].apply(pd.to_numeric, errors='coerce')

            numeric_cols = subnet_bd_df.select_dtypes(include=[np.number]).columns
            print('numeric columns are \n', numeric_cols)
            abs_diff = subnet_bd_df[numeric_cols] - subnet_nb_df[numeric_cols]
            print(abs_diff)
            # percentage_diff = ((subnet_bd_df[numeric_cols] - subnet_nb_df[numeric_cols]) / subnet_nb_df[numeric_cols]) * 100

            time_period_cols = [period + '_diff' for period in time_periods]
            if len(time_periods) > 1:
                time_period_cols.append('total_diff')

            abs_diff.insert(0, 'time_period', time_period_cols)
            abs_diff.insert(0, 'analysis_type', 'Transit')
            abs_diff.insert(0, 'subarea', subnet_name)

            print(abs_diff)
            diff_arr = abs_diff.values
            total_net_transit_stats.extend(diff_arr)

    subnets_transit = pd.DataFrame(total_net_transit_stats, columns=header)
    subnets_transit.to_csv(os.path.join(statistics_dir, 'transit_stats.csv'), index=False)


def creat_pair_net(net_list):
    organized_data = {}

    for item in net_list:
        name = item.rstrip('_BD').rstrip('_NB')
        if name not in organized_data:
            organized_data[name] = []

        if item.endswith('_BD'):
            organized_data[name].append(item)
        elif item.endswith('_NB'):
            organized_data[name].append(item)
        else:
            organized_data[name].append([item])

    final_list = [value if len(value) > 1 else value[0] for value in organized_data.values()]
    return final_list


if __name__ == "__main__":
    period_length_dict = {'am': 3, 'md': 6, 'pm': 4, 'nt': 11, 'pm_r': 4}
    time_periods = ['am', 'md', 'pm']

    net_dir = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\Python codes\nets_test'
    regional_transit_stats_path = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\Python codes\DTALite4Cube\DTALite4Cube\transit_regional_assignment'

    sub_net_list = [item for item in os.listdir(net_dir) if
                    os.path.isdir(os.path.join(net_dir, item)) and item != "statistics"]
    net_pair_list = creat_pair_net(sub_net_list)

    get_bus_delay(net_pair_list, time_periods, net_dir, regional_transit_stats_path)
