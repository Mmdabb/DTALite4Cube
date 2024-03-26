# Define the demand subareas as dictionaries
subarea_1 = {
    'activate': 0,
    'subarea_geometry': 'POLYGON ((-180 -90, 180 -90, 180 90, -180 90, -180 -90))',
    'file_name': 'demand.csv',
    'format_type': 'column'
}

# Append the demand subareas into a demand subareas list
demand_subareas = []

demand_subareas.append(subarea_1)

# Add the demand subareas list to the demand subarea dictionary 
demand_subarea_dict = {}
demand_subarea_dict = {'demand_files_for_subarea': demand_subareas}