import pandas as pd
import os


def link_performanc_preprocess(network_dir, time_period_list):
    link_performance_csv_files = {}
    print(f'Reading link_performance.csv files...')
    for time_period in time_period_list:
        print(f'Time period: {time_period} --> link_performance_{time_period.lower()}.csv')
        link_perfomance_dir = os.path.join(network_dir, f'link_performance_{time_period.lower()}.csv')

        try:
            # Check if the file exists
            if not os.path.exists(link_perfomance_dir):
                raise FileNotFoundError(f"File not found: {link_perfomance_dir}")

            # Try to read the CSV file
            link_performance_csv_files[time_period] = pd.read_csv(link_perfomance_dir)

            # Check if the DataFrame is empty
            if link_performance_csv_files[time_period].empty:
                raise pd.errors.EmptyDataError(f"File is empty: {link_perfomance_dir}")

        except FileNotFoundError as fnf_error:
            print(f"Error: {fnf_error}")
        except pd.errors.EmptyDataError as ede_error:
            print(f"Error: {ede_error}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    link_performance_combined = pd.concat([link_performance_csv_files[time_period] for time_period
                                           in time_period_list], axis=0)

    output_dir = os.path.join(network_dir, 'total_perf.csv')
    link_performance_combined.to_csv(output_dir, index=False)



def performance_stats_summary(network_dir, time_period):
    link_perfomance_dir = os.path.join(network_dir, f'link_performanc_{time_period}.csv')
    link_performance_data = pd.read_csv(link_perfomance_dir)
