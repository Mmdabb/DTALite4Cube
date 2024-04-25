class Sensor:
    def __init__(self, sensor_id=1, activate=0):
        self.sensor_id = sensor_id
        self.from_node_id = None
        self.to_node_id = None
        self.demand_period = None
        self.count = None
        self.scenario_index = None
        self.activate: activate

    def update_sensor(self, **kwargs):
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
