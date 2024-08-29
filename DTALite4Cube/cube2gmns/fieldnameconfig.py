# DO NOT MODIFY KEYs!!!!

# time_period_dict = {
#     1: 'AM',
#     2: 'MD',
#     3: 'PM',
#     4: 'NT'
# }

time_period_dict = {
    'AM': 1,
    'MD': 2,
    'PM': 3,
    'NT': 4
}

# Field name mapping for cube node structure
cube_node_mapping = {
    'from_node_field': 'A',
    'to_node_field': 'B',
    'geometry_field': 'geometry'
}

# Field name mapping for cube base link structure
cube_base_link_mapping = {
    'link_id_field': 'ID',
    'from_node_field': 'A',
    'to_node_field': 'B',
    'geometry_field': 'geometry',
    'distance_field': 'DISTANCE',
    # 'lane_field': '',
    'area_type_field': 'ATYPE',
    'facility_type_field': 'FTYPE',
    'capacity_class': 'CAPCLASS',
    'speed_class': 'SPDCLASS'
}

cube_link_dependent_mapping = {
    'lane_field': '{time_period}LANE',
    'limit_field': '{time_period}LIMIT',
    'toll_field': '{time_period}TOLL'
}

# DTALite fields mapping
dtalite_node_mapping = {
    'node_id': 'node_id',
    'x_coord': 'x_coord',
    'y_coord': 'y_coord',
    'centroid': 'centroid',
    'zone_id': 'zone_id',
    'geometry': 'geometry'
}

dtalite_base_link_mapping = {
    'link_id': 'link_id',
    'from_node_id': 'from_node_id',
    'to_node_id': 'to_node_id',
    'lanes': 'lanes',
    'length': 'length',
    'dir_flag': 'dir_flag',
    'geometry': 'geometry',
    'free_speed': 'free_speed',
    'capacity': 'capacity',
    'link_type': 'link_type',
    'vdf_code': 'vdf_code',
}
# 'vdf_toll' is used for both 'vdf_toll{mode}' and 'vdf_toll{mode}{period_sequence}'
#   vdf_parameter: ['alpha', 'beta', 'qdf', 'plf', 'cp', 'cd', 'n', 's']
# dtalite_additional_link_mapping = {
#     'vdf_toll': 'vdf_toll{mode}',
#     'vdf_parameter': 'VDF_{qvdf_param}'
# }


dtalite_additional_link_mapping = {
    'vdf_toll': 'VDF_toll{mode}',
    'period_lanes': 'lanes{period_sequence}',
    'period_free_speed': 'free_speed{period_sequence}',
    'period_link_type': 'link_type{period_sequence}',
    'period_vdf_code': 'vdf_code{period_sequence}',
    'vdf_parameter': 'VDF_{qvdf_param}'
}