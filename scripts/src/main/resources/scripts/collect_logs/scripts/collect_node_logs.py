"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes
"""

import os
import sys
import subprocess
from run_ssh_cmd_su import RunSUCommands

# Disable output buffering to receive the output instantly
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

SYSTEM = sys.argv[1]
SYS_FILE = sys.argv[2]
# Default file locations on MS
MS_DIR = "/root/Collect_Logs"
# Directory on MS to store all logs in
MS_LITP_LOGS = "/root/litp_logs"

LOGS_TO_COPY = "{0}/{1}/node_logs_to_copy.txt".format(MS_DIR, SYSTEM)
CMD_LOGS = "{0}/{1}/node_cmds_to_run.txt".format(MS_DIR, SYSTEM)

with open(SYS_FILE, 'r') as infile:
    for line in infile:
        if 'cluster_path' in line:
            CLUSTER_PATH = line.split("=")[1].rstrip()
        elif 'peer_user' in line:
            PEER_USER = line.split("=")[1].rstrip()
        elif 'peer_password' in line:
            PEER_PASSWORD = line.split("=")[1].rstrip()
        elif 'su_password' in line:
            PEER_SU_PASSWORD = line.split("=")[1].rstrip()
        elif 'ms_dir' in line:
            MS_DIR = line.split("=")[1].rstrip()
        elif 'ms_litp_logs' in line:
            MS_LITP_LOGS = line.split("=")[1].rstrip()
        elif 'node_copy_logs' in line:
            tmp = line.split("=")[1].rstrip()
            LOGS_TO_COPY = "{0}/{1}/{2}".format(MS_DIR, SYSTEM, tmp)
        elif 'node_run_cmds' in line:
            tmp = line.split("=")[1].rstrip()
            CMD_LOGS = "{0}/{1}/{2}".format(MS_DIR, SYSTEM, tmp)

with open(LOGS_TO_COPY) as f:
    COPY_LOGS = f.readlines()

with open(CMD_LOGS) as f:
    RUN_CMDS = f.readlines()

# Get all nodes in cluster
CMD = 'litp show -rp {0} | grep -v "inherited from" | grep -B1 "type: node" ' \
      '| grep -v type | grep "/"'.format(CLUSTER_PATH)
PROCESS = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)
PEER_NODES = PROCESS.communicate()[0]

for node in PEER_NODES.splitlines():
    # Get nodes hostname
    cmd = 'litp show -p {0} | grep hostname | ' \
          'sed "s/        hostname: //g"'.format(node)
    print cmd
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    hostname = process.communicate()[0][:-1]

    # Add node name to file for MS to SCP logs over
    for host in hostname.splitlines():
        with open("{0}/nodes.txt".format(MS_LITP_LOGS), "a") as node_file:
            node_file.write("{0}\n".format(host))

        # Create directory on node to copy its logs to
        peer_dir = "/home/{0}/{1}".format(PEER_USER, host)
        cmd = "mkdir {0}".format(peer_dir)
        node_dir = RunSUCommands(hostname, PEER_USER,
                                 PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
        node_dir.run_cmds()

        # Read file of logs to copy and GET TO WORK
        for line in COPY_LOGS:
            line = line.rstrip()
            cp_from = line.split()[0]
            cp_to = "{0}/{1}".format(peer_dir, line.split()[1])

            cmd = "cp {0} {1}".format(cp_from, cp_to)
            print cmd

            # If directory, copy all of its contents
            if cp_from[-1] == '/':
                cmd += " -r"

            copy_file = RunSUCommands(hostname, PEER_USER,
                                      PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
            copy_file.run_su_cmds()

        # Read file of commands to run and GET TO GOD DAMN WORK
        for line in RUN_CMDS:
            line = line.rstrip()
            cmd_to_run = line.split(" ||| ")[0]
            print cmd_to_run
            output_file = "{0}/{1}".format(peer_dir, line.split(" ||| ")[1])

            cmd = "{0} > {1}".format(cmd_to_run, output_file)
            exec_cmd = RunSUCommands(hostname, PEER_USER,
                                     PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
            exec_cmd.run_su_cmds()

        # Change user permissions on all files in
        # created log directory so they can be SCPed
        print 'Changing user permissions on files so they can be SCPed'
        cmd = "chmod -R 745 {0}/*".format(peer_dir)

        run_cmd = RunSUCommands(hostname, PEER_USER,
                                PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
        run_cmd.run_su_cmds()
