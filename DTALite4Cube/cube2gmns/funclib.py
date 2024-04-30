import pandas as pd
import geopandas as gpd
from shapely import wkt, geometry
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


def loadCSVfromSHP(shapefile_path):
    print('Loading shapefile with geometry ...')
    network_shapefile = gpd.read_file(shapefile_path)
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


def _loadLinks(network_gmns, network_shapefile):
    print('Loading links ...')
    # Define dtalite field mappings
    dtalite_field_mapping = Mapping(**dtalite_base_link_mapping)
    dtalite_dep_field_mapping = DependentMapping(**dtalite_additional_link_mapping)

    # Define required and optional fields
    cube_field_mapping = Mapping(**cube_base_link_mapping)
    cube_timedep_field_mapping = DependentMapping(**cube_link_dependent_mapping)
    _link_required_fields = set(vars(cube_field_mapping).values())
    for period in time_period_dict.values():
        for cls_key in vars(cube_timedep_field_mapping).keys():
            _link_required_fields.add(cube_timedep_field_mapping.get_field(cls_key, period))

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

        # Compute link length in meters and mile (DTALite use meters as default)
        cube_distance_field = cube_field_mapping.distance_field
        length_in_mile = network_shapefile[cube_distance_field][index]
        length = length_in_mile * 1609.34

        try:
            link.length = float(length)
        except ValueError:
            print(
                f'WARNING: Non-numeric value encountered in "Distance" field for link ID {link.org_link_id} '
                f'in network shape file. A zero value is assigned to "length" for GMNS link ID {link.link_id}.'
            )
            link.length = 0

        try:
            link.other_attrs['length_in_mile'] = float(length_in_mile)
        except ValueError:
            link.other_attrs['length_in_mile'] = 0

        # Extract lane information: number of lanes in AM is considered as default lane numbers
        # link_lane = network_shapefile['AMLANE'][index]
        cube_amlane_field = cube_timedep_field_mapping.get_field('lane_field', 'AM')
        try:
            link.lanes = int(network_shapefile[cube_amlane_field][index])
        except ValueError:
            link.lanes = 0
            print(
                f'WARNING: the number of lanes in the AM period in the network shape file is considered as '
                f'default lane numbers. \n But a non-integer value encountered in {cube_amlane_field} field for link ID '
                f'{link.org_link_id} in the network shapefile.  \n Hence, a zero value is assigned to "lanes" for '
                f'GMNS link ID {link.link_id}.'
            )

        # Extract link geometry
        cube_geometry_field = cube_field_mapping.geometry_field
        link.geometry = network_shapefile[cube_geometry_field][index]

        # Extract Facility and Area Types: AT and FT are will be used for link type calculation
        # The calculation is as follows: 10**4 * area type (AT) + 100 * facility type (FT) + allowed_uses
        # AM allowed uses will be considered as default value for link type
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

        cube_amlimit_field = cube_timedep_field_mapping.get_field('limit_field', 'AM')
        try:
            AMLIMIT = int(network_shapefile[cube_amlimit_field][index])
        except ValueError:
            print(
                f'WARNING: allowed uses in the AM period in the network shape file is considered as default '
                f'for link type calculation. \n But, a non-integer value encountered for {cube_amlimit_field} field for link ID '
                f'{link.org_link_id} in network shape file, hence 0 is assigned (link is open to all mode types). \n'
                f'This will impact link type and vdf code assignment for the GMNS link ID {link.link_id}'
            )
            AMLIMIT = 0

        if FT == 0:
            AMLIMIT = 0  # Connectors are always open to all mode types
        link_type = 10 ** 4 * int(AT) + 100 * int(FT) + int(AMLIMIT)
        link.link_type = link_type
        link.vdf_code = link_type

        # Extract link capacity information
        cube_capclass_field = cube_field_mapping.capacity_class
        try:
            cap_class = int(network_shapefile[cube_capclass_field][index])
        except ValueError:
            print(
                f'WARNING: a non-integer value encountered in {cube_capclass_field} field for link ID {link.org_link_id} '
                f'in network shape file.'
            )
            # cap_class = 13

        try:
            capacity = capacity_class_dict[cap_class]
            link.capacity = int(capacity)
        except KeyError:
            print(
                f'WARNING: the {cube_capclass_field} for link ID {link.org_link_id} in network shape file does not '
                f'exist in the defined capacity classes')
            # link.capacity = 2000

        # Extract link free speed information
        cube_spdclass_field = cube_field_mapping.speed_class
        try:
            spd_class = int(network_shapefile[cube_spdclass_field][index])
        except ValueError:
            print(
                f'WARNING: a non-integer value encountered in {cube_spdclass_field} field for link ID {link.org_link_id} '
                f'in network shape file.'
            )
            # spd_class = 11

        try:
            free_speed = speed_class_dict[spd_class]
            link.free_speed = int(free_speed)
        except KeyError:
            print(
                f'WARNING: the {cube_spdclass_field} for link ID {link.org_link_id} in network shape file does not '
                f'exist in the defined capacity classes')
            # link.free_speed = 63

        # Initialize link Volume Delay Function (VDF) parameters; AM period will be considered as default
        # vdf_fftt is not required anymore
        # try:
        #     vdf_fftt = 60 * link.other_attrs['length_in_mile'] / link.free_speed
        # except TypeError:
        #     vdf_fftt = 0
        # if vdf_fftt: link.other_attrs['VDF_fftt'] = float(vdf_fftt)

        # vdf_qdf is extracted from link_qvdf.csv
        # vdf_plf = 1 / (float(phf_dict['AM']))
        # link.other_attrs['VDF_plf'] = float(vdf_plf) if vdf_plf else 1

        # vdf_cap is not required anymore
        # vdf_cap = link.lanes * link.capacity / vdf_plf
        # link.other_attrs['VDF_cap'] = float(vdf_cap) if vdf_cap else 0

        vdf_alpha = float(alpha_dict[FT])
        dtalite_vdf_alpha_field = dtalite_dep_field_mapping.vdf_alpha
        link.other_attrs[dtalite_vdf_alpha_field] = float(vdf_alpha)

        vdf_beta = float(beta_dict[FT])
        dtalite_vdf_beta_field = dtalite_dep_field_mapping.vdf_beta
        link.other_attrs[dtalite_vdf_beta_field] = float(vdf_beta)

        # Process link data for different time period
        for t_seq, t_period in time_period_dict.items():

            cube_lane_field = cube_timedep_field_mapping.get_field('lane_field', t_period)
            try:
                lanes = int(network_shapefile[cube_lane_field][index])
            except ValueError:
                lanes = 0
                print(f'WARNING: a non-integer value encountered in {cube_lane_field} field for '
                      f'link ID {link.org_link_id} in the network shapefile')

            dtalite_period_lanes_field = dtalite_dep_field_mapping.get_field('period_lanes', t_seq)
            link.other_attrs[dtalite_period_lanes_field] = lanes

            dtalite_period_freespd_field = dtalite_dep_field_mapping.get_field('period_free_speed', t_seq)
            link.other_attrs[dtalite_period_freespd_field] = link.free_speed  # Same free speed for all time periods

            for agent_vdftoll in toll_allowed_uses_set:  # Set all toll prices for all mode types to 0
                link.other_attrs[str(agent_vdftoll) + str(t_seq)] = 0

            cube_toll_field = cube_timedep_field_mapping.get_field('toll_field', t_period)
            toll = network_shapefile[cube_toll_field][index] / 100  # cents -> dollars

            cube_limit_field = cube_timedep_field_mapping.get_field('limit_field', t_period)
            try:
                allowed_uses_key = int(network_shapefile[str(cube_limit_field)][index])
            except ValueError:
                allowed_uses_key = 0

            # allowed_uses = allowed_uses_dict[allowed_uses_key]

            if allowed_uses_key >= 0:
                # link.other_attrs[str('VDF_allowed_uses' + str(t_seq))] = allowed_uses
                if allowed_uses_key < 6:
                    for allowed_agent in toll_allowed_uses_dict[allowed_uses_key]:
                        link.other_attrs[str(allowed_agent) + str(t_seq)] = float(toll)

            if allowed_uses_key in (0, 6, 7, 8):
                t_link_type = 10 ** 4 * int(AT) + 100 * int(FT)
            else:
                t_link_type = 10 ** 4 * int(AT) + 100 * int(FT) + int(allowed_uses_key)

            dtalite_linktype_field = dtalite_dep_field_mapping.get_field('period_link_type', t_seq)
            link.other_attrs[dtalite_linktype_field] = t_link_type
            dtalite_vdfcode_field = dtalite_dep_field_mapping.get_field('period_vdf_code', t_seq)
            link.other_attrs[dtalite_vdfcode_field] = t_link_type

            # these field are not required anymore
            # t_vdf_fftt = 60 * link.other_attrs['length_in_mile'] / link.free_speed
            # if vdf_fftt: link.other_attrs['VDF_fftt' + str(t_seq)] = float(t_vdf_fftt)
            #
            # t_vdf_plf = 1 / (float(phf_dict[t_period]))
            # link.other_attrs['VDF_plf' + str(t_seq)] = float(t_vdf_plf) if t_vdf_plf else 1
            #
            # t_vdf_cap = lanes * link.capacity / vdf_plf
            # link.other_attrs['VDF_cap' + str(t_seq)] = float(t_vdf_cap) if t_vdf_cap else 0
            #
            # t_vdf_alpha = float(alpha_dict[FT])
            # if t_vdf_alpha: link.other_attrs['VDF_alpha' + str(t_seq)] = float(t_vdf_alpha)
            #
            # t_vdf_beta = float(beta_dict[FT])
            # if t_vdf_beta: link.other_attrs['VDF_beta' + str(t_seq)] = float(t_vdf_beta)

        for field in other_fields:
            link.other_attrs[field] = network_shapefile[field][index]

        # Needed for post-processing
        for t_seq, t_period in time_period_dict.items():
            field = cube_timedep_field_mapping.get_field('limit_field', t_period)
            link.other_attrs[field] = network_shapefile[field][index]

        link_dict[link.link_id] = link

    network_gmns.link_dict = link_dict
    network_gmns.link_other_attrs = other_fields

    print('%s links loaded' % len(link_dict))


def _buildnet(shapfile_path):
    raw_network = loadCSVfromSHP(shapfile_path)

    network = Network()
    _loadNodes(network, raw_network)
    _loadLinks(network, raw_network)

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


def _outputLink(network, output_folder):
    print('Generating link file ...')

    link_filename = 'link.csv'
    link_filepath = os.path.join(output_folder, 'link.csv')
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
    print('link.csv generated')


def district_id_map(net_dir):
    print('Assigning district ids ...')
    link_csv_path = os.path.join(net_dir, 'link.csv')
    node_csv_path = os.path.join(net_dir, 'node.csv')
    link_taz_jurname_csv_path = os.path.join(net_dir, 'TPBTAZ3722_TPBMod_JUR.csv')

    try:
        link_net = pd.read_csv(link_csv_path)
    except FileNotFoundError:
        print(f"link.csv not found in directory: {net_dir}")
        return None

    try:
        node_net = pd.read_csv(node_csv_path)
    except FileNotFoundError:
        print(f"node.csv not found in directory: {net_dir}")
        return None

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

    node_district_id_dict = dict(zip(link_net.from_node_id, link_net.district_id))
    # node_district_id_dict_2 = dict(zip(link_net.to_node_id, link_net.district_id))

    node_net['district_id'] = node_net.apply(lambda x: node_district_id_dict.setdefault(x.node_id, -1), axis=1)
    node_net.to_csv(os.path.join(net_dir, 'node.csv'), index=False)

    link_net.to_csv(os.path.join(net_dir, 'link.csv'), index=False)

    print('District ids assigned successfully.')


def cap_adjustment(net_dir):
    print('Adjusting link capacity ...')
    link_csv = os.path.join(net_dir, 'link.csv')
    if not os.path.exists(link_csv):
        print(f"File 'link.csv' not found in directory: {net_dir}")
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
        print("Columns 'ITS' and 'INTERSECTI' not found in 'link.csv'")
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
        df_bd_test.to_csv(os.path.join(net_dir, 'link.csv'), index=False)

    print('Link capacity  adjusted successfully.')


def get_gmns_from_cube(shapefile_path, district_id_assignment=True, capacity_adjustment=False):
    network = _buildnet(shapefile_path)
    _outputNode(network, shapefile_path)
    _outputLink(network, shapefile_path)

    if district_id_assignment:
        district_id_map(shapefile_path)

    if capacity_adjustment:
        cap_adjustment(shapefile_path)
