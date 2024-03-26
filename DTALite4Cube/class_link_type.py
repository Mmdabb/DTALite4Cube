from user_input import df

df.fillna('', inplace=True)
link_type = []

# Define the link types as dictionaries
for index, row in df.iterrows():
    link_type_data = {
        'link_type': row['link_type'],
        'link_type_name': row['link_type_name'],
        'name_description': row['name_description'],
        'type_code': row['type_code'],
        'traffic_flow_model': row['traffic_flow_model'],
        'allowed_uses_p1': row['allowed_uses_p1'],
        'allowed_uses_p2': row['allowed_uses_p2'],
        'allowed_uses_p3': row['allowed_uses_p3'],
        'free_speed_bike': row['free_speed_bike'],
        'free_speed_walk': row['free_speed_walk'],
        'capacity_bike': row['capacity_bike'],
        'capacity_walk': row['capacity_walk'],
        'lanes_bike': row['lanes_bike'],
        'lanes_walk': row['lanes_walk'],
        'k_jam_km': row['k_jam_km'],
        'meu_auto_bike': row['meu_auto_bike'],
        'meu_auto_walk': row['meu_auto_walk'],
        'meu_bike_walk': row['meu_bike_walk'],
        'meu_bike_auto': row['meu_bike_auto'],
        'meu_walk_bike': row['meu_walk_bike'],
        'meu_walk_auto': row['meu_walk_auto'],
        'emissions_auto_co2': row['emissions_auto_co2'],
        'emissions_auto_nox': row['emissions_auto_nox'],
        'emissions_bike_co2': row['emissions_bike_co2'],
        'emissions_bike_nox': row['emissions_bike_nox'],
        'emissions_walk_co2': row['emissions_walk_co2'],
        'emissions_walk_nox': row['emissions_walk_nox'],
        'emissions_ev_co2': row['emissions_ev_co2'],
        'emissions_ev_nox': row['emissions_ev_nox'],
        'emissions_truck_co2': row['emissions_truck_co2'],
        'emissions_truck_nox': row['emissions_truck_nox'],
        'emissions_bus_co2': row['emissions_bus_co2'],
        'emissions_bus_nox': row['emissions_bus_nox'],
        'emissions_hov_co2': row['emissions_hov_co2'],
        'emissions_hov_nox': row['emissions_hov_nox']
    }

    # Append the link types into a link type list
    link_type.append(link_type_data)

# Add the link type list to the link type dictionary 
link_type_dict = {'link_types': link_type}