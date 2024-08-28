"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes

Outputs the time taken to complete each phase in a plan.

Pass in /var/log/messages as an argument.
"""

import sys
from datetime import datetime
from datetime import timedelta


def phase_exec_time(time1, time2):
    """
    Return the time difference between the 2 times given.
    Taken from:
        http://stackoverflow.com/questions/3096953/
            difference-between-two-time-intervals-in-python
    """
    fmt = '%H:%M:%S'
    tdelta = datetime.strptime(
            time2, fmt) - datetime.strptime(time1, fmt)

    # If the time interval crosses midnight
    if tdelta.days < 0:
        tdelta = timedelta(days=0, seconds=tdelta.seconds,
                           microseconds=tdelta.microseconds)

    return tdelta


def print_phase_times(file_to_read):
    """
    Prints out the time taken to complete each phase in a LITP/ENM plan.
    """
    with open(file_to_read) as infile:
        msgs = infile.readlines()

    num = "0"
    phases = []
    for line in msgs:
        if "TotalTasks:" in line and "Phase" in line:
            phase_num = line.split("Phase ")[1].split("/")[0]

            # Only get first reference to the phase execution
            if phase_num != num:
                phases.append(line.rstrip())
                num = phase_num

        # To find time taken to run last phase
        if "INFO: Deployment Plan execution successful" in line:
            time_plan_ended = line[7:15]

    phase_number = "1"
    # Get time when first phase started executing
    prev_time = phases[0][7:15]

    for line in phases[1:]:
        # Print number of previous phase
        print "Phase " + phase_number
        phase_number = line.split("Phase ")[1].split("/")[0]

        new_time = line[7:15]
        tdelta = phase_exec_time(prev_time, new_time)

        # Print time taken to execute previous phase
        print "Time Taken: " + str(tdelta)
        print "--------------------"

        prev_time = new_time

    # Get time taken to run last phase
    tdelta = phase_exec_time(prev_time, time_plan_ended)
    print "Phase " + phase_number
    print "Time Taken: " + str(tdelta)

print_phase_times(sys.argv[1])
