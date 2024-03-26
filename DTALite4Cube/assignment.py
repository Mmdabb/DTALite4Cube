# -*- coding: utf-8 -*-
"""
Created on Sat Feb 19 02:52:22 2022

@author: Asus
"""

import pandas as pd
import numpy as np
import os
import shutil
import csv
import time



def create_link_qvdf(net_dir):

    link_df = pd.read_csv(net_dir+'\\'+"link.csv") 
    qvdf_df = pd.read_csv('./input_files/' + "whole_net_link_qvdf.csv")
    
    link_df['pair'] = link_df['from_node_id'].astype(str) + '->' + link_df['to_node_id'].astype(str)
    link_id_dict = dict(zip(link_df.pair, link_df.link_id))
    
    
    qvdf_df['pair'] = qvdf_df['from_node_id'].astype(str) + '->' + qvdf_df['to_node_id'].astype(str)
    qvdf_df['new_link_id'] = qvdf_df.apply(lambda x: link_id_dict.setdefault(x.pair, -1) if x.data_type == 'link' else "", axis=1)
    
    filtered_qvdf_df = qvdf_df[(qvdf_df['new_link_id'] != -1) | (qvdf_df['data_type'] == 'vdf_code')].copy()
    filtered_qvdf_df['link_id'] = filtered_qvdf_df['new_link_id']
    
    #filtered_qvdf_df = filtered_qvdf_df.drop(['pair', 'flag'], axis=1).copy()
    #filtered_qvdf_df.to_csv(net_dir+'\\'+"link_qvdf.csv", index=False)
    filtered_qvdf_df.to_csv(net_dir+'\\'+"link_qvdf.csv", index=False)
    print('link_qvdf has created')
    
    

def create_link_qvdf_0(net_dir):
    
    # Read the link.csv file
    link_df = pd.read_csv(net_dir+'\\'+'link.csv')

    # Read the whole_net_link_qvdf.csv file
    whole_net_link_qvdf_df = pd.read_csv('./input_files/' + 'whole_net_link_qvdf.csv')

    # Create the "pair" column in both dataframes
    link_df['pair'] = link_df['from_node_id'].astype(str) + '->' + link_df['to_node_id'].astype(str)
    whole_net_link_qvdf_df['pair'] = whole_net_link_qvdf_df['from_node_id'].astype(str) + '->' + whole_net_link_qvdf_df['to_node_id'].astype(str)

    # Filter pairs that exist in both dataframes
    common_pairs = set(link_df['pair']).intersection(whole_net_link_qvdf_df['pair'])
    print(common_pairs)
    filtered_whole_net_link_qvdf_df = whole_net_link_qvdf_df[whole_net_link_qvdf_df['pair'].isin(common_pairs)]

    # Combine the filtered data and vdf_code data
    final_df = pd.concat([filtered_whole_net_link_qvdf_df, whole_net_link_qvdf_df[whole_net_link_qvdf_df['data_type'] == 'vdf_code']])

    # Save the final dataframe to link_qvdf.csv
    final_df.to_csv(net_dir+'\\'+'link_qvdf.csv', index=False)
    print('link_qvdf has created')
    
    

def run_dtalite(net_dir, time_periods):
    
    owd = os.getcwd()
    #print('current directory:\n', owd)
    os.chdir(net_dir)
    #print('changing directory to :\n', net_dir)
    
    network_name = net_dir.split('\\')[-1]
    print(network_name)
    
    for time_period in time_periods:
        print('time period = ', time_period)
        
        if time_period == 'nt' and os.path.exists('link_qvdf.csv'):
            try:
                os.remove(f'link_qvdf_{time_period}.csv')
            except:
                pass
            os.rename('link_qvdf.csv',f'link_qvdf_{time_period}.csv')
            
        else:
            try:
                shutil.copyfile('link_qvdf_nt.csv','link_qvdf.csv')
            except:
                pass
            
        shutil.copyfile(f'settings_{time_period}.csv', 'settings.csv')
        
        print('running DTALite')
        os.system('DTALite_0324b.exe')
        
        #rename the link performance file before next run
        try:
            shutil.copyfile('link_performance.csv', f'link_performance_{time_period}.csv')
        except:
            print('Warning: link_performance.csv cannot be copied to link_performance_%s.csv. Trying again ...' % (time_period))
            
            try:
                shutil.copyfile('link_performance.csv', f'link_performance_{time_period}.csv')
            except:
                try:
                    os.rename('link_performance.csv', f'link_performance_{time_period}.csv')
                except:
                    print('Warning: Write permission has not been granted for the destination folder and link_performance.csv cannot be replaced. Skipping to the next run ...')
                    pass
                
    #back to the parent directory
    os.chdir(owd)
    #print('changing directory to :\n', owd)
    
    




def create_assignment_directory(source_directory, destination_directory, network_list, time_periods):
    for network in network_list:
        network_dir = os.path.join(source_directory, network)
        
        source_demand_folder = [demand for demand in os.listdir(network_dir) 
               if os.path.isdir(os.path.join(network_dir, demand)) and 'Demand' in demand]
        if len(source_demand_folder) != 1:
            raise ValueError(f"{network}: There should be exactly one 'Demand' folder per network.")
        
        source_network_folder = [ntwk for ntwk in os.listdir(network_dir) 
               if os.path.isdir(os.path.join(network_dir, ntwk)) and 'NTWK' in ntwk]
        if len(source_network_folder) != 1:
            raise ValueError(f"{network}: There should be exactly one 'NTWK' folder per network.")
        
        destination_network_dir = os.path.join(destination_directory, network)
        if not os.path.exists(destination_network_dir):
            os.makedirs(destination_network_dir, exist_ok=True)  # Create if it doesn't exist
        
        for source_demand in source_demand_folder:
            source_demand_dir = os.path.join(network_dir, source_demand)
            source_od_matrix_csv = os.path.join(source_demand_dir, 'OD_matrix_csv')
            if os.path.exists(source_od_matrix_csv):
                destination_od_matrix_csv = os.path.join(destination_network_dir, 'OD_matrix_csv')
                if not os.path.exists(destination_od_matrix_csv):
                    for root, dirs, files in os.walk(source_od_matrix_csv):
                        for file in files:
                            src_file = os.path.join(root, file)
                            dest_file = os.path.join(destination_network_dir, file)
                            shutil.copy(src_file, dest_file)
                
        for source_network in source_network_folder:
            source_network_dir = os.path.join(network_dir, source_network)
            source_link_csv = os.path.join(source_network_dir, 'link.csv')
            source_node_csv = os.path.join(source_network_dir, 'node.csv')
            
            if os.path.exists(source_link_csv):
                destination_link_csv = os.path.join(destination_network_dir, 'link.csv')
                if not os.path.exists(destination_link_csv):
                    shutil.copy(source_link_csv, destination_link_csv)
                    
            if os.path.exists(source_node_csv):
                destination_node_csv = os.path.join(destination_network_dir, 'node.csv')
                if not os.path.exists(destination_node_csv):
                    shutil.copy(source_node_csv, destination_node_csv)
                    
        #time_periods = ['am','md','pm','nt']
        for time_period in time_periods:
            source_setting_csv = os.path.join('./input_files/', f'settings_{time_period}.csv')
            destination_setting_csv = os.path.join(destination_network_dir, f'settings_{time_period}.csv')
            if not os.path.exists(destination_setting_csv):
                shutil.copy(source_setting_csv, destination_setting_csv)
                
        source_dtalite_exe = os.path.join('./input_files/', 'DTALite_0324b.exe')
        destination_dtalite_exe = os.path.join(destination_network_dir, 'DTALite_0324b.exe')
        if not os.path.exists(destination_dtalite_exe):
            shutil.copy(source_dtalite_exe, destination_dtalite_exe)
            



            

if __name__ == "__main__":
    start = time.process_time()
    
    #time_periods = ['am','md','pm','nt','pmr']
    time_periods = ['am','md','pm','nt']
    #time_periods = ['pmr']
        
    source_directory = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\2024\2030 projects\Feb 10\cube_nets\2045_transit'
    assignment_dir   = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\2024\2030 projects\Feb 10\gmns_nets\2045_transit_bpr'
    
    
    #network_list = ['PWC042']
    #network_list = ['MAN003', 'PWC040_BD','PWC040_NB', 'PWC042']
    #network_list = [item for item in os.listdir(source_directory) if os.path.isdir(os.path.join(source_directory, item))]
    
    source_network_list = [item for item in os.listdir(source_directory) if os.path.isdir(os.path.join(source_directory, item)) and not "statistics" in item]
    #create_assignment_directory(source_directory, assignment_dir, source_network_list, time_periods)
    
    assignment_network_list = [item for item in os.listdir(assignment_dir) if os.path.isdir(os.path.join(assignment_dir, item)) and not "statistics" in item]
    
    
    
    for network in assignment_network_list:
        net_dir = os.path.join(assignment_dir, network)
            
        print("network = ", network)
            
        if os.path.exists(net_dir):
            #create_link_qvdf(net_dir)
            run_dtalite(net_dir, time_periods)
        else:
            print(f"File for network {network} does not exist in the network folder")
            continue
    
    
   