#/usr/bin/env python

import traceback
import os
import re
from collections import OrderedDict

# regular expression to match the lines we need from the sed file
REGEX = r'^(?:.*?)(=)'
# map the sed variable names to the cluster spec variable names
SITEDATA_CLUSTERSPEC_MAP = {
    'LMS_IP': 'ms_ip',
    'LMS_hostname': 'ms_host',
    'LMS_eth0_macaddress': 'ms_eth0_mac',
    'LMS_ilo_IP': 'ms_ilo_ip',
    'LMS_iloUsername': 'ms_ilo_username',
    'LMS_iloPassword': 'ms_ilo_password',
    'LMS_subnet': 'ms_subnet',
    'LMS_gateway': 'ms_gateway'
}
# the file name to give the cluster spec
CLUSTER_SPEC_FILENAME = 'enm_cluster_spec.sh'


cluster_data = OrderedDict()
# data that cannot be pulled from the SED file or isn't required at all, we set
# it manually
cluster_data['blade_type'] = 'G8'
cluster_data['ms_ilo_ip'] = ''
cluster_data['ms_ilo_username'] = ''
cluster_data['ms_ilo_password'] = ''
cluster_data['ms_ip'] = ''
cluster_data['ms_subnet'] = ''
cluster_data['ms_gateway'] = ''
cluster_data['ms_vlan'] = ''
cluster_data['ms_host'] = ''
cluster_data['ms_eth0_mac'] = ''
cluster_data['node_hostname[0]'] = 'NULL'
cluster_data['node_ip[0]'] = 'NULL'

site_engineering_data = OrderedDict()

# get the directory we're running the parser from and locate all subdirectories
current_directory = os.path.abspath(__file__)
directory_name = os.path.dirname(current_directory)
subdirectories = [
    os.path.join(directory_name, f)
    for f in os.listdir(directory_name)
    if os.path.isdir(os.path.join(directory_name, f))
]

try:
    # find site_engineering_data subdirectory
    site_data_directory = [
        dir for dir in subdirectories if 'site_engineering_data' in dir
    ][0]
    # get the files from the directory
    site_data_directory_files = [
        f for f in os.listdir(site_data_directory)
        if os.path.isfile(os.path.join(site_data_directory, f))
    ]
    # find the sed file from the files in the directory
    site_data_file = [
        f for f in site_data_directory_files
        if 'SiteEngineering' in f and 'ENM' in f and 'Cluster1032' in f
    ][0]
    site_data_path = os.path.join(
        site_data_directory, site_data_file
    )
    # open the file and read the contents
    with open(site_data_path, 'r') as f:
        file_contents = f.readlines()
    # for each line in the file, if the line doesn't start with comment, check
    # if it matches a line we want and if it does, strip away unwanted
    # characters and put them into key:value pairs
    for line in file_contents:
        if not line.startswith('#'):
            matched = re.match(REGEX, line)
            if matched:
                key = matched.group(0).rstrip('=')
                value = line.split(matched.group(0))[-1].strip('\n')
                site_engineering_data[key] = value
    # for each key in the dictionary we just created, if the key also exists in
    # the map, set the value to the cluster spec variable
    for key, value in site_engineering_data.iteritems():
        if key in SITEDATA_CLUSTERSPEC_MAP.keys():
            cluster_data[SITEDATA_CLUSTERSPEC_MAP[key]] = value
    # write to cluster spec file all the required key value pairs
    cluster_spec_path = os.path.join(
        site_data_directory, CLUSTER_SPEC_FILENAME
    )
    with open(cluster_spec_path, 'w') as f:
        f.write('#/bin/bash\n')
        f.write('\n')
        for key, value in cluster_data.iteritems():
            f.write('{0}="{1}"\n'.format(key, value))
except IndexError as err:
    print traceback.format_exc()
except IOError as err:
    print traceback.format_exc()
