class Mode:
    def __init__(self, mode_type=None, mode_type_index=None):
        self.mode_type = mode_type
        self.mode_type_index = mode_type_index
        self.name = None
        self.vot = None
        self.meu = None
        self.person_occupancy = None
        self.headway_in_sec = 1.5
        self.DTM_real_time_info_type = 0
        self.activate = 1

    def update_mode(self, **kwargs):
        updated_attributes = set()
        for attribute, value in kwargs.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)
                updated_attributes.add(attribute)
            else:
                print(f"Ignoring unknown attribute: {attribute}")

        not_updated_attributes = set(vars(self).keys()) - updated_attributes
        for attribute in not_updated_attributes:
            if not {getattr(self, attribute)}:
                # add if attribue is None exit
                print(f"Warning: {attribute} has not been updated and is set to: {getattr(self, attribute)}")
