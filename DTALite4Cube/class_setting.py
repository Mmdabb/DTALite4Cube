import os
from class_link_type import LinkType, link_type_defaults
from class_basic import DtaBasics
from class_demand_file import DemandFile
from class_demand_subarea import DemandSubarea
from class_demand_period import DemandPeriod
from class_departure_profile import DepartureProfile, departure_profile_defaults
from class_dtm import DTMs, dtm_defaults
from class_scenario import Scenario
from class_sensor_data import Sensor
from class_mode import Mode
from mode_type_input import mode_config_data
import yaml
import logging

class Settings:
    def __init__(self, period=None, scenario_index=0):

        if not isinstance(scenario_index, int):
            scenario_index = 0
            logging.warning(f"Invalid value for 'scenario_index', using default value {scenario_index}")

        allowed_periods = {'am', 'md', 'pm', 'nt'}
        if period.lower() not in allowed_periods:
            error_msg = f"Invalid period title '{period}'. Valid options are {allowed_periods}."
            logging.error(error_msg)
            raise ValueError(error_msg)

        self.scenario_index = scenario_index
        self.period = period.lower()
        self.link_type_dict = {}
        self.basic_dict = {}
        self.demand_file_dict = {}
        self.demand_period_dict = {}
        self.demand_subarea_dict = {}
        self.departure_profile_dict = {}
        self.dtm_dict = {}
        self.scenario_dict = {}
        self.sensor_data_dict = {}
        self.mode_types_dict = {}

    def update_scenario(self, year=None, scenario_name=None):
        if not scenario_name:
            scenario_name = f'scenario_{self.period}'
        if not year:
            year = 2025
        scenarios = []
        scenario = Scenario(self.scenario_index, year, scenario_name)
        scenarios.append(vars(scenario))
        self.scenario_dict = {'scenarios': scenarios}

    def update_link_type(self, input_link_type_dataframe):
        input_link_type_dataframe.fillna('', inplace=True)
        link_types = []
        for index, row in input_link_type_dataframe.iterrows():
            link_type = LinkType(link_type_defaults)
            for link_type_attribute, link_type_attribute_value in vars(link_type).items():
                if link_type_attribute in row:
                    link_type_attribute_value = row[link_type_attribute]
                    setattr(link_type, link_type_attribute, link_type_attribute_value)
                else:
                    logging.warning(
                        f"For link type {row['link_type']} corresponding column {link_type_attribute} not found in link type data frame, using default value "
                        f"{link_type_attribute_value}")
                    continue

            link_types.append(vars(link_type))
        self.link_type_dict = {'link_types': link_types}

    def update_dta_basic(self, iteration, route, simu, UE_converge, length, speed):
        dta_basics = DtaBasics(iteration, route, simu, UE_converge, length, speed)
        self.basic_dict = vars(dta_basics)

    def update_demand_list(self, modes, period_time, demand_scale_factor=1):
        demand_files = []
        for index, mode_type in enumerate(modes):
            file_name = f"{mode_type}_{period_time}.csv"
            demand_period = self.period
            mode_type = mode_type
            file_sequence_no = index + 1
            demand_file = DemandFile(file_sequence_no, self.scenario_index, file_name, demand_period, mode_type,
                                     demand_scale_factor)
            demand_files.append(vars(demand_file))
        self.demand_file_dict = {'demand_files': demand_files}

    def update_demand_periods(self, period_time):
        demand_periods = []
        period_indices = {'am': 1, 'md': 2, 'pm': 3, 'nt': 4}
        period_index = period_indices[self.period]
        demand_period = DemandPeriod(self.period, period_index, period_time)
        demand_periods.append(vars(demand_period))
        self.demand_period_dict = {'demand_periods': demand_periods}

    def update_demand_subarea(self, input_demand_subarea=None):
        demand_subareas = []
        demand_subarea = DemandSubarea()
        if input_demand_subarea:
            demand_subarea.update_demand_subarea(**input_demand_subarea)
        demand_subareas.append(vars(demand_subarea))
        self.demand_subarea_dict = {'demand_files_for_subarea': demand_subareas}

    def update_departure_profile(self, input_departure_profile_dict=None):
        departure_profiles = []
        departure_profile = DepartureProfile(departure_profile_defaults)
        if input_departure_profile_dict:
            departure_profile.update_profile(**input_departure_profile_dict)
        departure_profiles.append(vars(departure_profile))
        self.departure_profile_dict = {'departure_time_profile': departure_profiles}

    def update_dtm(self, input_dtm_dict=None):
        dtms = []
        dtm = DTMs(dtm_defaults)
        if input_dtm_dict:
            dtm.update_dtm(**input_dtm_dict)
        dtms.append(vars(dtm))
        self.dtm_dict = {'dynamic_traffic_management_data': dtms}

    def update_sensor_data(self, input_sensor_data_dict=None):
        sensors_data = []
        sensor_data = Sensor()
        if input_sensor_data_dict:
            sensor_data.update_sensor(**input_sensor_data_dict)
        sensors_data.append(vars(sensor_data))
        self.sensor_data_dict = {'sensor_data': sensors_data}

    def update_mode(self, modes):
        sov_index = None
        sov_flag = None
        mode_types = []
        mode_config_dict = mode_config_data[self.period]

        if 'auto' in modes:
            sov_index = modes.index('auto')
            sov_flag = 'auto'
        elif 'sov' in modes:
            sov_index = modes.index('sov')
            sov_flag = 'sov'

        for index, mode_type in enumerate(modes):
            # It is recommended that the single occupancy vehicle has the index of 0
            if mode_type == sov_flag and index != 0:
                index = 0
            elif sov_flag and index == 0:
                index = sov_index

            if mode_type in mode_config_dict:
                mode_type_config_dict = mode_config_dict[mode_type]
                mode = Mode(mode_type, index)
                mode.update_mode(**mode_type_config_dict)
                mode_types.append(vars(mode))
            else:
                logging.warning(
                    f"Mode type '{mode_type}' not found in {mode_config_dict.keys()}.")
                continue
        self.mode_types_dict = {'mode_types': mode_types}

    def yaml_writer(self, period_time, output_path):
        # Merge all the classes to a single dataset
        data = {}
        data.update(self.basic_dict)
        data.update(self.mode_types_dict)
        data.update(self.scenario_dict)
        data.update(self.demand_period_dict)
        data.update(self.demand_file_dict)
        data.update(self.demand_subarea_dict)
        data.update(self.sensor_data_dict)
        data.update(self.dtm_dict)
        data.update(self.departure_profile_dict)
        data.update(self.link_type_dict)

        # with open(f'settings_{self.period}.yml', 'w') as file:
        #     yaml.dump(data, file, Dumper=yaml.SafeDumper, sort_keys=False)

        yaml_file_name = f'settings_{self.period}.yml'
        yaml_file_path = os.path.join(output_path, yaml_file_name)
        with open(yaml_file_path, 'w') as file:
            yaml.dump(data, file, Dumper=yaml.SafeDumper, sort_keys=False)

        # Post-process the YAML file to add single quotes to the specified time_period (if start with 0!??)
        with open(yaml_file_path, 'r') as file:
            lines = file.readlines()

        with open(yaml_file_path, 'w') as file:
            for line in lines:
                if period_time in line and period_time.startswith('0'):
                    line = line.replace(period_time, f"'{period_time}'")
                file.write(line)
