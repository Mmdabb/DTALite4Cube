time_period_dict = {
    'AM': 1,
    'MD': 2,
    'PM': 3,
    'NT': 4
}

# Define the time period values from the table
vot_time_periods = {# [DRIVE, HOV2, HOV3, COMMERCIAL, TRUCK, AIR]
    'AM': [24, 40, 60, 30, 30, 30],
    'MD': [20, 15, 15, 30, 30, 30],
    'PM': [20, 30, 60, 30, 30, 30],
    'NT': [20, 15, 15, 30, 30, 30]
}

# The original agent_types dictionary
agent_types_dict = { # [name, vot, flow_type, pce, person_occupancy]
    'sov': ['DRIVE', 24, 0, 1, 1],
    'hov2': ['HOV2', 40, 0, 1, 2],
    'hov3': ['HOV3', 60, 0, 1, 3.5],
    'com': ['COMMERCIAL TRUCK', 30, 0, 1, 1],
    'trk': ['TRUCK', 30, 0, 1, 1],
    'apv': ['AIR', 30, 0, 1, 1.6]
}

link_type_dict = {
    0: ["Centroids", "", "c", 0],
    100: ["Centroids", "", "c", 0],
    101: ["Freeways", "", "f", 0],
    102: ["Major Arterial", "", "a", 0],
    103: ["Minor Arterial", "", "a", 0],
    104: ["Collector", "", "a", 0],
    105: ["Expressway", "", "f", 0],
    106: ["Ramp", "", "r", 0],
    200: ["Centroids", "", "c", 0],
    201: ["Freeways", "", "f", 0],
    202: ["Major Arterial", "", "a", 0],
    203: ["Minor Arterial", "", "a", 0],
    204: ["Collector", "", "a", 0],
    205: ["Expressway", "", "f", 0],
    206: ["Ramp", "", "r", 0],
    300: ["Centroids", "", "c", 0],
    301: ["Freeways", "", "f", 0],
    302: ["Major Arterial", "", "a", 0],
    303: ["Minor Arterial", "", "a", 0],
    304: ["Collector", "", "a", 0],
    305: ["Expressway", "", "f", 0],
    306: ["Ramp", "", "r", 0],
    400: ["Centroids", "", "c", 0],
    401: ["Freeways", "", "f", 0],
    402: ["Major Arterial", "", "a", 0],
    403: ["Minor Arterial", "", "a", 0],
    404: ["Collector", "", "a", 0],
    405: ["Expressway", "", "f", 0],
    406: ["Ramp", "", "r", 0],
    500: ["Centroids", "", "c", 0],
    501: ["Freeways", "", "f", 0],
    502: ["Major Arterial", "", "a", 0],
    503: ["Minor Arterial", "", "a", 0],
    504: ["Collector", "", "a", 0],
    505: ["Expressway", "", "f", 0],
    506: ["Ramp", "", "r", 0],
    600: ["Centroids", "", "c", 0],
    601: ["Freeways", "", "f", 0],
    602: ["Major Arterial", "", "a", 0],
    603: ["Minor Arterial", "", "a", 0],
    604: ["Collector", "", "a", 0],
    605: ["Expressway", "", "f", 0],
    606: ["Ramp", "", "r", 0]
}