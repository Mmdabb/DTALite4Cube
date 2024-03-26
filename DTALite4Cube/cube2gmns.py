# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
import geopandas as gpd
from shapely import wkt, geometry
import numpy as np
import time
import csv
import sys
import os


class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.x_coord = None
        self.y_coord = None
        self.centroid = None
        self.zone_id = None
        self.geometry = None

        self.other_attrs = {}


class Link:
    def __init__(self, link_id):
        self.org_link_id = None
        self.link_id = link_id
        self.from_node = None
        self.to_node = None
        self.lanes = None
        self.length = 0
        self.dir_flag = 1
        self.geometry = None

        self.free_speed = None
        self.capacity = None
        self.link_type = 0
        self.vdf_code = 0

        self.other_attrs = {}


class Network:
    def __init__(self):
        self.node_dict = {}
        self.link_dict = {}

        self.max_node_id = 0
        self.max_link_id = 0

        self.original_coordinate_type = 'lonlat'

        self.node_other_attrs = []
        self.link_other_attrs = []

    @property
    def number_of_nodes(self):
        return len(self.node_dict)

    @property
    def number_of_links(self):
        return len(self.link_dict)


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
    _node_required_fields = {'A', 'B', 'geometry'}
    _node_optional_fields = {'zone_id'}

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
    from_to_node_field = ['A', 'B']
    for index in network_shapefile.index:

        for i in range(2):
            node = Node(int(network_shapefile[from_to_node_field[i]][index]))

            if node.node_id in node_id_list:
                continue

            node_coords = network_shapefile["geometry"][index].coords
            node.geometry = geometry.Point(node_coords[i])
            node.x_coord, node.y_coord = float(node_coords[i][0]), float(node_coords[i][1])

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

    # Define required and optional fields
    _link_required_fields = {'ID', 'A', 'B', 'DISTANCE', 'AMLANE', 'MDLANE', 'PMLANE', 'NTLANE', 'geometry',
                             'ATYPE', 'FTYPE', 'AMLIMIT', 'MDLIMIT', 'PMLIMIT', 'NTLIMIT'}
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
    time_period_dict = {1: 'AM', 2: 'MD', 3: 'PM', 4: 'NT'}

    # Define constants
    alpha_dict = {0: 0.1, 1: 0.87, 2: 0.96, 3: 0.96, 4: 0.96, 5: 0.87, 6: 0.96}  # classified by facility type
    beta_dict = {0: 2, 1: 5, 2: 2.3, 3: 2.3, 4: 2.3, 5: 5, 6: 2.3}  # classified by facility type

    allowed_uses_dict = {0: 'sov;hov2;hov3;trk;apv;com', 1: 'sov;hov2;hov3;trk;apv;com', 2: 'hov2;hov3', 3: 'hov3',
                         4: 'sov;hov2;hov3;com;apv', 5: 'apv', 6: '', 7: '', 8: '', 9: 'closed'}

    # A dictionary for allowed agents for toll pricing calculations
    toll_allowed_uses_dict = {}
    for usedict_key, usedict_value in allowed_uses_dict.items():
        if usedict_key < 6:
            uses = usedict_value.split(';')  # Take only the first 5 items
            toll_allowed_uses_dict[usedict_key] = ['VDF_toll' + use for use in uses]

    speed_class_dict = {0: 17, 1: 17, 2: 17, 3: 23, 4: 29, 5: 35, 6: 40, 11: 63, 12: 63, 13: 69, 14: 69, 15: 75,
                        16: 75, 21: 40, 22: 40, 23: 52, 24: 52, 25: 58, 26: 58, 31: 40, 32: 40, 33: 46, 34: 46,
                        35: 46, 36: 52, 41: 35, 42: 35, 43: 35, 44: 40, 45: 40, 46: 40, 51: 52, 52: 52, 53: 58,
                        54: 58, 55: 58, 56: 63, 61: 23, 62: 23, 63: 35, 64: 35, 65: 40, 66: 58}

    capacity_class_dict = {0: 3150, 1: 3150, 2: 3150, 3: 3150, 4: 3150, 5: 3150, 6: 3150, 11: 1900, 12: 1900,
                           13: 2000, 14: 2000, 15: 2000, 16: 2000, 21: 600, 22: 800, 23: 960, 24: 960,
                           25: 1100, 26: 1100, 31: 500, 32: 600, 33: 700, 34: 840, 35: 900, 36: 900, 41: 500,
                           42: 500, 43: 600, 44: 800, 45: 800, 46: 800, 51: 1100, 52: 1200, 53: 1200, 54: 1400,
                           55: 1600, 56: 1600, 61: 1000, 62: 1000, 63: 1000, 64: 1000, 65: 2000, 66: 2000}

    phf_dict = {'AM': 2.39776486, 'MD': 5.649424854, 'PM': 3.401127052, 'NT': 6.66626961}

    # Process each link in the shapefile
    for index in network_shapefile.index:

        link = Link(int(index + 1))
        link.org_link_id = int(network_shapefile['ID'][index])

        # Extract from_node and to_node IDs
        from_node_id, to_node_id = int(network_shapefile['A'][index]), int(network_shapefile['B'][index])
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
        length_in_mile = network_shapefile['DISTANCE'][index]
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
        try:
            link.lanes = int(network_shapefile['AMLANE'][index])
        except ValueError:
            link.lanes = 0
            print(
                f'WARNING: the number of lanes in the AM period in the network shape file is considered as '
                f'default lane numbers. \n But a non-integer value encountered in "AMLANE" field for link ID '
                f'{link.org_link_id} in the network shapefile.  \n Hence, a zero value is assigned to "lanes" for '
                f'GMNS link ID {link.link_id}.'
            )

        # Extract link geometry
        link.geometry = network_shapefile['geometry'][index]

        # Extract Facility and Area Types: AT and FT are will be used for link type calculation
        # The calculation is as follows: 10**4 * area type (AT) + 100 * facility type (FT) + allowed_uses
        # AM allowed uses will be considered as default value for link type

        try:
            AT = int(network_shapefile['ATYPE'][index])
        except ValueError:
            print(
                f'WARNING: a non-integer value encountered in "ATYPE" field for link ID {link.org_link_id} '
                f'in network shape file, hence 0 is assigned to "AT" for GMNS link ID {link.link_id}. \n'
                f'This will impact link type and vdf code assignment for the specified GMNS link'
            )
            AT = 0

        try:
            FT = int(network_shapefile['FTYPE'][index])
        except ValueError:
            print(
                f'WARNING: a non-integer value encountered in "FTYPE" field for link ID {link.org_link_id} '
                f'in network shape file, hence 0 is assigned to "FT" for GMNS link ID {link.link_id} '
                f'(The link will be treated as a connector).  \n'
                f'This will impact link type and vdf code assignment for the specified GMNS link'
            )
            FT = 0

        try:
            AMLIMIT = int(network_shapefile['AMLIMIT'][index])
        except ValueError:
            print(
                f'WARNING: allowed uses in the AM period in the network shape file is considered as default '
                f'for link type calculation. \n But, a non-integer value encountered for "AMLIMIT" field for link ID '
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
        try:
            cap_class = int(network_shapefile['CAPCLASS'][index])
        except ValueError:
            print(
                f'WARNING: a non-integer value encountered in "CAPCLASS" field for link ID {link.org_link_id} '
                f'in network shape file.'
            )
            # cap_class = 13

        try:
            capacity = capacity_class_dict[cap_class]
            link.capacity = int(capacity)
        except KeyError:
            print(
                f'WARNING: the CAPCLASS for link ID {link.org_link_id} in network shape file does not exist '
                f'in the defined capacity classes')
            # link.capacity = 2000

        # Extract link free speed information
        try:
            spd_class = int(network_shapefile['SPDCLASS'][index])
        except ValueError:
            print(
                f'WARNING: a non-integer value encountered in "SPDCLASS" field for link ID {link.org_link_id} '
                f'in network shape file.'
            )
            # spd_class = 11

        try:
            free_speed = speed_class_dict[spd_class]
            link.free_speed = int(free_speed)
        except KeyError:
            print(
                f'WARNING: the SPDCLASS for link ID {link.org_link_id} in network shape file does not exist '
                f'in the defined capacity classes')
            # link.free_speed = 63

        # Initialize link Volume Delay Function (VDF) parameters; AM period will be considered as default
        try:
            vdf_fftt = 60 * link.other_attrs['length_in_mile'] / link.free_speed
        except TypeError:
            vdf_fftt = 0
        if vdf_fftt: link.other_attrs['VDF_fftt'] = float(vdf_fftt)

        vdf_plf = 1 / (float(phf_dict['AM']))
        link.other_attrs['VDF_plf'] = float(vdf_plf) if vdf_plf else 1

        vdf_cap = link.lanes * link.capacity / vdf_plf
        link.other_attrs['VDF_cap'] = float(vdf_cap) if vdf_cap else 0

        vdf_alpha = float(alpha_dict[FT])
        link.other_attrs['VDF_alpha'] = float(vdf_alpha)

        vdf_beta = float(beta_dict[FT])
        link.other_attrs['VDF_beta'] = float(vdf_beta)

        # Process link data for different time period
        for t_seq, t_period in time_period_dict.items():

            try:
                lanes = int(network_shapefile[str(t_period) + 'LANE'][index])
            except ValueError:
                lanes = 0
                print(f'WARNING: a non-integer value encountered in {str(t_period) + "LANE"} field for '
                      f'link ID {link.org_link_id} in the network shapefile')
            link.other_attrs['lanes' + str(t_seq)] = lanes

            link.other_attrs['free_speed' + str(t_seq)] = link.free_speed  # Same free speed for all time periods

            for allowed_agent in toll_allowed_uses_dict[0]:  # Set all toll prices for all mode types to 0
                link.other_attrs[str(allowed_agent) + str(t_seq)] = 0

            toll = network_shapefile[t_period + 'TOLL'][index] / 100  # cents -> dollars

            try:
                allowed_uses_key = int(network_shapefile[str(t_period + 'LIMIT')][index])
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

            link.other_attrs['link_type' + str(t_seq)] = t_link_type
            link.other_attrs['vdf_code' + str(t_seq)] = t_link_type

            t_vdf_fftt = 60 * link.other_attrs['length_in_mile'] / link.free_speed
            if vdf_fftt: link.other_attrs['VDF_fftt' + str(t_seq)] = float(t_vdf_fftt)

            t_vdf_plf = 1 / (float(phf_dict[t_period]))
            link.other_attrs['VDF_plf' + str(t_seq)] = float(t_vdf_plf) if t_vdf_plf else 1

            t_vdf_cap = lanes * link.capacity / vdf_plf
            link.other_attrs['VDF_cap' + str(t_seq)] = float(t_vdf_cap) if t_vdf_cap else 0

            t_vdf_alpha = float(alpha_dict[FT])
            if t_vdf_alpha: link.other_attrs['VDF_alpha' + str(t_seq)] = float(t_vdf_alpha)

            t_vdf_beta = float(beta_dict[FT])
            if t_vdf_beta: link.other_attrs['VDF_beta' + str(t_seq)] = float(t_vdf_beta)

        for field in other_fields:
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

    writer.writerow(['node_id', 'x_coord', 'y_coord', 'centroid', 'zone_id', 'geometry'])
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
    link_header = ['first', 'link_id', 'from_node_id', 'to_node_id', 'lanes', 'length', 'dir_flag', 'geometry',
                   'free_speed', 'capacity', 'link_type', 'vdf_code']

    first_link = network.link_dict[1]
    other_link_header = list(first_link.other_attrs.keys())

    link_header.extend(other_link_header)

    writer.writerow(link_header)

    for link_id, link in network.link_dict.items():
        line = ['', link.link_id, link.from_node.node_id, link.to_node.node_id, link.lanes, link.length,
                link.dir_flag, link.geometry, link.free_speed, link.capacity, link.link_type, link.vdf_code]

        other_link_att_values = list(link.other_attrs.values())

        line.extend(other_link_att_values)

        writer.writerow(line)
    outfile.close()
    print('link.csv generated')


def district_id_map(net_dir):
    link_net = pd.read_csv(os.path.join(net_dir, 'link.csv'))
    node_net = pd.read_csv(os.path.join(net_dir, 'node.csv'))

    link_taz_jurname = pd.read_csv(os.path.join('./input_files/', 'TPBTAZ3722_TPBMod_JUR.csv'))

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


def cap_adjustment(net_dir):
    link_csv = os.path.join(net_dir, 'link.csv')
    if not os.path.exists(link_csv):
        print(f"File 'link.csv' not found in directory: {net_dir}")
        return

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
            link_adj_cap_net['VDF_cap1'] *= adj_factor
            link_adj_cap_net['VDF_cap2'] *= adj_factor
            link_adj_cap_net['VDF_cap3'] *= adj_factor
            link_adj_cap_net['VDF_cap4'] *= adj_factor

            data_seg_list.append(link_adj_cap_net)

    if data_seg_list:
        df_bd_test = pd.concat(data_seg_list)
        df_bd_test = df_bd_test.sort_values(by="link_id")
        df_bd_test.to_csv(os.path.join(net_dir, 'link.csv'), index=False)


def get_gmns_from_cube(shapefile_path):
    network = _buildnet(shapefile_path)
    _outputNode(network, shapefile_path)
    _outputLink(network, shapefile_path)

if __name__ == '__main__':
    start_time = time.process_time()

    capacity_adjustment = False
    district_id_assignment = True
    cube_net_dir = r'C:\Users\mabbas10\Dropbox (ASU)\2. ASU\2. PhD\2. Projects\NVTA\3_Subarea_analysis\Python codes\test\dec 28-2023\cube_nets'
    # network_list = ['CMP001', 'FFX134_BD','FFX134_NB', 'FFX138_BD', 'FFX138_NB',
    #                'LDN029_BD', 'LDN029_NB', 'LDN033_BD', 'LDN033_NB', 'LDN034', 'MAN003', 'PWC040_BD', 'PWC040_NB']

    network_list = [item for item in os.listdir(cube_net_dir) if os.path.isdir(os.path.join(cube_net_dir, item))]

    for network_file in network_list:
        print("=======================================================================================")
        print("Network = ", network_file)

        network_dir = os.path.join(cube_net_dir, network_file)

        network_shapefile_dir = [ntwk for ntwk in os.listdir(network_dir)
                                 if os.path.isdir(os.path.join(network_dir, ntwk)) and 'NTWK' in ntwk]

        for ntwk in network_shapefile_dir:
            shapfile_path = os.path.join(network_dir, ntwk)
            output_folder = shapfile_path

            network = _buildnet(shapfile_path)
            _outputNode(network, output_folder)
            _outputLink(network, output_folder)

            if capacity_adjustment and network_file.endswith("_BD"):
                cap_adjustment(shapfile_path)

            if district_id_assignment:
                district_id_map(shapfile_path)

    end_time = time.process_time()
    print('Total running time: %s Seconds' % (end_time - start_time))
