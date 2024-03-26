# @author       Jiawei Lu
# @email        jiaweil9@asu.edu
# @create date  2020/05/18 22:31
# @desc         [description]

import os
import openmatrix as omx
import numpy as np
# import pandas as pd
import csv
import time


def get_gmns_demand_from_omx(demand_dir, time_period_list):
    filenames = os.listdir(demand_dir)
    # output_dir = os.path.join(demand_dir, './OD_matrix_csv/')
    output_dir = demand_dir

    for filename in filenames:
        if not '.omx' in filename.lower() or 'Transit' in filename:
            continue

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for p in time_period_list:
            p = p.upper()
            if not p in filename:
                continue

            myfile = omx.open_file(os.path.join(demand_dir, filename))
            # print ("network path = ", demand_dir)
            print("Time period =", p)

            # print ('Net: %s  -----------------------------------------------------------------------------' % (
            # net_name))
            print('Shape:', myfile.shape())  # (100,100)
            print('Number of tables:', len(myfile))  # 3
            print('Table names:', myfile.list_matrices())  # ['m1','m2',',m3']

            # Work with data. Pass a string to select matrix by name:
            # -------------------------------------------------------
            start = time.process_time()

            m_apv = myfile[p + '_APVs']
            m_com = myfile[p + '_COMs']
            m_hv2 = myfile[p + '_HV2s']
            m_hv3 = myfile[p + '_HV3s']
            m_sov = myfile[p + '_SOVs']
            m_trk = myfile[p + '_TRKs']

            lane_uses = ['apv', 'com', 'hv2', 'hv3', 'sov', 'trk']
            # dir2 = './OD_matrix_csv/'

            # time_period = ['am','md','pm','nt']
            for lu in lane_uses:
                m_file = myfile[p + '_' + lu.upper() + 's']
                arr = np.array(m_file)
                output = os.path.join(output_dir, lu + '_' + p.lower() + '.csv')
                with open(output, 'a', newline='') as df:
                    f_csv = csv.writer(df)
                    f_csv.writerow(['o_zone_id', 'd_zone_id', 'volume'])
                    for i in range(len(arr)):
                        row = arr[i]
                        for j in range(len(row)):
                            if row[j] > 0:
                                f_csv.writerow([i + 1, j + 1, row[j]])

            end = time.process_time()
            print('Total running time for %s: %s Seconds' % (p, end - start))
