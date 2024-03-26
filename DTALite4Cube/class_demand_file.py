from user_input import demand_file, demand_mode, demand_title, demand_scale_factor

demand_files = []
temp = 0
index = 0

# Define the demand files as dictionaries
for i,j,k in zip(demand_file, demand_mode, demand_title):
    if k == 'am':
        index = 0
    elif k == 'md':
        index = 1
    elif k == 'pm':
        index = 2
    elif k == 'nt':
        index = 3
        
    demand_file = {
           'file_sequence_no': temp+1,
           'scenario_index_vector': index,
           'file_name': i,
           'demand_period': k,
           'mode_type': j,
           'format_type': 'column',
           'scale_factor': demand_scale_factor,
           'departure_time_profile_no': 1 
    }
    temp = temp + 1
    
    # Append the demand files into a demand files list
    demand_files.append(demand_file)

# Add the demand files list to the demand file dictionary 
demand_file_dict = {'demand_files': demand_files}