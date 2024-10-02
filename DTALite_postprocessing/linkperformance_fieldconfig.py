# Field name mapping
link_required_fields_mapping = {
    'length': 'length_in_mile',
    'free_speed': 'free_speed',
    'taz_code': 'TAZ',
    'district_id': 'district_id',
    'field_type': 'FT',
    'toll_grp': 'TOLLGRP'
}

# old version and TAPLite
link_performance_fields_mapping = {
    'fftt': 'fftt',
    'tt': 'tt',
    'speed': 'speed',
    'speed_ratio': 'speed_ratio',
    'person_volume': 'person_volume',
    # 'person_volume': 'volume',      # for Taplite
    'truck_volume': 'person_vol_trk',
    # 'truck_volume': 'mod_vol_trk',  # for Taplite
    'severe_congestion': 'severe_congestion_duration_in_h',
    # 'severe_congestion': 'Severe_Congestion_P'      # for TAPLite
}


# # New Verssion DTALite
# link_performance_fields_mapping = {
#     'fftt': 'fftt',
#     'tt': 'travel_time',
#     'speed': 'speed_mph',
#     'speed_ratio': 'speed_ratio',
#     'person_volume': 'person_volume',
#     'truck_volume': 'vehicle_vol_trk',
#     'severe_congestion': 'severe_congestion_duration_in_h'
# }


district_id_name_mapping = {
    2: 'Arlington',
    1: 'Alexandria',
    3: 'Fairfax',
    4: 'Fairfax City',
    5: 'Falls Church',
    6: 'Loudoun',
    9: 'Prince William',
    7: 'Manassas',
    8: 'Manassas Park',
    10: 'Others'
}

length_unit = 'mile'
speed_unit = 'mph'