"""
Name    : process_litp_show.py
Purpose : Process log containing output of litp show_plan into an
        : easier to read format.
        : Helps understanding and aids faster debugging of plans.
"""
#!/usr/bin/env python
import re
import sys
import os
import textwrap
from argparse import ArgumentParser, RawDescriptionHelpFormatter


def printtaskdetails(item_list, info_list, term_width):
    """
    Helper Function to Print the Task Details and
    fit the printout to the Terminal width if desired.
    :param item_list
    :param info_list
    :param term_width
    """
    to_print = item_list.ljust(70) + '\t' + info_list
    if term_width:
        if term_width < len(to_print):
            to_print = to_print[:term_width - 1]
    print to_print


def printlines(parsed_args):
    """
    Print the Task Details
    :param args: parsed cmd line arguments
    """
    item_list = None
    info_list = None
    gathering_info = False
    term_width = None
    item_to_print = None

    if parsed_args.force_one_line:
        term_width = get_terminal_width()

    lines = filter(None, (line.rstrip() for line in open(parsed_args.file)))
    for line in lines:
        line = line.lstrip()
        item_to_print = is_phase_heading(line)

        if item_to_print:
            # Print collated Task Details
            if item_list and info_list:
                printtaskdetails(item_list, info_list, term_width)
                gathering_info = False
                info_list = None
            print item_to_print.strip()
        elif "Task status" in line or "-----------" in line:
            pass
        elif "Initial" in line or "Success" in line or "Failed" in line:
            if gathering_info:
                printtaskdetails(item_list, info_list, term_width)
                gathering_info = False
                info_list = None
            item_list = line
        else:
            if item_list:
                gathering_info = True
                if info_list:
                    info_list += ' ' + line
                else:
                    info_list = line

        if "Plan Status:" in line or "Tasks" in line:
            print line


def is_phase_heading(line):
    """
    Determines if Phase heading is in line and returns heading if found
    :param line: line to check
    """
    matched = re.match(r'Phase \d+', line)
    if matched:
        return line
    return None


def get_terminal_size(fdesc=1):
    """
    Returns height and width of current terminal. First tries to get
    size via termios.TIOCGWINSZ, then from environment. Defaults to 25
    lines x 80 columns if both methods fail.

    :param fdesc: file descriptor (default: 1=stdout)
    """
    try:
        import fcntl
        import termios
        import struct
        heightwidth = \
            struct.unpack('hh', fcntl.ioctl(fdesc, termios.TIOCGWINSZ, '1234'))
    except Exception as excp:
        try:
            heightwidth = (os.environ['LINES'], os.environ['COLUMNS'])
        except Exception as excp:
            print "Error '{0}'. Arguments {1}.".format(excp.message, excp.args)
            heightwidth = (25, 80)

    return heightwidth


def get_terminal_width(fdesc=1):
    """
    Returns width of terminal if it is a tty, 999 otherwise

    :param fdesc: file descriptor (default: 1=stdout)
    """
    if os.isatty(fdesc):
        width = get_terminal_size(fdesc)[1]
    else:
        width = 999

    return width


def process_arguments(parser, parsed_args):
    """
    Additional logic to validate command line arguments
    :param parser
    :param upgrade_args: parsed arguments
    """
    if parsed_args.file is None:
        parser.error('Need enminst log to process')
    else:
        args_ok = True

    if not args_ok:
        parser.print_usage()


def create_parser():
    """
    Creates and configures parser to process command line arguments
    :return:
    """
    upgrade_epilog = textwrap.dedent('''
Examples:
python process_litpshow.py -f show_plan.log
python process_litpshow.py -f show_plan.log --force_one_line
python process_litpshow.py -f ~/Downloads/show_plan.log --force_one_line

''')
    arg_parser = \
        ArgumentParser(prog="process_litpshow.py",
                       formatter_class=RawDescriptionHelpFormatter,
                       epilog=upgrade_epilog)

    arg_parser.add_argument('-f', '--file',
                            dest='file',
                            required=False,
                            help='litp show_plan Logfile to process')

    arg_parser.add_argument('-force', '--force_one_line',
                            dest='force_one_line',
                            default=False,
                            action='store_true',
                            help='Print details on one line. Truncates Info.')

    return arg_parser


def main(args):
    """
    Main function
    :param args: arguments to be processed
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args[1:])
    process_arguments(parser, parsed_args)
    printlines(parsed_args)

if __name__ == '__main__':
    if sys.argv is not None:
        main(sys.argv)
