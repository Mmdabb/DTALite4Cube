class DTMs:
    def __init__(self, dtm_defaults):
        for default_attribute, default_value in dtm_defaults.items():
            setattr(self, default_attribute, default_value)

    def update_dtm(self, **kwargs):
        updated_attributes = set()
        for attribute, value in kwargs.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)
                updated_attributes.add(attribute)
            else:
                print(f"Ignoring unknown attribute: {attribute}")

        not_updated_attributes = set(vars(self).keys()) - updated_attributes
        for attribute in not_updated_attributes:
            # add if attribue is None exit
            print(f"Warning: {attribute} has not been updated and is set to: {getattr(self, attribute)}")


# Define the default DTMs as dictionaries
dtm_defaults = {
    'dtm_id': 1,
    'dtm_type': 'lane_closure',
    'from_node_id': 1,
    'to_node_id': 3,
    'final_lanes': 0.5,
    'demand_period': 'am',
    'mode_type': 'info',
    'scenario_index_vector': 0,
    'activate': 0
}
