import pandas as pd
import os
import traceback
import sys
import numpy as np
from datetime import datetime, timedelta
from .linkperformance_fieldconfig import link_required_fields_mapping, link_performance_fields_mapping, district_id_name_mapping

def link_performance_preprocess(network_dir, time_period_list, length_unit='mile',
                        speed_unit='mph', developer_mode=0):

    link_performance_csv_files = {}
    print('============================================================================================================')
    print(f'Reading link_performance.csv files...')
    for time_period in time_period_list:
        print(f'Time period: {time_period} --> link_performance_{time_period.lower()}.csv')
        link_perfomance_dir = os.path.join(network_dir, f'link_performance_{time_period.lower()}.csv')

        try:
            # Check if the file exists
            if not os.path.exists(link_perfomance_dir):
                raise FileNotFoundError(f"File not found: {link_perfomance_dir}")

            # Try to read the CSV file
            link_performance_csv = pd.read_csv(link_perfomance_dir)

            # Check if the DataFrame is empty
            if link_performance_csv.empty:
                raise pd.errors.EmptyDataError(f"File is empty: {link_perfomance_dir}")

        except FileNotFoundError as fnf_error:
            print(f"Error: {fnf_error}")
            continue
        except pd.errors.EmptyDataError:
            print(f"Error: File is empty: {link_perfomance_dir}")
            continue
        except ValueError as ve:
            print(f"Error: File is empty or invalid format: {link_perfomance_dir}")
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue

        link_performance_fieldnames = list(link_performance_csv)
        link_performance_fieldnames = [fieldname for fieldname in link_performance_fieldnames if fieldname]
        link_performance_fieldnames_set = set(link_performance_fieldnames)

        # if 'time_period' not in link_performance_fieldnames_set:
        #     link_performance_csv['time_period'] = time_period
        link_performance_csv['time_period'] = time_period

        required_fields_list = list(link_required_fields_mapping.values())
        required_fields_list.append(f'{time_period.upper()}LIMIT')
        print(f'Cheking for required fields in link_performance_{time_period.lower()}.csv ... \n'
              f'Required fields: {required_fields_list}')
        required_fields = set(required_fields_list)
        columns_to_merge = []
        for required_field in required_fields:
            if required_field not in link_performance_fieldnames_set:
                columns_to_merge.append(required_field)

        if columns_to_merge:
            print(f'Required fields {columns_to_merge} not found in link_performance_{time_period.lower()}.csv. \n'
                  f'Merging from link_{time_period.lower()}.csv ...')
            print(f"Reading link_{time_period.lower()}.csv ...")
            print(f'Time period: {time_period} --> link_{time_period.lower()}.csv')
            link_dir = os.path.join(network_dir, f'link_{time_period.lower()}.csv')

            try:
                # Check if the file exists
                if not os.path.exists(link_dir):
                    raise FileNotFoundError(f"File not found: {link_dir}")

                # Try to read the CSV file
                link_csv = pd.read_csv(link_dir)

                # Check if the DataFrame is empty
                if link_csv.empty:
                    raise pd.errors.EmptyDataError(f"File is empty: {link_dir}")

            except FileNotFoundError as fnf_error:
                print(f"Error: {fnf_error}")
            except pd.errors.EmptyDataError:
                print(f"Error: File is empty: {link_dir}")
            except ValueError as ve:
                print(f"Error: File is empty or invalid format: {link_dir}")
            except Exception as e:
                print(f"An unexpected error occurred during reading link_{time_period.lower()}.csv: {e}")

            link_fieldnames = list(link_csv)
            link_fieldnames = [fieldname for fieldname in link_fieldnames if fieldname]
            link_fieldnames_set = set(link_fieldnames)
            for required_field in required_fields:
                if required_field not in link_fieldnames_set:
                    if required_field == 'FT':
                        try:
                            link_csv['FT'] = (link_csv['link_type'] % 10).astype(int)
                        except KeyError as e:
                            sys.exit(f"KeyError: {e} - 'link_type' column not found in link_{time_period.lower()}.csv.")
                        except TypeError as e:
                            sys.exit(
                                f"TypeError: {e} - Non-numeric data in 'link_type' column of link_{time_period.lower()}.csv.")
                        except ValueError as e:
                            sys.exit(
                                f"ValueError: {e} - Unable to convert 'link_type' column of link_{time_period.lower()}.csv to integer.")
                    else:
                        sys.exit(
                            f'ERROR: required field ({required_field}) for generating performance summary does not exist in the link_{time_period.lower()}.csv')

            try:
                link_performance_csv['link_id'] = link_performance_csv['link_id'].astype(str)
            except KeyError:
                print(f"link_performance_{time_period.lower()}.csv: Missing link_id column")
            except Exception as e:
                print(f"link_performance_{time_period.lower()}.csv: Link_id data type conversion to str error: {e}")

            try:
                link_csv['link_id'] = link_csv['link_id'].astype(str)
            except KeyError:
                print(f"link_{time_period.lower()}.csv: Missing link_id column")
            except Exception as e:
                print(f"link_{time_period.lower()}.csv: Link_id data type conversion to str error: {e}")

            # Identify duplicate link_id values
            duplicate_link_ids_link_csv = link_csv[link_csv['link_id'].duplicated(keep=False)]
            if not duplicate_link_ids_link_csv.empty:
                print(f"Duplicate link_id values in link_{time_period.lower()}.csv:")
                print(duplicate_link_ids_link_csv)
                print("Keeping the first occurrence")
                link_csv = link_csv.drop_duplicates(subset='link_id', keep='first')

            duplicate_link_ids_link_perf_csv = link_performance_csv[
                link_performance_csv['link_id'].duplicated(keep=False)]
            if not duplicate_link_ids_link_perf_csv.empty:
                print(f"Duplicate link_id values in link_performance_{time_period.lower()}.csv:")
                print(duplicate_link_ids_link_perf_csv)
                print("Keeping the first occurrence")
                link_performance_csv = link_performance_csv.drop_duplicates(subset='link_id', keep='first')

            columns_to_merge.append('link_id')
            try:
                merged_link_performance_csv = pd.merge(link_performance_csv, link_csv[columns_to_merge], on='link_id',
                                                       how='left', suffixes=('_link_performance', '_link'))
                print(f'Required fields are successfully added to link_performance_{time_period.lower()}.csv.')
            except KeyError as e:
                print(
                    f"KeyError: {e}. Check if 'link_id' exists in both link_{time_period.lower()}.csv and link_performance_{time_period.lower()}.csv.")
            except TypeError as e:
                print(
                    f"TypeError: {e}. Ensure that the 'link_id' has the same data type in both link_{time_period.lower()}.csv and link_performance_{time_period.lower()}.csv.")
            except Exception as e:
                print(f"An unexpected error occurred during merging: {e}")

            link_performance_csv = merged_link_performance_csv.copy()

        print("All the features are satisfied")

        try:
            link_performance_csv['is_hov'] = (
                    (link_performance_csv['TOLLGRP'] == 2) |
                    (link_performance_csv[f'{time_period.upper()}LIMIT'] == 2) |
                    (link_performance_csv[f'{time_period.upper()}LIMIT'] == 3)
            ).astype(int)

        except KeyError as e:
            print(f"KeyError: {e} - One or more columns ('TOLLGRP', '{time_period.upper()}LIMIT') not found.")
        except TypeError as e:
            print(f"TypeError: {e} - Non-numeric data encountered in 'TOLLGRP' or '{time_period.upper()}LIMIT'.")
        except ValueError as e:
            print(
                f"ValueError: {e} - Error while converting data to integer in 'is_hov' column based on the ('TOLLGRP' == 2 or {time_period.upper()}LIMIT' == 2 or 3) conditions.")

        try:
            filtered_link_performance_csv = link_performance_csv[
                (link_performance_csv['TAZ'] > 1404) &
                (link_performance_csv['TAZ'] < 2820) &
                (link_performance_csv['FT'] > 0)
                ]

        except KeyError as e:
            print(f"KeyError: {e} - One or more columns ('TAZ', 'FT') not found.")
        except TypeError as e:
            print(f"TypeError: {e} - Non-numeric data encountered in 'TAZ' or 'FT'.")
        except ValueError as e:
            print(
                f"ValueError: {e} - Error while filtering link_performance_{time_period.lower()}.csv based on the (1404 < 'TAZ' <2820, 'FT' > 0) conditions.")

        volume_field = 'vehicle_volume' if 'vehicle_volume' in link_performance_fieldnames_set else 'volume'
        try:
            if filtered_link_performance_csv.empty or filtered_link_performance_csv[volume_field].sum() < 0.5:
                print(
                    f"Warning: Time period: {time_period} --> Filtering link_performance_{time_period.lower()}.csv based on conditions (1404 < 'TAZ' < 2820 and 'FT' > 0) resulted in an empty dataset or a total vehicle volume less than 0.5.")
                continue

        except KeyError as e:
            print(
                f"KeyError: {e} - The 'vehicle_volume' or 'volume' column does not exist in link_performance_{time_period.lower()}.csv.")
        except TypeError as e:
            print(
                f"TypeError: {e} - Non-numeric data encountered in 'vehicle_volume' or other operations in link_performance_{time_period.lower()}.csv.")
        except AttributeError as e:
            print(f"AttributeError: {e} - 'filtered_link_performance_csv' is not a DataFrame.")
        except ValueError as e:
            print(
                f"ValueError: {e} - Error while summing the 'vehicle_volume' values in link_performance_{time_period.lower()}.csv.")

        link_performance_csv_files[time_period] = filtered_link_performance_csv

    if link_performance_csv_files:
        link_performance_combined = pd.concat([link_performance_csv_files[time_period]
                                               for time_period in time_period_list
                                               if time_period in link_performance_csv_files], axis=0)

        # output_dir = os.path.join(network_dir, 'link_performance_combined.csv')
        # link_performance_combined.to_csv(output_dir, index=False)
        # print(f"Combined link performance data saved to: {output_dir}")

    else:
        sys.exit("No valid link_performance file were loaded to combine.")
        # return None  # Return None if no files are loaded


    if length_unit not in {'mile', 'meter'} or speed_unit not in {'mph', 'kph'}:
        sys.exit("Error: Invalid units. Length must be 'mile' or 'meter', and speed must be 'mph' or 'kph'.")

    if (length_unit == 'mile' and speed_unit == 'kph') or (length_unit == 'meter' and speed_unit == 'mph'):
        sys.exit("Error: Invalid unit combination. Use 'mile' with 'mph' or 'meter' with 'kph'.")

    link_performance_field_names = list(link_performance_combined)
    link_performance_field_names = [fieldname for fieldname in link_performance_field_names if fieldname]
    link_performance_field_names_set = set(link_performance_field_names)

    fftt_field_name = link_performance_fields_mapping['fftt']
    free_speed_field_name = link_required_fields_mapping['free_speed']  # must be exactly the same as required field
    length_field_name = link_required_fields_mapping['length']  # must be exactly the same as required field
    tt_field_name = link_performance_fields_mapping['tt']
    speed_field_name = link_performance_fields_mapping['speed']
    speed_ratio_field_name = link_performance_fields_mapping['speed_ratio']
    person_volume_field_name = link_performance_fields_mapping['person_volume']
    severe_congestion_field_name = link_performance_fields_mapping['severe_congestion']
    truck_volume_field_name = link_performance_fields_mapping['truck_volume']

    if 'volume' not in link_performance_field_names_set and 'vehicle_volume' not in link_performance_field_names_set:
        sys.exit("Error: Column 'volume' or 'vehicle_volume' is missing from link performance files")
    else:
        vehicle_volume_field_name = 'vehicle_volume' if 'vehicle_volume' in link_performance_field_names_set else 'volume'

    try:
        link_performance_combined[length_field_name] = link_performance_combined[length_field_name].astype(float)
        if length_unit == 'meter':
            link_performance_combined['length'] = link_performance_combined[length_field_name] * 1.609
        else:
            link_performance_combined['length'] = link_performance_combined[length_field_name]

    except KeyError as e:
        sys.exit(f"KeyError: {e} - '{length_field_name}' column not found in link performance files.")
    except ValueError as e:
        sys.exit(f"ValueError: {e} - Ensure that '{length_field_name}' column contains numeric data.")
    except Exception as e:
        sys.exit(f"An unexpected error occurred: {e}")

    try:
        if fftt_field_name not in link_performance_field_names_set:
            if free_speed_field_name not in link_performance_field_names_set:
                raise KeyError(f"'{free_speed_field_name}' column is missing from the link performance files.")

            link_performance_combined[free_speed_field_name] = link_performance_combined[free_speed_field_name].astype(
                float)

            link_performance_combined[fftt_field_name] = link_performance_combined['length'] / np.where(
                link_performance_combined[free_speed_field_name] > 0,
                link_performance_combined[free_speed_field_name],
                np.nan
            )

            # Check for NaN values and report if any are created
            invalid_speed_mask = link_performance_combined[free_speed_field_name] <= 0
            invalid_speed_indices = link_performance_combined[invalid_speed_mask].index
            if invalid_speed_indices.any():
                print(
                    f"Warning: {len(invalid_speed_indices)} rows have negative or zero values in {free_speed_field_name}.")
                print("Row indices with invalid values:", invalid_speed_indices.tolist())
            if link_performance_combined[fftt_field_name].isna().any():
                print(f"Warning: NaN values generated in '{fftt_field_name}' column.")

    except KeyError as e:
        sys.exit(f"KeyError: {e}. Please check the column names.")
    except ValueError as e:
        sys.exit(f"ValueError: {e}. Ensure that '{free_speed_field_name}' column contains numeric data.")
    except Exception as e:
        sys.exit(f"An unexpected error occurred: {e}")

    # Create travel time if it does not exist in link_performance.csv
    try:
        if tt_field_name not in link_performance_field_names_set:
            if speed_field_name not in link_performance_field_names_set:
                raise KeyError(f"'{speed_field_name}' column is missing from the link performance files.")

            link_performance_combined[speed_field_name] = link_performance_combined[speed_field_name].astype(float)

            link_performance_combined[tt_field_name] = link_performance_combined['length'] / np.where(
                link_performance_combined[speed_field_name] > 0,
                link_performance_combined[speed_field_name],
                np.nan
            )

            # Check for NaN values and report if any are created
            invalid_speed_mask = link_performance_combined[speed_field_name] <= 0
            invalid_speed_indices = link_performance_combined[invalid_speed_mask].index
            if invalid_speed_indices.any():
                print(f"Warning: {len(invalid_speed_indices)} rows have negative or zero values in {speed_field_name}.")
                print("Row indices with invalid values:", invalid_speed_indices.tolist())
            if link_performance_combined[fftt_field_name].isna().any():
                print(f"Warning: NaN values generated in '{tt_field_name}' column.")

    except KeyError as e:
        sys.exit(f"KeyError: {e}. Please check the column names.")
    except ValueError as e:
        sys.exit(f"ValueError: {e}. Ensure that '{speed_field_name}' column contains numeric data.")
    except Exception as e:
        sys.exit(f"An unexpected error occurred: {e}")

    try:
        if speed_ratio_field_name not in link_performance_field_names_set:
            link_performance_combined[speed_ratio_field_name] = link_performance_combined[speed_field_name] / np.where(
                link_performance_combined[free_speed_field_name] > 0,
                link_performance_combined[free_speed_field_name],
                np.nan
            )
    except KeyError as e:
        sys.exit(f"KeyError: {e}. Please check the column names.")
    except Exception as e:
        sys.exit(f"An unexpected error occurred: {e}")


    try:
        # Handle NaN
        #         link_performance_combined[tt_field_name].fillna(0, inplace=True)
        #         link_performance_combined[fftt_field_name].fillna(0, inplace=True)
        #         link_performance_combined[speed_ratio_field_name].fillna(1, inplace=True)
        link_performance_combined['delay'] = np.where(
            (link_performance_combined[tt_field_name] - link_performance_combined[fftt_field_name] > 0) &
            (link_performance_combined[speed_ratio_field_name] < 1),
            link_performance_combined[tt_field_name] - link_performance_combined[fftt_field_name], 0)

    except KeyError as e:
        sys.exit(f"KeyError: {e}. Column is missing from the link performance files")
    except Exception as e:
        sys.exit(f"An unexpected error occurred: {e}")

    if developer_mode:
        invalid_tt_mask = (link_performance_combined[tt_field_name] - link_performance_combined[fftt_field_name] < 0) & \
                          (link_performance_combined[speed_ratio_field_name] < 1)
        invalid_tt_indices = link_performance_combined[invalid_tt_mask].index
        if invalid_tt_mask.any():
            print(f"Warning: {len(invalid_tt_indices)} rows have negative delay (travel time < fftt)!")
            print("Row indices with invalid values:", invalid_tt_indices.tolist())


    try:
        #         link_performance_combined[person_volume_field_name] = link_performance_combined[person_volume_field_name].fillna(0)
        #         link_performance_combined['delay'] = link_performance_combined['delay'].fillna(0)
        link_performance_combined['person_delay'] = link_performance_combined[person_volume_field_name] * \
                                                    link_performance_combined['delay']
    except KeyError as e:
        sys.exit(f"KeyError: {e}. Column is missing from the link performance files")
    except (TypeError, ValueError) as e:
        sys.exit(
            f"Error during 'person_delay' calculation: {e}. Check for non-numeric values or incompatible data types in 'delay' or {person_volume_field_name}.")


    try:
        link_performance_combined['person_hour'] = link_performance_combined[person_volume_field_name] * \
                                                   link_performance_combined[tt_field_name]
    except KeyError as e:
        sys.exit(f"KeyError: {e}. Column is missing from the link performance files")
    except (TypeError, ValueError) as e:
        sys.exit(
            f"Error during 'person_hour' calculation: {e}. Check for non-numeric values or incompatible data types in {tt_field_name} or {person_volume_field_name}.")


    try:
        link_performance_combined['person_mile'] = link_performance_combined[person_volume_field_name] * \
                                                   link_performance_combined['length']
    except KeyError as e:
        sys.exit(f"KeyError: {e}. Column is missing from the link performance files")
    except (TypeError, ValueError) as e:
        sys.exit(
            f"Error during 'person_mile' calculation: {e}. Check for non-numeric values or incompatible data types in 'length' or {person_volume_field_name}.")


    try:
        link_performance_combined['length_weighted_P'] = link_performance_combined[severe_congestion_field_name] * \
                                                         link_performance_combined['length']
    except KeyError as e:
        print(f"KeyError: {e}. Column is missing from the link performance files")
    except (TypeError, ValueError) as e:
        print(
            f"Error during 'length_weighted_P' calculation: {e}. Check for non-numeric values or incompatible data types in 'length' or {severe_congestion_field_name}.")


    try:
        link_performance_combined['vehicle_mile'] = link_performance_combined[vehicle_volume_field_name] * \
                                                    link_performance_combined['length']
    except KeyError as e:
        sys.exit(f"KeyError: {e}. Column is missing from the link performance files")
    except (TypeError, ValueError) as e:
        sys.exit(
            f"Error during 'vehicle_mile' calculation: {e}. Check for non-numeric values or incompatible data types in 'length' or {vehicle_volume_field_name}.")


    try:
        link_performance_combined['vehicle_hour'] = link_performance_combined[vehicle_volume_field_name] * \
                                                    link_performance_combined[tt_field_name]
    except KeyError as e:
        sys.exit(f"KeyError: {e}. Column is missing from the link performance files")
    except (TypeError, ValueError) as e:
        sys.exit(
            f"Error during 'vehicle_hour' calculation: {e}. Check for non-numeric values or incompatible data types in 'length' or {tt_field_name}.")


    try:
        link_performance_combined['trk_vehicle_mile'] = link_performance_combined[truck_volume_field_name] * \
                                                        link_performance_combined['length']
    except KeyError as e:
        sys.exit(f"KeyError: {e}. Column is missing from the link performance files")
    except (TypeError, ValueError) as e:
        sys.exit(
            f"Error during trk_vehicle_mile calculation: {e}. Check for non-numeric values or incompatible data types in 'length' or {truck_volume_field_name}.")


    try:
        link_performance_combined['trk_vehicle_hour'] = link_performance_combined[truck_volume_field_name] * \
                                                        link_performance_combined[tt_field_name]
    except KeyError as e:
        sys.exit(f"KeyError: {e}. Column is missing from the link performance files")
    except (TypeError, ValueError) as e:
        sys.exit(
            f"Error during trk_vehicle_hour calculation: {e}. Check for non-numeric values or incompatible data types in 'length' or {tt_field_name}.")


    # Create conditional mask for hov flags
    hov_flag_mask = link_performance_combined['is_hov'] == 1
    link_performance_combined['hov_delay'] = link_performance_combined['delay'].where(hov_flag_mask)
    link_performance_combined['hov_person_delay'] = link_performance_combined['person_delay'].where(hov_flag_mask)
    link_performance_combined['hov_person_hour'] = link_performance_combined['person_hour'].where(hov_flag_mask)
    link_performance_combined['hov_person_mile'] = link_performance_combined['person_mile'].where(hov_flag_mask)


    link_performance_combined_dir = os.path.join(network_dir, 'link_performance_combined_processed.csv')
    link_performance_combined.to_csv(link_performance_combined_dir, index=False)
    print(f"Processed link performance data saved to: {link_performance_combined_dir}")
    print('============================================================================================================')

    return link_performance_combined