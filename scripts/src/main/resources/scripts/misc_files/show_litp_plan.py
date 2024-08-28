"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     November 2016
@author:    Laura Forbes

To be run on an MS.
Runs a 'litp show_plan -a' command every
            5 minutes while plan is in a 'Running' state.
Outputs Running Phases/Tasks to running_phases.txt.
"""

import subprocess
import time


CMD = "litp show_plan -a"
SAVE_TO_FILE = "running_phases.txt"
PLAN_RUNNING = True

while PLAN_RUNNING:
    PROCESS = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)
    PLAN_STATUS = None
    SHOW_PLAN = []

    for line in iter(PROCESS.stdout.readline, ''):
        SHOW_PLAN.append(line)
        if "Plan Status:" in line:
            PLAN_STATUS = line.split()[-1]

    if PLAN_STATUS == "Running":
        with open(SAVE_TO_FILE, "a") as out_file:
            out_file.write(time.strftime(
                    "Date: %d/%m/%Y   Time: %H:%M:%S\nlitp show_plan -a\n\n"))
            for line in SHOW_PLAN:
                out_file.write(line)
            out_file.write("\n#########################################"
                           "#######################################\n\n")
        time.sleep(300)
    else:
        print "Plan no longer in 'Running' state.\nOutput saved to {0}".format(
                                                                SAVE_TO_FILE)
        PLAN_RUNNING = False
