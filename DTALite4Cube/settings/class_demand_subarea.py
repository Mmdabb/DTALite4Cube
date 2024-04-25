class DemandSubarea:
    def __init__(self, activate=0, subarea_geometry='POLYGON ((-180 -90, 180 -90, 180 90, -180 90, -180 -90))',
                 file_name='demand.csv', format_type='column'):
        self.activate = activate
        self.subarea_geometry = subarea_geometry
        self.file_name = file_name
        self.format_type = format_type

    def update_demand_subarea(self, **kwargs):
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

