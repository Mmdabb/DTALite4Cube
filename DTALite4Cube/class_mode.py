from user_input import modes, modes_dedicated, modes_person

mode_types = []

# Define the mode type as dictionaries
for i in range(len(modes)):
    mode = 'mode' + modes[i]
    mode = {
        'mode_type': modes[i],
        'mode_type_index': i,
        'name': modes[i],
        'vot': 10,
        'multimodal_dedicated_assignment_flag': modes_dedicated[i],
        'person_occupancy': modes_person[i],
        'headway_in_sec': 1.5,
        'DTM_real_time_info_type': 0,
        'activate': 1    
    }

    # Append the modes into a mode types list
    mode_types.append(mode)

# Add the mode types list to the mode types dictionary 
mode_types_dict = {'mode_types': mode_types}