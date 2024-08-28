"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     September 2019
@author:    Terry Farrell, Diarmuid Leahy

Performs a comparison on an ENM Deployment Description and a
SED. Outputs a list of missing/extra parameters found in the
DD that are either not found or surplus in the SED
"""

import os
import sys
import re
import textwrap
import xml.etree.ElementTree as ElementTree

from argparse import RawTextHelpFormatter, ArgumentParser

RED   = "\033[31m"
GREEN = "\033[32m"
YELLOW= "\033[33m"
RESET = "\033[0m"
HEADER = "\033[;1m"

class DeploymentHandler():
    """
    Class to perform the parameter comparison
    """
    def __init__(self):
        self.litp_parameter_set = set()
        self.sed_parameter_map = {}
        self.deployment_file = ''
        self.sed_file = ''

    def process_files(self):
        """
        Scan through the DD and SED files populating data structures containing
        lists of variables seen in each
        """
        self.litp_parameter_set = set()
        try:
            root = ElementTree.parse(self.deployment_file)
        except IOError as ex:
            print_in_colour(str(ex), RED)
            sys.exit(1)
        for elem in root.getiterator():
            text = elem.text
            if text:
                paramList = [re.match('%%(.*)%%', match).group(1) for match in
                             re.split('(%%[^%]+%%)', text) if
                             re.match('%%([^%]+)%%', match)]
                for param in paramList:
                    self.litp_parameter_set.add(param)
        try:
            with open(self.sed_file) as file:
                lines = file.readlines()
                for line in lines:
                    if (re.match('(\S+)=(\S+)', line) and
                            line != 'Variable_Name=Variable_Value'):
                        (parameter, sep, value) = line.partition('=')
                        self.sed_parameter_map[parameter] = value
        except IOError as ex:
            print_in_colour(str(ex), RED)
            sys.exit(1)


def print_in_colour(the_message, colour):
    """
    Print a message in a given colour
    :param text: Message to print
    :type text: str or list
    :param colour: Colour in which to print the message
    :type colour: str
    """
    if isinstance(the_message, list):
        the_message = "\n".join(the_message)
    print colour + the_message + RESET

def print_missing_params(deployment_set, sed_map):
    """
    Print a list of missing parameters
    :param deployment_set: Set containing all params found in DD
    :type deployment_set: Set -> str
    :param sed_map: A dictionary containing param values keyed by param names
    :type sed_map: dict[str] -> str
    :return: None
    """
    ignore_list = [ "ERICrhel76jbossimage", "ERICsles11ncmimage",
                    "ERICrhel6baseimage", "ERICrhel6jbossimage",
                    "ERICrhel76lsbimage", "ERICrhel7baseimage",
                    "uuid_ms_disk0", "vm_ssh_key"]

    sed_set = set(sed_map.keys())
    sorted_diff = sorted(deployment_set.difference(sed_set))
    collected_missing = []
    collected_missing_ignore = []

    for param in sorted_diff:
        if param not in ignore_list:
            if (param.endswith('_password_encrypted') and
                    param[0:param.index('_password_encrypted')]+"_password"
                    not in sed_set):
                collected_missing.append(param)
            elif not(param.endswith('_password_encrypted')):
                collected_missing.append(param)
        else:
            collected_missing_ignore.append(param)

    print_in_colour("\nPrinting missing parameters from SED :\n", HEADER)

    if len(collected_missing) > 0:
        print_in_colour(collected_missing, RED)
    else:
        print_in_colour('\n-- No essential parameters missing --\n', GREEN)

    if len(collected_missing_ignore) > 0:
        print_in_colour("\nMissing parameters, but can be ignored "
            "(populated from working.cfg) : \n", HEADER)
        print_in_colour(collected_missing_ignore, YELLOW)

def print_extra_params(deployment_set, sed_map):
    """
    Print a list of extra parameters
    :param deployment_set: Set containing all params found in DD
    :type deployment_set: Set -> str
    :param sed_map: A dictionary containing param values keyed by param names
    :type sed_map: dict[str] -> str
    :return: None
    """
    print_in_colour("\nPrinting extra parameters from SED:\n", HEADER)
    sed_set = set(sed_map.keys())
    sorted_diff = sorted(sed_set.difference(deployment_set))
    for param in sorted_diff:
        if (param.endswith('_password') and param+'_encrypted'
                not in deployment_set):
            print param
        elif not(param.endswith('_password')):
            print param

def create_arg_parser():
    """
    Create an object for parsing the arguments passed into the script.
    Defines helptext and required parameters
    :return: ArgumentParser object
    """
    epilog = textwrap.dedent('''
# %(prog)s --missing -> Display parameters missing from Site Engineering \
Document
# %(prog)s --extra   -> Display extra parameters from Site Engineering \
Document
# If neither of the above are specified, both checks are performed
''')

    this_script = os.path.basename(__file__)

    parser = ArgumentParser(prog=this_script,
                            epilog=epilog,
                            formatter_class=RawTextHelpFormatter,
                            add_help=False)

    parser.add_argument('deployment_file', help='Path to Deployment XML file')
    parser.add_argument('sed_file', help='Path to Site Engineering Document')
    parser.add_argument('--missing', help='Display parameters missing from \
Site Engineering Document', action='store_true')
    parser.add_argument('--extra', help='Display extra parameters from Site \
Engineering Document', action='store_true')
    parser.add_argument('--help', '-h', action='help',
                        help='Show this help message and exit')
    return parser

if __name__ == '__main__':
    parser = create_arg_parser()
    args = parser.parse_args()
    handler = DeploymentHandler()
    deployment_file = args.deployment_file
    sed_file = args.sed_file
    handler.deployment_file =  deployment_file
    handler.sed_file = sed_file
    handler.process_files()
    deployment_set = handler.litp_parameter_set
    sed_map = handler.sed_parameter_map
    if args.missing:
        print_missing_params(deployment_set, sed_map)
    if args.extra:
        print_extra_params(deployment_set, sed_map)
    if not(args.missing) and not(args.extra):
        print_missing_params(deployment_set, sed_map)
        print_extra_params(deployment_set, sed_map)
