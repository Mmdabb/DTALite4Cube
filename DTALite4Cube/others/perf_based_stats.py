# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 22:59:49 2022

@author: M. Abbasi
"""
import pandas as pd
import numpy as np
import os
#import shutil
import csv
import time


        
        


def perf_based_stat(time_periods, parent_dir, net_list):
    

    allowed_uses_dict = {
        0: 'sov;hov2;hov3;trk;apv;com',
        1: 'sov;hov2;hov3;trk;apv;com',
        2: 'hov2;hov3',
        3: 'hov3',
        4: 'sov;hov2;hov3;com;apv',
        5: 'apv',
        6: '',
        7: '',
        8: '',
        9: 'closed'
        }   

    # Reverse the dictionary to map values to keys
    reverse_allowed_uses_dict = {v: k for k, v in allowed_uses_dict.items()}
    
    new_net_list = creat_pair_net(net_list)
    total_net_stats = []
    for subnet_list in new_net_list:
    
        
        for sub_net in subnet_list:
            print("network = ", sub_net)
        
            net_dir = os.path.join(parent_dir, f'{sub_net}')
    
            link_net = pd.read_csv(os.path.join(net_dir, 'link.csv'))
    

            pair_taz_dict = dict(zip(link_net.pair, link_net.TAZ))
            #pair_jur_dict = dict(zip(link_net.pair, link_net.JUR))
            #pair_jurname_dict = dict(zip(link_net.pair, link_net.JUR_NAME))
            #pair_district_dict = dict(zip(link_net.pair, link_net.district_id))
            #pair_tollgrp_dict = dict(zip(link_net.pair, link_net.TOLLGRP))

            length_dict = dict(zip(link_net.pair, link_net.length_in_mile))
            free_speed_dict = dict(zip(link_net.pair, link_net.free_speed))
            

            header_df=['subarea','time_period', 'delay', 'person_delay', 'person_hour', 'person_mile','mile/hour', 'delay/hour',
                   'max_severe_congestion_duration', 'mean_severe_congestion_duration(normal avg)',
                   'mean_severe_congestion_duration(length avg)', 'severe_congestion_duration(length weighted sum)',
                   'vehicle_mile', 'vehicle_hour', 'vehicle mile/hour',
                   'trk_vehicle_mile', 'trk_vehicle_hour', 'trk mile/hour',
                   'HOV/HOT_delay', 	'HOV/HOT_person_delay', 'HOV/HOT_person_hour', 'HOV/HOT_person_mile', 'HOV/HOT_mile/hour', 'HOV/HOT_delay/hour'
                   ] 
    
            total_stat = []
            period_stat = []
            periods_to_numbers = {'am': 1, 'md': 2, 'pm': 3, 'nt': 4, 'pmr':4}
            for periods in time_periods:
                
                print('time period = ', periods)
                period_number = periods_to_numbers[periods]
                link_net[f'VDF_allowed_uses_keys{period_number}'] = link_net[f'VDF_allowed_uses{period_number}'].map(reverse_allowed_uses_dict).fillna(-1)
                # Filter link_net based on conditions for keys 2 or 3
                hov_filtered_links = link_net[
                    (link_net['TOLLGRP'] == 2) | 
                    (link_net[f'VDF_allowed_uses_keys{period_number}'] == 2) |
                    (link_net[f'VDF_allowed_uses_keys{period_number}'] == 3)
                    ]

                # Get node pairs from the filtered links
                hov_filtered_node_pairs = hov_filtered_links['pair']  
                
                

                link_perf_net = pd.read_csv(os.path.join(net_dir, f'link_performance_{periods}.csv'))
                link_perf_net['pair'] = link_perf_net['from_node_id'].astype(str) + '->' + link_perf_net['to_node_id'].astype(str)
                #link_perf_net['district_id'] = link_perf_net.apply(lambda x: pair_district_dict.setdefault(x.pair, -1), axis=1)
                
                link_perf_net['TAZ'] = link_perf_net.apply(lambda x: pair_taz_dict.setdefault(x.pair, -1), axis=1)
                link_perf_net['FT'] = link_perf_net.link_type%10
                #link_perf_jur_net = link_perf_net[link_perf_net['FT']>0].copy()
                link_perf_jur_net = link_perf_net[(link_perf_net['TAZ']>1404) & (link_perf_net['TAZ']<2820) & (link_perf_net['FT']>0)].copy()
                
                
                if link_perf_jur_net.volume.sum() < 0.5 or link_perf_jur_net.empty:
                    continue
                
                link_perf_jur_net['length_in_mile'] = link_perf_jur_net.apply(lambda x: length_dict.setdefault(x.pair, -1), axis=1)
                link_perf_jur_net['free_speed'] = link_perf_jur_net.apply(lambda x: free_speed_dict.setdefault(x.pair, -1), axis=1)
                
                period_length_dict = {'am':3,'md':6,'pm':4,'nt':11,'pmr':4}
                period_length=period_length_dict.get(periods)
        
                link_perf_jur_net['FFTT'] = link_perf_jur_net['length_in_mile'] / link_perf_jur_net['free_speed']
                link_perf_jur_net['TT'] = link_perf_jur_net['length_in_mile'] / link_perf_jur_net['speed']
                link_perf_jur_net['delay'] = link_perf_jur_net['TT'] - link_perf_jur_net['FFTT']
                link_perf_jur_net['person_delay'] = link_perf_jur_net.person_volume * link_perf_jur_net.delay
                link_perf_jur_net['person_hour'] = link_perf_jur_net.person_volume * link_perf_jur_net.TT
                link_perf_jur_net['person_mile'] = link_perf_jur_net.person_volume * link_perf_jur_net.length_in_mile
                link_perf_jur_net['length_weighted_P'] = link_perf_jur_net['severe_congestion_duration_in_h'] * link_perf_jur_net['length_in_mile']
        
                link_perf_jur_net['vehicle_mile'] = link_perf_jur_net.volume * link_perf_jur_net.length_in_mile
                link_perf_jur_net['vehicle_hour'] = link_perf_jur_net.volume * link_perf_jur_net.TT
                vehicle_mile_over_hour = link_perf_jur_net.vehicle_mile.sum() / np.maximum(link_perf_jur_net.vehicle_hour.sum(),0.1)
        
                link_perf_jur_net['trk_vehicle_mile'] = link_perf_jur_net.person_vol_trk * link_perf_jur_net.length_in_mile  # occ of truck = 1
                link_perf_jur_net['trk_vehicle_hour'] = link_perf_jur_net.person_vol_trk * link_perf_jur_net.TT
                trk_vehicle_mile_over_hour = link_perf_jur_net.trk_vehicle_mile.sum() / np.maximum(link_perf_jur_net.trk_vehicle_hour.sum(),0.1)
        
                if link_perf_jur_net.person_hour.sum() < 0.5:
                    print('sum of person_hour for %s = %s' % (periods, link_perf_jur_net.person_hour.sum()))
            
                mile_over_hour = link_perf_jur_net.person_mile.sum() / np.maximum(link_perf_jur_net.person_hour.sum(),0.1)
                delay_over_hour = link_perf_jur_net.person_delay.sum() / np.maximum(link_perf_jur_net.person_hour.sum(),0.1)
        
                severe_P_length_weighted = link_perf_jur_net['length_weighted_P'].sum() / link_perf_jur_net['length_in_mile'].sum()
                
                
                # Use filtered node pairs to extract statistics from link_performance_df
                hov_link_perf_net = link_perf_jur_net[link_perf_jur_net['pair'].isin(hov_filtered_node_pairs)]
                hov_mile_over_hour = hov_link_perf_net.person_mile.sum() / np.maximum(hov_link_perf_net.person_hour.sum(),0.1)
                hov_delay_over_hour = hov_link_perf_net.person_delay.sum() / np.maximum(hov_link_perf_net.person_hour.sum(),0.1)
                

                
            
    
                period_stat.append([f'{sub_net}', f'{periods}', 
                        link_perf_jur_net.delay.sum(), 
                        link_perf_jur_net.person_delay.sum(),
                        link_perf_jur_net.person_hour.sum(), 
                        link_perf_jur_net.person_mile.sum(),
                        mile_over_hour, delay_over_hour,
                        np.minimum(link_perf_jur_net['severe_congestion_duration_in_h'].max(),period_length),
                        np.minimum(link_perf_jur_net['severe_congestion_duration_in_h'].mean(),period_length),
                        severe_P_length_weighted,
                        link_perf_jur_net['length_weighted_P'].sum(),
                        link_perf_jur_net.vehicle_mile.sum(),
                        link_perf_jur_net.vehicle_hour.sum(),
                        vehicle_mile_over_hour,
                        link_perf_jur_net.trk_vehicle_mile.sum(),
                        link_perf_jur_net.trk_vehicle_hour.sum(),
                        trk_vehicle_mile_over_hour,
                        hov_link_perf_net.delay.sum(), 
                        hov_link_perf_net.person_delay.sum(),
                        hov_link_perf_net.person_hour.sum(), 
                        hov_link_perf_net.person_mile.sum(),
                        hov_mile_over_hour, hov_delay_over_hour
                        ])

    
            total_stat.extend(period_stat)
            
            if len(time_periods) > 1:
                per_perf_based_stats = pd.DataFrame(period_stat, columns=header_df)
                
                
                #print(per_perf_based_stats)
                total_stat.append([f'{sub_net}', 'total', 
                         per_perf_based_stats.delay.sum(), 
                         per_perf_based_stats.person_delay.sum(),
                         per_perf_based_stats.person_hour.sum(), 
                         per_perf_based_stats.person_mile.sum(),
                         per_perf_based_stats.person_mile.sum() / np.maximum(per_perf_based_stats.person_hour.sum(),0.1), 
                         per_perf_based_stats.person_delay.sum() / np.maximum(per_perf_based_stats.person_hour.sum(),0.1),
                         per_perf_based_stats['max_severe_congestion_duration'].max(),
                         per_perf_based_stats['mean_severe_congestion_duration(normal avg)'].mean(),
                         per_perf_based_stats['mean_severe_congestion_duration(length avg)'].mean() ,
                         per_perf_based_stats['severe_congestion_duration(length weighted sum)'].sum(),
                         per_perf_based_stats.vehicle_mile.sum(),
                         per_perf_based_stats.vehicle_hour.sum(),
                         per_perf_based_stats.vehicle_mile.sum() / np.maximum(per_perf_based_stats.vehicle_hour.sum(),0.1),
                         per_perf_based_stats.trk_vehicle_mile.sum(),
                         per_perf_based_stats.trk_vehicle_hour.sum(),
                         per_perf_based_stats.trk_vehicle_mile.sum() / np.maximum(per_perf_based_stats.trk_vehicle_hour.sum(),0.1),
                         per_perf_based_stats['HOV/HOT_delay'].sum(), 
                         per_perf_based_stats['HOV/HOT_person_delay'].sum(),
                         per_perf_based_stats['HOV/HOT_person_hour'].sum(), 
                         per_perf_based_stats['HOV/HOT_person_mile'].sum(),
                         per_perf_based_stats['HOV/HOT_person_mile'].sum() / np.maximum(per_perf_based_stats['HOV/HOT_person_hour'].sum(),0.1), 
                         per_perf_based_stats['HOV/HOT_person_delay'].sum() / np.maximum(per_perf_based_stats['HOV/HOT_person_hour'].sum(),0.1)
                         ])
        
        
            perf_based_stats = pd.DataFrame(total_stat,columns=header_df)
            ##perf_based_stats.to_csv(os.path.join(net_dir, f'perf_based_stat_{case[1]}.csv') , index=False)
            perf_based_stats.to_csv(os.path.join(net_dir, f'perf_stat_{sub_net}.csv') , index=False)
        
            total_net_stats.extend(total_stat) 
        
        if len(subnet_list) > 1:
            subnet_stats = pd.DataFrame(total_net_stats,columns=header_df)
            
            subnet_bd = subnet_list[0]
            subnet_nb = subnet_list[1]
            subnet_name = subnet_bd.rsplit('_', 1)[0]
            
            subnet_bd_df = subnet_stats[subnet_stats['subarea'] == subnet_bd].reset_index(drop=True)
            subnet_nb_df = subnet_stats[subnet_stats['subarea'] == subnet_nb].reset_index(drop=True)
            
            numeric_cols = subnet_bd_df.select_dtypes(include=[np.number]).columns
            print(numeric_cols)
            abs_diff = subnet_bd_df[numeric_cols] - subnet_nb_df[numeric_cols]
            #percentage_diff = ((subnet_bd_df[numeric_cols] - subnet_nb_df[numeric_cols]) / subnet_nb_df[numeric_cols]) * 100
            
            time_period_cols = [period + '_diff' for period in time_periods]
            if len(time_periods) > 1:  
                time_period_cols.append('total_diff')
    
            abs_diff.insert(0, 'time_period', time_period_cols)
            abs_diff.insert(0, 'subarea', subnet_name)
           
            
            print(abs_diff)
            diff_arr = abs_diff.values
            total_net_stats.extend(diff_arr) 
    
        
    
        net_stats = pd.DataFrame(total_net_stats,columns=header_df)
        net_stats.to_csv(os.path.join(parent_dir, 'total_perf.csv') , index=False)   



    
        
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
    start = time.process_time()

    
    time_periods = ['am','md','pm','nt']
    #time_periods = ['pmr']
    
    
    
    parent_dir = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\2024\2030 projects\Feb 10\gmns_nets\transit_allqvdf'
    #sub_net_list = ['CMP001', 'FFX134_BD','FFX134_NB', 'FFX138_BD', 'FFX138_NB',
     #               'LDN029_BD', 'LDN029_NB', 'LDN033_BD', 'LDN033_NB', 'LDN034', 'MAN003', 'PWC040_BD', 'PWC040_NB']
    
    sub_net_list = [item for item in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, item)) and not "statistics" in item]
    
    perf_based_stat(time_periods, parent_dir, sub_net_list)
    
    end = time.process_time()
    print('Total Running time: %s Seconds' % (end - start))
    


