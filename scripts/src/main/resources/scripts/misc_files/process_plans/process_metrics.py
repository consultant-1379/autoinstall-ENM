"""
Name    : process_metrics.py
Purpose : Process metrics log and display in an easier to read format.
        : Helps understanding and aids faster debugging of plans.
"""
#!/usr/bin/env python
import sys
import textwrap
from argparse import ArgumentParser, RawDescriptionHelpFormatter


def printlines(parsed_args):
    """
    Print the Task Details
    :param args: parsed cmd line arguments
    """
    phase = None
    failed = None
    stopped = None
    success = None
    timetaken = None
    cback = None
    configs = None
    myphase = None
    plantimetaken = None

    lines = filter(None, (line.rstrip() for line in open(parsed_args.file)))
    print "Phase    NoOfCallbackTasks   NoOfConfigTasks   NoOfFailedTasks\
    NoOfStoppedTasks   NoOfSuccessfulTasks   TimeTaken"

    printedphases = list()
    for line in lines:
        if "[Run]" in line and 'DisablePuppet' not in line:
            mylist = line.split('[Run]')[1]
            myphase = is_phase_heading(mylist)

            if 'CallbackTask_' in line:
                #Skip lines related to specific Callback tasks.
                continue
            newlist = mylist.split('].')
            for item in newlist:
                if myphase and myphase in item:
                    phase = item.lstrip('[')
                if 'NoOfCallbackTasks' in item:
                    cback = item.split('=')[1]
                if 'NoOfConfigTasks' in item:
                    configs = item.split('=')[1]
                if 'NoOfFailedTasks' in item:
                    failed = item.split('=')[1]
                if 'NoOfStoppedTasks' in item:
                    stopped = item.split('=')[1]
                if 'NoOfSuccessfulTasks' in item:
                    success = item.split('=')[1]
                if 'TimeTaken' in item:
                    timetaken = item.split('=')[1]
                if '.TimeTaken' in item:
                    plantimetaken = item.split('=')[1]

        if phase and (cback or configs) and failed and \
           stopped and success and timetaken:
            if not cback:
                cback = 0
            if not configs:
                configs = 0
            if phase not in printedphases:
                print "{0: <9}".format(phase) + "{0: <20}".format(cback) + \
                      "{0: <17}".format(configs) + ' ' + \
                    "{0: <19}".format(failed) + "{0: <19}".format(stopped) + \
                    "{0: <22}".format(success) + "{0}".format(timetaken)
                printedphases.append(phase)
                phase = None
                failed = None
                stopped = None
                success = None
                timetaken = None
                cback = None
                configs = None
                myphase = None
        if plantimetaken:
            print "Plan execution time: {0}".format(plantimetaken)
            printedphases[:] = []
            plantimetaken = None
            timetaken = None


def is_phase_heading(line):
    """
    Determines if Phase heading is in line and returns heading if found
    :param line: line to check
    """
    newlist = line.split('.')[0]
    if 'Phase' in newlist:
        newlist = newlist.lstrip('[')
        newlist = newlist.rstrip(']')
        return newlist
    return None


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
python process_metrics.py -f metrics.log
python process_metrics.py -f ~/Downloads/metrics.log

''')
    arg_parser = \
        ArgumentParser(prog="process_metrics.py",
                       formatter_class=RawDescriptionHelpFormatter,
                       epilog=upgrade_epilog)

    arg_parser.add_argument('-f', '--file',
                            dest='file',
                            required=False,
                            help='litp metrics log to process')

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
