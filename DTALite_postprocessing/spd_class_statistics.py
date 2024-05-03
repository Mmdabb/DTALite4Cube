import pandas as pd
import csv
import time
import numpy as np
import os


def speed_class(speed):
    nb_range = np.floor(speed / 5)
    name = str(int(nb_range * 5)) + '_' + str(int((nb_range + 1) * 5))
    return name


def statistics(bd_df, nb_df, am_sta_nb_df, am_sta_bd_df, period_name, period_length, output_folder):
    statistics_list = []

    length_dict = dict(zip(am_sta_nb_df.pair, am_sta_nb_df.length_in_mile))
    free_speed_dict = dict(zip(am_sta_nb_df.pair, am_sta_nb_df.free_speed))

    nb_df['speed_class'] = nb_df.apply(lambda x: speed_class(x.speed_mph), axis=1)

    nb_df['length_in_mile'] = nb_df.apply(lambda x: length_dict.setdefault(x.pair, -1), axis=1)
    nb_df['free_speed'] = nb_df.apply(lambda x: free_speed_dict.setdefault(x.pair, -1), axis=1)
    nb_df['FFTT'] = nb_df['length_in_mile'] / nb_df['free_speed']
    # unit in hours
    nb_df['TT'] = nb_df['length_in_mile'] / nb_df['speed_mph']
    # unit in hours
    nb_df['delay'] = nb_df['length_in_mile'] / nb_df['speed_mph'] - nb_df['FFTT']
    nb_df['person_delay'] = nb_df.person_volume * nb_df.delay
    nb_df['person_hour'] = nb_df.person_volume * nb_df.TT
    nb_df['person_mile'] = nb_df.person_volume * nb_df.length_in_mile
    nb_df['vehicle_mile'] = nb_df.vehicle_volume * nb_df.length_in_mile
    nb_df['trk_vehicle_mile'] = nb_df.vehicle_vol_trk * nb_df.length_in_mile  # occ of truck = 1

    mile_over_hour_nb = nb_df.person_mile.sum() / np.maximum(nb_df.person_hour.sum(), 0.1)
    delay_over_hour_nb = nb_df.person_delay.sum() / np.maximum(nb_df.person_hour.sum(), 0.1)

    nb_df['severe_congestion_duration_in_h'] = np.minimum(nb_df['severe_congestion_duration_in_h'], period_length)
    nb_df['P'] = np.minimum(nb_df['P'], period_length)

    nb_df['length_weighed_severe_congestion'] = \
        (nb_df['severe_congestion_duration_in_h'] * nb_df['length_in_mile'])  # /nb_df['length_in_mile'].mean()

    nb_df['length_weighed_P'] = \
        (nb_df['P'] * nb_df['length_in_mile'])  # /nb_df['length_in_mile'].mean()

    # keep 3 decimal places
    sta_nb = ['NB', format(nb_df.delay.sum(), ".7f"), format(nb_df.person_delay.sum(), ".7f"),
              format(nb_df.person_hour.sum(), ".7f"), format(nb_df.person_mile.sum(), ".7f"),
              format(mile_over_hour_nb, ".7f"), format(delay_over_hour_nb, ".7f"),
              nb_df['severe_congestion_duration_in_h'].max(),
              nb_df['severe_congestion_duration_in_h'].mean(),
              nb_df['length_weighed_severe_congestion'].sum(),
              nb_df['P'].max(),
              nb_df['P'].mean(),
              nb_df['length_weighed_P'].sum(),
              format(nb_df.vehicle_mile.sum(), ".7f"),
              format(nb_df.trk_vehicle_mile.sum(), ".7f")]

    group = nb_df.groupby('speed_class')
    for spd_class, sub_nb_df in group:
        statistics_list.append(sta_nb)
        sub_mile_over_hour_nb = sub_nb_df.person_mile.sum() / np.maximum(sub_nb_df.person_hour.sum(), 0.1)
        sub_delay_over_hour_nb = sub_nb_df.person_delay.sum() / np.maximum(sub_nb_df.person_hour.sum(), 0.1)
        sta_nb = [spd_class, format(sub_nb_df.delay.sum(), ".7f"), format(sub_nb_df.person_delay.sum(), ".7f"),
                  format(sub_nb_df.person_hour.sum(), ".7f"), format(sub_nb_df.person_mile.sum(), ".7f"),
                  format(sub_mile_over_hour_nb, ".7f"), format(sub_delay_over_hour_nb, ".7f"),
                  sub_nb_df['severe_congestion_duration_in_h'].max(),
                  sub_nb_df['severe_congestion_duration_in_h'].mean(),
                  sub_nb_df['length_weighed_severe_congestion'].sum(),
                  sub_nb_df['P'].max(),
                  sub_nb_df['P'].mean(),
                  sub_nb_df['length_weighed_P'].sum(),
                  format(sub_nb_df.vehicle_mile.sum(), ".7f"),
                  format(sub_nb_df.trk_vehicle_mile.sum(), ".7f")]
    statistics_list.append(sta_nb)

    length_dict = dict(zip(am_sta_bd_df.pair, am_sta_bd_df.length_in_mile))
    free_speed_dict = dict(zip(am_sta_bd_df.pair, am_sta_bd_df.free_speed))

    bd_df['speed_class'] = bd_df.apply(lambda x: speed_class(x.speed_mph), axis=1)
    bd_df['length_in_mile'] = bd_df.apply(lambda x: length_dict.setdefault(x.pair, -1), axis=1)
    bd_df['free_speed'] = bd_df.apply(lambda x: free_speed_dict.setdefault(x.pair, -1), axis=1)
    bd_df['FFTT'] = bd_df['length_in_mile'] / bd_df['free_speed']
    # unit in hours
    bd_df['TT'] = bd_df['length_in_mile'] / bd_df['speed_mph']
    # unit in hours
    bd_df['delay'] = bd_df['length_in_mile'] / bd_df['speed_mph'] - bd_df['FFTT']
    bd_df['person_delay'] = bd_df.person_volume * bd_df.delay
    bd_df['person_hour'] = bd_df.person_volume * bd_df.TT
    bd_df['person_mile'] = bd_df.person_volume * bd_df.length_in_mile
    bd_df['vehicle_mile'] = bd_df.vehicle_volume * bd_df.length_in_mile
    bd_df['trk_vehicle_mile'] = bd_df.vehicle_vol_trk * bd_df.length_in_mile  # occ of truck = 1

    mile_over_hour_bd = bd_df.person_mile.sum() / np.maximum(bd_df.person_hour.sum(), 0.1)
    delay_over_hour_bd = bd_df.person_delay.sum() / np.maximum(bd_df.person_hour.sum(), 0.1)

    bd_df['severe_congestion_duration_in_h'] = np.minimum(bd_df['severe_congestion_duration_in_h'], period_length)
    bd_df['P'] = np.minimum(bd_df['P'], period_length)
    bd_df['length_weighed_severe_congestion'] = \
        (bd_df['severe_congestion_duration_in_h'] * bd_df['length_in_mile'])  # /bd_df['length_in_mile'].mean()
    bd_df['length_weighed_P'] = \
        (bd_df['P'] * bd_df['length_in_mile'])  # /bd_df['length_in_mile'].mean()

    # keep 3 decimal places
    sta_bd = ['BD', format(bd_df.delay.sum(), ".7f"), format(bd_df.person_delay.sum(), ".7f"),
              format(bd_df.person_hour.sum(), ".7f"), format(bd_df.person_mile.sum(), ".7f"),
              format(mile_over_hour_bd, ".7f"), format(delay_over_hour_bd, ".7f"),
              bd_df['severe_congestion_duration_in_h'].max(),
              bd_df['severe_congestion_duration_in_h'].mean(),
              bd_df['length_weighed_severe_congestion'].sum(),
              bd_df['P'].max(),
              bd_df['P'].mean(),
              bd_df['length_weighed_P'].sum(),
              format(bd_df.vehicle_mile.sum(), ".7f"),
              format(bd_df.trk_vehicle_mile.sum(), ".7f")]

    group = bd_df.groupby('speed_class')
    for spd_class, sub_bd_df in group:
        statistics_list.append(sta_bd)
        sub_mile_over_hour_nb = sub_bd_df.person_mile.sum() / np.maximum(sub_bd_df.person_hour.sum(), 0.1)
        sub_delay_over_hour_nb = sub_bd_df.person_delay.sum() / np.maximum(sub_bd_df.person_hour.sum(), 0.1)
        sta_bd = [spd_class, format(sub_bd_df.delay.sum(), ".7f"), format(sub_bd_df.person_delay.sum(), ".7f"),
                  format(sub_bd_df.person_hour.sum(), ".7f"), format(sub_bd_df.person_mile.sum(), ".7f"),
                  format(sub_mile_over_hour_nb, ".7f"), format(sub_delay_over_hour_nb, ".7f"),
                  sub_bd_df['severe_congestion_duration_in_h'].max(),
                  sub_bd_df['severe_congestion_duration_in_h'].mean(),
                  sub_bd_df['length_weighed_severe_congestion'].sum(),
                  sub_bd_df['P'].max(),
                  sub_bd_df['P'].mean(),
                  sub_bd_df['length_weighed_P'].sum(),
                  format(sub_bd_df.vehicle_mile.sum(), ".7f"),
                  format(sub_bd_df.trk_vehicle_mile.sum(), ".7f")]
    statistics_list.append(sta_bd)
    sta_dff = ['DIFF', format(bd_df.delay.sum() - nb_df.delay.sum(), ".3f"),
               format(bd_df.person_delay.sum() - nb_df.person_delay.sum(), ".3f"),
               format(bd_df.person_hour.sum() - nb_df.person_hour.sum(), ".3f"),
               format(bd_df.person_mile.sum() - nb_df.person_mile.sum(), ".3f"),
               format(mile_over_hour_bd - mile_over_hour_nb, ".3f"),
               format(delay_over_hour_bd - delay_over_hour_nb, ".3f"),
               bd_df['severe_congestion_duration_in_h'].max() - nb_df['severe_congestion_duration_in_h'].max(),
               bd_df['severe_congestion_duration_in_h'].mean() - nb_df['severe_congestion_duration_in_h'].mean(),
               bd_df['length_weighed_severe_congestion'].sum() - nb_df['length_weighed_severe_congestion'].sum(),
               bd_df['P'].max() - nb_df['P'].max(),
               bd_df['P'].mean() - nb_df['P'].mean(),
               bd_df['length_weighed_P'].sum() - nb_df['length_weighed_P'].sum(),
               format(bd_df.vehicle_mile.sum() - nb_df.vehicle_mile.sum(), ".3f"),
               format(bd_df.trk_vehicle_mile.sum() - nb_df.trk_vehicle_mile.sum(), ".3f")]
    statistics_list.append(sta_dff)

    with open(output_folder + '/' + 'spd_class_statistics_' + period_name + '.csv', 'w', encoding='UTF8',
              newline='') as f:
        writer = csv.writer(f)
        header = [period_name, 'delay', 'person_delay', 'person_hour', 'person_mile',
                  'mile/hour', 'delay/hour', 'max_severe_congestion_duration', 'avg_severe_congestion_duration',
                  'length_weighted_severe_congestion_duration',
                  'max_mild_congestion_duration', 'avg_mild_congestion_duration',
                  'length_weighted_mild_congestion_duration', 'vehicle_mile', 'trk_vehicle_mile']
        writer.writerow(header)
        writer.writerows(statistics_list)


def getspdstat(output_path, nb_net, bd_net, time_periods, period_length_dict):
    link_nb_df = pd.read_csv(os.path.join(nb_net, 'link.csv'))
    link_bd_df = pd.read_csv(os.path.join(bd_net, 'link.csv'))

    for time_period in time_periods:
        period_length = period_length_dict.get(time_period)

        nb_df = pd.read_csv(os.path.join(nb_net, f'link_performance_{time_period}.csv'))

        nb_pair_taz_dict = dict(zip(link_nb_df.pair, link_nb_df.TAZ))

        nb_df['pair'] = nb_df['from_node_id'].astype(str) + '->' + nb_df['to_node_id'].astype(str)
        # old_vdf_code = vdf_code / 100; FT = int(old_vdf_code % 10)
        old_vdf_code_nb = nb_df.link_type / 100
        link_type_ft_nb = (old_vdf_code_nb % 10).astype(int)
        nb_df['FT'] = link_type_ft_nb
        nb_df['TAZ'] = nb_df.apply(lambda x: nb_pair_taz_dict.setdefault(x.pair, -1), axis=1)

        nb_df_f = nb_df[(nb_df['TAZ'] > 1404) & (nb_df['TAZ'] < 2820) & (nb_df['FT'] > 0)].copy()
        # nb_df_f = nb_df_f.drop(['pair'],axis=1)
        # nb_df_f = nb_df_f.drop(['FT'],axis=1)

        bd_df = pd.read_csv(os.path.join(bd_net, f'link_performance_{time_period}.csv'))

        bd_pair_taz_dict = dict(zip(link_bd_df.pair, link_bd_df.TAZ))

        bd_df['pair'] = bd_df['from_node_id'].astype(str) + '->' + bd_df['to_node_id'].astype(str)
        # old_vdf_code = vdf_code / 100; FT = int(old_vdf_code % 10)
        old_vdf_code_bd = bd_df.link_type / 100
        link_type_ft_bd = (old_vdf_code_bd % 10).astype(int)
        bd_df['FT'] = link_type_ft_bd
        bd_df['TAZ'] = bd_df.apply(lambda x: bd_pair_taz_dict.setdefault(x.pair, -1), axis=1)

        bd_df_f = bd_df[(bd_df['TAZ'] > 1404) & (bd_df['TAZ'] < 2820) & (bd_df['FT'] > 0)].copy()
        # bd_df_f = bd_df_f.drop(['pair'],axis=1)
        # bd_df_f=bd_df_f.drop(['FT'],axis=1)

        sta_nb_df = link_nb_df[['link_id', 'pair', 'length_in_mile', 'free_speed']]
        sta_bd_df = link_bd_df[['link_id', 'pair', 'length_in_mile', 'free_speed']]

        statistics(bd_df_f, nb_df_f, sta_nb_df, sta_bd_df, time_period, period_length, output_path)


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

