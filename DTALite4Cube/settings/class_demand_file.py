
class DemandFile:
    def __init__(self, file_sequence_no, file_name, mode_type,
                 scale_factor=1, format_type='column', departure_time_profile_no=1):

        self.file_sequence_no = file_sequence_no
        self.file_name = file_name
        self.mode_type = mode_type
        self.format_type = format_type
        self.scale_factor = scale_factor
        self.departure_time_profile_no = departure_time_profile_no


