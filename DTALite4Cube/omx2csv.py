import os
import openmatrix as omx
import numpy as np
import csv
import time
from tqdm import tqdm


def export_matrix_data(output_dir, time_period, lane_uses, matrix_file):
    for lu in lane_uses:
        matrix = matrix_file[f"{time_period}_{lu.upper()}s"]
        arr = np.array(matrix)

        output_file_name = f"{lu}_{time_period.lower()}.csv"
        if lu == 'hv2':
            output_file_name = f"hov2_{time_period.lower()}.csv"
        elif lu == 'hv3':
            output_file_name = f"hov3_{time_period.lower()}.csv"

        output = os.path.join(output_dir, output_file_name)

        with open(output, 'w', newline='') as df:
            print(f"Writing {output_file_name} ...", end="")
            f_csv = csv.writer(df)
            f_csv.writerow(['o_zone_id', 'd_zone_id', 'volume'])

            total_entries = sum(1 for i in range(len(arr)) for j in range(len(arr[i])) if arr[i][j] > 0)
            update_frequency = 1000  # Update every 1000 entries
            counter = 0

            with tqdm(total=total_entries, desc=f"Writing {output_file_name}", unit=" entry") as pbar:
                for i in range(len(arr)):
                    for j in range(len(arr[i])):
                        if arr[i][j] > 0:
                            f_csv.writerow([i + 1, j + 1, arr[i][j]])
                            counter += 1
                            if counter % update_frequency == 0:
                                pbar.update(update_frequency)
                # Update any remaining entries
                pbar.update(counter % update_frequency)



            # for i in range(len(arr)):
            #     for j in range(len(arr[i])):
            #         if arr[i][j] > 0:
            #             f_csv.writerow([i + 1, j + 1, arr[i][j]])
            #
            # print(f" done")

# Main function to process OMX files
def get_gmns_demand_from_omx(demand_dir, time_period_list):
    filenames = os.listdir(demand_dir)
    output_dir = demand_dir  # Can be customized if needed

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    lane_uses = ['apv', 'com', 'hv2', 'hv3', 'sov', 'trk']

    for filename in filenames:
        if '.omx' not in filename.lower() or 'transit' in filename.lower():
            continue

        # Check for time period in filename
        for time_period in time_period_list:
            time_period_upper = time_period.upper()

            if time_period_upper in filename:
                print(f"Processing file: {filename} for time period: {time_period_upper}")

                myfile = omx.open_file(os.path.join(demand_dir, filename))
                print("Shape:", myfile.shape())  # (100,100)
                print("Number of tables:", len(myfile))  # 3
                print("Table names:", myfile.list_matrices())  # ['m1','m2',',m3']

                start = time.process_time()

                # Export matrices for the current time period
                export_matrix_data(output_dir, time_period_upper, lane_uses, myfile)

                myfile.close()
                end = time.process_time()

                print(f"Total running time for {time_period_upper}: {end - start} seconds")

# Example usage:
# demand_dir = '/path/to/demand_dir'
# time_period_list = ['am', 'md', 'pm', 'nt']
# get_gmns_demand_from_omx(demand_dir, time_period_list)