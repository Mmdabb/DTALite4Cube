import pandas as pd
import geopandas as gpd
from shapely import wkt, geometry
import numpy as np
import time
import csv
import sys
import os
from .mapclass import Mapping, DependentMapping
from .netclass import Node, Link, Network
from .fieldnameconfig import time_period_dict
from .fieldnameconfig import cube_node_mapping, cube_base_link_mapping, cube_link_dependent_mapping
from .fieldnameconfig import dtalite_node_mapping, dtalite_base_link_mapping, dtalite_additional_link_mapping
from .netconfig import alpha_dict, beta_dict, allowed_uses_dict, speed_class_dict, capacity_class_dict
from .NVTA_qvdf_calibration_results_dict import NVTA_qvdf_dict
from datetime import datetime, timedelta


def convert_to_datetime(time_str):
    return datetime.strptime(time_str, '%H%M')


def time_period_duration(time_period_list, period_range_list):
    time_period_duration_dict = {}
    for period_title, time_range in zip(time_period_list, period_range_list):
        start_time_str, end_time_str = time_range.split('_')
        start_time = convert_to_datetime(start_time_str)
        end_time = convert_to_datetime(end_time_str)
        time_duration = end_time - start_time
        if time_duration.days < 0:
            time_duration = time_duration + timedelta(days=1)
        time_period_duration_dict[period_title] = time_duration.total_seconds() / 3600
    return time_period_duration_dict


def linkqvdf_reader(time_period_list, time_period_dict, shapfile_path):
    link_qvdf_file = False
    vdf_dict = {}
    net_dir = os.path.join(shapfile_path, 'link_qvdf.csv')
    if os.path.exists(net_dir):
        print(
            'A link_qvdf.csv file has been found in this directory and will be used to assign values to QVDF parameters. '
            'If you prefer not to use it, please remove the file and re-run the program.')

        qvdf_fields = ['QVDF_plf', 'QVDF_n', 'QVDF_s', 'QVDF_cp', 'QVDF_cd', 'QVDF_alpha', 'QVDF_beta']
        qvdf_required_fields = set()  # Initialize as a set

        for time_period in time_period_list:
            for qvdf_field in qvdf_fields:
                time_sequence = time_period_dict.get(time_period.upper())  # Use get to safely retrieve value
                if time_sequence:
                    qvdf_required_fields.add(str(qvdf_field) + str(time_sequence))

        vdf_data = pd.read_csv('link_qvdf.csv')
        qvdf_fieldnames_set = set(vdf_data.columns)

        if 'vdf_code' in qvdf_fieldnames_set:
            link_qvdf_file = True
            if 'all' in vdf_data['vdf_code'].values:
                vdf_dict = vdf_data.iloc[:-1].set_index('vdf_code').to_dict(orient='index')
                vdf_dict['all'] = vdf_data.iloc[-1].to_dict()
            else:
                vdf_dict = vdf_data.set_index('vdf_code').to_dict(orient='index')

            # Check if all required fields exist
            for qvdf_field in qvdf_required_fields:
                if qvdf_field not in qvdf_fieldnames_set:
                    print(f'Warning: QVDF required field ({qvdf_field}) does not exist in the network file')
                    # these should be added using the dictionary NVTA

        else:
            vdf_dict = NVTA_qvdf_dict
            print('"vdf_code" field does not exist in "link_qvdf.csv".')

    else:
        vdf_dict = NVTA_qvdf_dict

    return vdf_dict


def loadCSVfromSHP(shapefile_path):
    print(f'Loading shapefile - {shapefile_path}  with geometry ...')
    network_shapefile = gpd.read_file(shapefile_path)
    network_shapefile['ID'] = range(1, len(network_shapefile) + 1)
    # network_shapefile.plot()
    print('Shapefile loaded successfully.')
    return network_shapefile


def linestring_to_points(feature, line):
    return {feature: line.coords}


def poly_to_points(feature, poly):
    return {feature: poly.exterior.coords}


def _loadNodes(network_gmns, network_shapefile):
    print('Loading nodes ...')
    print('Node IDs below 10,000 will be treated as zone IDs.')

    field_mapping = Mapping(**cube_node_mapping)
    _node_required_fields = set(vars(field_mapping).values())
    _node_optional_fields = {}

    fieldnames = list(network_shapefile)
    if '' in fieldnames:
        print('WARNING: columns with an empty header are detected in the network file. these columns will be skipped')
        fieldnames = [fieldname for fieldname in fieldnames if fieldname]

    fieldnames_set = set(fieldnames)
    for field in _node_required_fields:
        if field not in fieldnames_set:
            sys.exit(f'ERROR: required field ({field}) for generating node file does not exist in the network file')

    other_fields = list(fieldnames_set.difference(_node_required_fields.union(_node_optional_fields)))

    node_id_list = []
    node_coord_list = []
    node_dict = {}

    for index in network_shapefile.index:
        # for one-way route-able road only
        for i in range(2):
            if not i:
                node = Node(int(network_shapefile[field_mapping.from_node_field][index]))
            else:
                node = Node(int(network_shapefile[field_mapping.to_node_field][index]))

            if node.node_id in node_id_list:
                continue

            node_coords = network_shapefile[field_mapping.geometry_field][index].coords
            node.geometry = geometry.Point(node_coords[i])
            node.x_coord, node.y_coord = float(node_coords[i][0]), float(node_coords[i][-1])

            if node.node_id < 10000:
                node.zone_id = node.node_id

            # others
            for field in other_fields:
                node.other_attrs[field] = network_shapefile[field][index]

            node_dict[node.node_id] = node
            node_id_list.append(node.node_id)

    network_gmns.node_dict = node_dict
    network_gmns.node_other_attrs = other_fields

    print('%s nodes loaded successfully.' % len(node_id_list))


def _loadLinks(network_gmns, network_shapefile, time_period, time_period_list, vdf_dict, length_unit='mile', dtalite_version_code='old'):
    print('Loading links ...')
    print(f'Time period: {time_period}')
    # Define dtalite field mappings
    dtalite_field_mapping = Mapping(**dtalite_base_link_mapping)
    dtalite_dep_field_mapping = DependentMapping(**dtalite_additional_link_mapping)

    # Define required and optional fields
    cube_field_mapping = Mapping(**cube_base_link_mapping)
    cube_timedep_field_mapping = DependentMapping(**cube_link_dependent_mapping)
    _link_required_fields = set(vars(cube_field_mapping).values())

    # for t_period in time_period_list:
    for class_key in vars(cube_timedep_field_mapping).keys():
        _link_required_fields.add(cube_timedep_field_mapping.get_field(class_key, time_period.upper()))

    _link_optional_fields = {}

    # Check for empty headers in field names
    fieldnames = list(network_shapefile)
    if '' in fieldnames:
        print('WARNING: columns with an empty header are detected in the network file. these columns will be skipped')
        fieldnames = [fieldname for fieldname in fieldnames if fieldname]

    fieldnames_set = set(fieldnames)

    # Check if all required fields exist
    for field in _link_required_fields:
        if field not in fieldnames_set:
            sys.exit(f'ERROR: required field ({field}) for generating link file does not exist in the network file')

    # Extract other fields
    other_fields = list(fieldnames_set.difference(_link_required_fields.union(_link_optional_fields)))

    # Initialize dictionaries and variables
    node_dict = network_gmns.node_dict
    link_dict = {}

    # A dictionary for allowed agents for toll pricing calculations
    toll_allowed_uses_dict = {}
    toll_allowed_uses_set = set()
    for usedict_key, usedict_value in allowed_uses_dict.items():
        if usedict_key < 6:  # Take only the first 5 items
            uses = usedict_value.split(';')
            toll_allowed_uses_list = []
            for use in uses:
                dtalite_vdftoll_field = dtalite_dep_field_mapping.get_field('vdf_toll', use)
                toll_allowed_uses_set.add(dtalite_vdftoll_field)
                toll_allowed_uses_list.append(dtalite_vdftoll_field)
            toll_allowed_uses_dict[usedict_key] = toll_allowed_uses_list

    # time_duration_dict = time_period_duration(time_period_list, time_period_duration_list)
    time_sequence = time_period_dict[time_period.upper()]
    # time_duration = time_duration_dict[time_sequence]

    # Process each link in the shapefile
    for index in network_shapefile.index:

        link = Link(int(index + 1))
        cube_link_id_field = cube_field_mapping.link_id_field
        link.org_link_id = int(network_shapefile[cube_link_id_field][index])

        # Extract from_node and to_node IDs
        from_node_field = cube_field_mapping.from_node_field
        to_node_field = cube_field_mapping.to_node_field
        from_node_id = int(network_shapefile[from_node_field][index])
        to_node_id = int(network_shapefile[to_node_field][index])
        # from_node_id, to_node_id = int(network_shapefile[cube_field_mapping.from_node_field][index]),
        # int(network_shapefile[cube_field_mapping.to_node_field][index])

        if from_node_id == to_node_id:
            print(f'WARNING: from_node and to_node of link {link.link_id} are the same')
            continue

        try:
            link.from_node = node_dict[from_node_id]
        except KeyError:
            print(f'WARNING: from_node {from_node_id} of link {link.link_id} does not exist in the node file')
            continue
        try:
            link.to_node = node_dict[to_node_id]
        except KeyError:
            print(f'WARNING: to_node {to_node_id} of link {link.link_id} does not exist in the node file')
            continue

        # Compute link length in meters and mile
        cube_distance_field = cube_field_mapping.distance_field
        length_in_mile = network_shapefile[cube_distance_field][index]

        if length_unit == 'meter':
            length = length_in_mile * 1609.34
        elif length_unit == 'mile':
            length = length_in_mile
        else:
            sys.exit(f'ERROR: Invalid length unit ({length_unit}). It must be either "meter" or "mile".')

        try:
            link.length = float(length)
        except ValueError:
            print(f'WARNING: Non-numeric value encountered in "Distance" field for link ID {link.org_link_id}. '
                  f'Assigning zero to "length" for GMNS link ID {link.link_id}.')
            link.length = 0  # or some small values?

        try:
            link.other_attrs['length_in_mile'] = float(length_in_mile)
        except ValueError:
            link.other_attrs['length_in_mile'] = 0

        cube_lane_field = cube_timedep_field_mapping.get_field('lane_field', time_period.upper())
        try:
            lanes = int(network_shapefile[cube_lane_field][index])
        except ValueError:
            print(f'WARNING: a non-integer value encountered in {cube_lane_field} field for '
                  f'link ID {link.org_link_id} in the network shapefile.'
                  f'This link will be removed from the link file.')
            continue

        if lanes <= 0:
            print(f'WARNING: Link ID {link.org_link_id} has {lanes} lanes. Skipping this link.')
            continue  # Skip the current link if it has 0 or fewer lanes

        link.lanes = lanes
        dtalite_period_lanes_field = dtalite_dep_field_mapping.get_field('period_lanes', time_sequence)
        link.other_attrs[dtalite_period_lanes_field] = lanes

        # Extract link geometry
        cube_geometry_field = cube_field_mapping.geometry_field
        link.geometry = network_shapefile[cube_geometry_field][index]

        # Extract Facility and Area Types: AT and FT are will be used for link type calculation
        # The calculation is as follows: 10**2 * area type (AT) + facility type (FT)
        cube_at_field = cube_field_mapping.area_type_field
        try:
            AT = int(network_shapefile[cube_at_field][index])
        except ValueError:
            print(
                f'WARNING: a non-integer value encountered in {cube_at_field} field for link ID {link.org_link_id} '
                f'in network shape file, hence 0 is assigned to "AT" for GMNS link ID {link.link_id}. \n'
                f'This will impact link type and vdf code assignment for the specified GMNS link'
            )
            AT = 0

        cube_ft_field = cube_field_mapping.facility_type_field
        try:
            FT = int(network_shapefile[cube_ft_field][index])
        except ValueError:
            print(
                f'WARNING: a non-integer value encountered in {cube_ft_field} field for link ID {link.org_link_id} '
                f'in network shape file, hence 0 is assigned to "FT" for GMNS link ID {link.link_id} '
                f'(The link will be treated as a connector).  \n'
                f'This will impact link type and vdf code assignment for the specified GMNS link'
            )
            FT = 0

        link_type = 10 ** 2 * int(AT) + int(FT)
        link.link_type = link_type
        link.vdf_code = link_type

        # Extract link capacity information
        cube_capclass_field = cube_field_mapping.capacity_class
        try:
            cap_class = int(network_shapefile[cube_capclass_field][index])
        except ValueError:  # KeyError should be added with sys.exist
            print(
                f'WARNING: a non-integer value encountered in {cube_capclass_field} field for link ID {link.org_link_id} '
                f'in network shape file. Skipping this link.'
            )
            continue
            # cap_class = 13

        try:
            capacity = capacity_class_dict[cap_class]
            link.capacity = int(capacity)
        except KeyError:
            print(
                f'WARNING: the {cube_capclass_field} for link ID {link.org_link_id} in network shape file does not '
                f'exist in the defined capacity classes. Skipping this link.')
            continue
            # link.capacity = 2000

        # Extract link free speed information
        cube_spdclass_field = cube_field_mapping.speed_class
        try:
            spd_class = int(network_shapefile[cube_spdclass_field][index])
        except ValueError:  # KeyError should be added with sys.exist
            print(
                f'WARNING: a non-integer value encountered in {cube_spdclass_field} field for link ID {link.org_link_id} '
                f'in network shape file. Skipping this link.'
            )
            continue

        try:
            free_speed = speed_class_dict[spd_class]
        except KeyError:
            print(
                f'WARNING: the {cube_spdclass_field} for link ID {link.org_link_id} in network shape file does not '
                f'exist in the defined capacity classes. Skipping this link.')
            continue

        if length_unit == 'meter':
            link.free_speed = int(free_speed) * 1.60934
        elif length_unit == 'mile':
            link.free_speed = int(free_speed)
        else:
            sys.exit(f'ERROR: Invalid length unit ({length_unit}). It must be either "meter" or "mile".')

        dtalite_period_freespd_field = dtalite_dep_field_mapping.get_field('period_free_speed', time_sequence)
        link.other_attrs[dtalite_period_freespd_field] = link.free_speed

        if dtalite_version_code=='old':
            vdf_fields = ['alpha', 'beta', 'plf']
            vdf_key_prefix = 'VDF'
        else:
            vdf_fields = ['alpha', 'beta', 'qdf', 'plf', 'cp', 'cd', 'n', 's']
            if 'all' not in vdf_dict.keys():
                vdf_dict['all'] = NVTA_qvdf_dict['all']
            vdf_key_prefix = 'QVDF'

        link_type_vdf_key = str(link_type) if link_type else np.nan
        for vdf_field in vdf_fields:
            vdf_key = f'{vdf_key_prefix}_{vdf_field}{time_sequence}'
            try:
                vdf_value = vdf_dict[link_type_vdf_key][vdf_key]
            except KeyError:
                vdf_value = np.nan

            if vdf_field == 'plf':
                vdf_plf = vdf_value

            if dtalite_version_code=='old':
                dtalite_vdf_field = vdf_key
            else:
                dtalite_vdf_field = dtalite_dep_field_mapping.get_field('vdf_parameter', vdf_field)

            link.other_attrs[dtalite_vdf_field] = float(vdf_value) if vdf_value else vdf_value


        #   Extracting Allowed uses
        cube_limit_field = cube_timedep_field_mapping.get_field('limit_field', time_period.upper())
        # Needed for post-processing
        link.other_attrs[cube_limit_field] = network_shapefile[cube_limit_field][index]
        try:
            allowed_uses_key = network_shapefile[str(cube_limit_field)][index]
            allowed_uses_key = int(allowed_uses_key)
        except KeyError:
            sys.exit(f'ERROR: The field "{cube_limit_field}" was not found in network_shapefile.')
        except ValueError:
            print(
                f'WARNING: A non-integer value encountered in {cube_limit_field} field for link ID {link.org_link_id} '
                f'in network shape file. Assigning zero.'
            )
            allowed_uses_key = 0

        #   Creating allowed uses for DTALIte and assign toll values
        allowed_uses = allowed_uses_dict[allowed_uses_key]
        cube_toll_field = cube_timedep_field_mapping.get_field('toll_field', time_period.upper())
        try:
            toll = network_shapefile[cube_toll_field][index] / 100  # cents -> dollars
        except KeyError:
            print(f'Warning: The field "{cube_toll_field}" was not found in network_shapefile.')
            toll = 0

        for agent in toll_allowed_uses_set:  # Set all toll prices for all mode types to 0
            if dtalite_version_code == 'old':
                link.other_attrs[f'{agent}{time_sequence}'] = 0
            else:
                link.other_attrs[str(agent)] = 0

        if allowed_uses_key >= 0:
            if dtalite_version_code == 'old':
                link.other_attrs[f'VDF_allowed_uses{time_sequence}'] = allowed_uses
            else:
                link.other_attrs[str('allowed_uses')] = allowed_uses
            if allowed_uses_key < 6:
                for allowed_agent in toll_allowed_uses_dict[allowed_uses_key]:
                    if dtalite_version_code == 'old':
                        link.other_attrs[f'{allowed_agent}{time_sequence}'] = float(toll)
                    else:
                        link.other_attrs[str(allowed_agent)] = float(toll)

        if dtalite_version_code == 'old':
            if free_speed > 0:
                vdf_fftt = 60 * length_in_mile / free_speed

            if vdf_fftt: link.other_attrs['VDF_fftt' + str(time_sequence)] = float(vdf_fftt)

            vdf_cap = lanes * link.capacity / (vdf_plf if vdf_plf else 1)
            link.other_attrs['VDF_cap' + str(time_sequence)] = float(vdf_cap) if vdf_cap else 0

        for field in other_fields:
            link.other_attrs[field] = network_shapefile[field][index]

        link_dict[link.link_id] = link

    network_gmns.link_dict = link_dict
    network_gmns.link_other_attrs = other_fields

    print('%s links loaded' % len(link_dict))


def _buildnet(shapfile_path, time_period, time_period_list, length_unit, node_generation):
    network = Network()
    if node_generation:
        raw_network = loadCSVfromSHP(shapfile_path)
        _loadNodes(network, raw_network)
    # vdf_dict = linkqvdf_reader(time_period_list, time_period_dict, shapfile_path)
    vdf_dict = NVTA_qvdf_dict
    _loadLinks(network, raw_network, time_period, time_period_list, vdf_dict, length_unit)

    return network


def _outputNode(network, output_folder):
    print('Generating node file ...')

    node_filename = 'node.csv'
    node_filepath = os.path.join(output_folder, node_filename)

    outfile = open(node_filepath, 'w', newline='', errors='ignore')

    writer = csv.writer(outfile)

    node_header = list(dtalite_node_mapping.values())
    writer.writerow(node_header)
    for node_id, node in network.node_dict.items():
        line = [node.node_id, node.x_coord, node.y_coord, node.centroid, node.zone_id, node.geometry]

        writer.writerow(line)
    outfile.close()
    print('node.csv generated')


def _outputLink(network, output_folder, time_period):
    print('Generating link file ...')

    link_filename = f'link_{time_period}.csv'
    link_filepath = os.path.join(output_folder, link_filename)
    outfile = open(link_filepath, 'w', newline='', errors='ignore')

    writer = csv.writer(outfile)
    link_header = list(dtalite_base_link_mapping.values())
    # link_header = ['link_id', 'from_node_id', 'to_node_id', 'lanes', 'length', 'dir_flag', 'geometry',
    #                'free_speed', 'capacity', 'link_type', 'vdf_code']
    other_link_header = list(network.link_dict[1].other_attrs.keys())
    link_header.extend(other_link_header)
    writer.writerow(link_header)

    for link_id, link in network.link_dict.items():
        line = [link.link_id, link.from_node.node_id, link.to_node.node_id, link.lanes, link.length,
                link.dir_flag, link.geometry, link.free_speed, link.capacity, link.link_type, link.vdf_code]

        other_link_att_values = list(link.other_attrs.values())
        line.extend(other_link_att_values)
        writer.writerow(line)
    outfile.close()
    print(f'link_{time_period}.csv generated')


def district_id_map(net_dir, time_period):
    print('Assigning district ids ...')

    link_csv_path = os.path.join(net_dir, f'link_{time_period}.csv')
    try:
        link_net = pd.read_csv(link_csv_path)
    except FileNotFoundError:
        print(f"link_{time_period}.csv not found in directory: {net_dir}")
        return None

    node_generation = True
    node_csv_path = os.path.join(net_dir, 'node.csv')
    try:
        node_net = pd.read_csv(node_csv_path)
    except FileNotFoundError:
        print(f"node.csv not found in directory: {net_dir}")
        return None
    if 'district_id' in node_net.columns:
        node_generation = False

    link_taz_jurname_csv_path = os.path.join(net_dir, 'TPBTAZ3722_TPBMod_JUR.csv')
    try:
        link_taz_jurname = pd.read_csv(link_taz_jurname_csv_path)
    except FileNotFoundError:
        print(f"TPBTAZ3722_TPBMod_JUR.csv not found in directory: {net_dir}")
        return None

    link_net['pair'] = link_net['from_node_id'].astype(str) + '->' + link_net['to_node_id'].astype(str)

    link_taz_jurname_dict = dict(zip(link_taz_jurname.TAZ, link_taz_jurname.NAME))

    district_id_dict = {'Arlington': 2,
                        'Alexandria': 1,
                        'Fairfax': 3,
                        'Fairfax City': 4,
                        'Falls Church': 5,
                        'Loudoun': 6,
                        'Prince William': 9,
                        'Manassas': 7,
                        'Manassas Park': 8
                        }

    link_net['JUR_NAME'] = link_net.apply(lambda x: link_taz_jurname_dict.setdefault(x.TAZ, -1), axis=1)
    link_net['district_id'] = link_net.apply(lambda x: district_id_dict.setdefault(x.JUR_NAME, 10), axis=1)

    if node_generation:
        node_district_id_dict = dict(zip(link_net.from_node_id, link_net.district_id))
        # node_district_id_dict_2 = dict(zip(link_net.to_node_id, link_net.district_id))
        node_net['district_id'] = node_net.apply(lambda x: node_district_id_dict.setdefault(x.node_id, -1), axis=1)
        node_net.to_csv(os.path.join(net_dir, 'node.csv'), index=False)

    link_net.to_csv(os.path.join(net_dir, f'link_{time_period}.csv'), index=False)

    print('District ids assigned successfully.')


def cap_adjustment(net_dir, time_period):
    print('Adjusting link capacity ...')
    link_csv = os.path.join(net_dir, f'link_{time_period}.csv')
    if not os.path.exists(link_csv):
        print(f"File 'link_{time_period}.csv' not found in directory: {net_dir}")
        return None

    df_link = pd.read_csv(link_csv)

    has_its = 'ITS' in df_link.columns
    has_intersecti = 'INTERSECTI' in df_link.columns

    data_seg_list = []

    # Check available columns and adjust dictionaries and filters accordingly
    if has_its and has_intersecti:
        cap_adj_dict = {
            1: [0, 0],
            1.05: [0, 1],
            1.01: [1, 0],
            1.06: [1, 1]
        }
    elif has_its:
        cap_adj_dict = {
            1: [0],
            1.01: [1]
        }
    elif has_intersecti:
        cap_adj_dict = {
            1: [0],
            1.05: [1]
        }
    else:
        print(f"Columns 'ITS' and 'INTERSECTI' not found in 'link_{time_period}.csv'")
        return

    for adj_factor, cap_key in cap_adj_dict.items():
        ITS_code = cap_key[0] if has_its else None
        intersection_code = cap_key[-1] if has_intersecti else None

        # Filter the links based on available columns
        if ITS_code is not None and intersection_code is not None:
            link_adj_cap_net = df_link[
                (df_link.get('ITS') == ITS_code) & (df_link.get('INTERSECTI') == intersection_code)].copy()
        elif ITS_code is not None and intersection_code is None:
            link_adj_cap_net = df_link[(df_link.get('ITS') == ITS_code)].copy()
        elif intersection_code is not None and ITS_code is None:
            link_adj_cap_net = df_link[(df_link.get('INTERSECTI') == intersection_code)].copy()
        else:
            continue

        if not link_adj_cap_net.empty:
            link_adj_cap_net['capacity'] *= adj_factor
            data_seg_list.append(link_adj_cap_net)

    if data_seg_list:
        df_bd_test = pd.concat(data_seg_list)
        df_bd_test = df_bd_test.sort_values(by="link_id")
        df_bd_test.to_csv(os.path.join(net_dir, f'link_{time_period}.csv'), index=False)

    print('Link capacity  adjusted successfully.')


def get_gmns_from_cube(shapefile_path, time_period_list, length_unit='mile',
                       district_id_assignment=True, capacity_adjustment=False, dtalite_version_code='old'):
    node_generation = True
    for time_period in time_period_list:
        if node_generation:
            raw_network = loadCSVfromSHP(shapefile_path)
            network = Network()
            _loadNodes(network, raw_network)
            _outputNode(network, shapefile_path)
            node_generation = False

        if dtalite_version_code == 'old':
            link_bpr_dir = os.path.join(shapefile_path, 'link_bpr.csv')
            if not os.path.exists(link_bpr_dir):
                sys.exit(f'ERROR: "link_bpr.csv" not found. Please provide the file in the following location: \n'
                         f'({os.path.abspath(shapefile_path)})')

            vdf_bpr_dict = pd.read_csv(link_bpr_dir)
            vdf_dict = vdf_bpr_dict.set_index('VDF_code').T.to_dict()
        else:
            vdf_dict = NVTA_qvdf_dict

        _loadLinks(network, raw_network, time_period, time_period_list, vdf_dict, length_unit, dtalite_version_code)
        _outputLink(network, shapefile_path, time_period.lower())

        if district_id_assignment:
            district_id_map(shapefile_path, time_period.lower())

        if capacity_adjustment:
            cap_adjustment(shapefile_path, time_period.lower())
