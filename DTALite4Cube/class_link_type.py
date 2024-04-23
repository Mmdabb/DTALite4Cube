class LinkType:
    def __init__(self, link_type_defaults):
        # self.link_type_defaults = link_type_defaults
        for default_attributes, default_value in link_type_defaults.items():
            setattr(self, default_attributes, default_value)


# Define default attributes and values for LinkType class
link_type_defaults = {
    'link_type': '',
    'link_type_name': '',
    'name_description': '',
    'type_code': 'f',
    'traffic_flow_model': '',
    'allowed_uses_p1': '',
    'allowed_uses_p2': '',
    'allowed_uses_p3': '',
    'k_jam_km': 300,
    'emissions_auto_co2': '20785.99541;0.0002;0.0042;0.3412',
    'emissions_auto_nox': '5.53516;0.0003;0.0043;0.0959',
    'emissions_bike_co2': '0;0;0;0',
    'emissions_bike_nox': '0;0;0;0',
    'emissions_walk_co2': '0;0;0;0',
    'emissions_walk_nox': '0;0;0;0',
    'emissions_ev_co2': '10392.99771;0.0002;0.0042;0.3412',
    'emissions_ev_nox': '2;0.0003;0.0043;0.0959',
    'emissions_truck_co2': '23816.14583;0.0002;0.0042;0.3412',
    'emissions_truck_nox': '6.342370833;0.0003;0.0043;0.0959',
    'emissions_bus_co2': '25115.20833;0.0002;0.0042;0.3412',
    'emissions_bus_nox': '6.688318333;0.0003;0.0043;0.0959',
    'emissions_hov_co2': '10392.99771;0.0002;0.0042;0.3412',
    'emissions_hov_nox': '2;0.0003;0.0043;0.0959'
}
