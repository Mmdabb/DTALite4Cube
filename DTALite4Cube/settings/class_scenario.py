class Scenario:
    def __init__(self, scenario_index=0, year=2025, scenario_name='', activate=1):
        self.scenario_index = scenario_index
        self.year = year
        self.scenario_name = scenario_name
        self.activate = activate

    def update_scenario(self, **kwargs):
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
