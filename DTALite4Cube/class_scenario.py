from user_input import scenario_gen

scenarios = []

# Define the scenarios as dictionaries
for i in range(len(scenario_gen)):
    scenario = {
        'scenario_index': i,
        'year': 2025,
        'scenario_name': scenario_gen[i],
        'activate': 0
    }
    
    # Append the scenarios into a scenarios list
    scenarios.append(scenario)

# Add the scenarios list to the scenarios dictionary 
scenario_dict = {'scenarios': scenarios}