"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes

Collect logs from the MS creating relevant directories.
Call script to collect peer node logs. Copy node logs here.

TO DO: NEED TO RUN PASSWORD SCRIPTS FIRST.
"""

import sys
import subprocess
import pexpect
from collect_logs_funcs import CollectLogsFuncs
import os.path
from run_ssh_cmd_su import RunSUCommands

collect_logs_funcs = CollectLogsFuncs
# Disable output buffering to receive the output instantly
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

SYSTEM = sys.argv[1]
SYS_FILE = sys.argv[2]
# Default file locations on MS
MS_DIR = "/root/Collect_Logs"
# Directory on MS to store all logs in
MS_LITP_LOGS = "/root/litp_logs"
MS_SCRIPTS_DIR = "{0}/scripts".format(MS_DIR)
LOGS_TO_COPY = "{0}/{1}/ms_logs_to_copy.txt".format(MS_DIR, SYSTEM)
CMD_LOGS = "{0}/{1}/ms_cmds_to_run.txt".format(MS_DIR, SYSTEM)
# Create directory for MS specific Logs
MS_LOG_DIR = "{0}/ms_logs".format(MS_LITP_LOGS)

with open(SYS_FILE, 'r') as infile:
    for line in infile:
        if 'peer_user' in line:
            PEER_USER = line.split("=")[1].rstrip()
        elif 'peer_password' in line:
            PEER_PASSWORD = line.split("=")[1].rstrip()
        elif 'su_password' in line:
            PEER_SU_PASSWORD = line.split("=")[1].rstrip()
        elif 'ms_dir' in line:
            MS_DIR = line.split("=")[1].rstrip()
        elif 'ms_litp_logs' in line:
            MS_LITP_LOGS = line.split("=")[1].rstrip()
        elif 'ms_scripts_dir' in line:
            tmp = line.split("=")[1].rstrip()
            MS_SCRIPTS_DIR = "{0}/{1}".format(MS_DIR, tmp)
        elif 'ms_copy_logs' in line:
            tmp = line.split("=")[1].rstrip()
            LOGS_TO_COPY = "{0}/{1}/{2}".format(MS_DIR, SYSTEM, tmp)
        elif 'ms_run_cmds' in line:
            tmp = line.split("=")[1].rstrip()
            CMD_LOGS = "{0}/{1}/{2}".format(MS_DIR, SYSTEM, tmp)
        elif 'ms_logs_dir' in line:
            tmp = line.split("=")[1].rstrip()
            MS_LOG_DIR = "{0}/{1}".format(MS_LITP_LOGS, tmp)

with open(LOGS_TO_COPY) as f:
    COPY_LOGS = f.readlines()

with open(CMD_LOGS) as f:
    RUN_CMDS = f.readlines()

collect_logs_funcs.mkdir_parent(MS_LOG_DIR)

# Run the specified commands piping the output to the specified file
for line in RUN_CMDS:
    line = line.rstrip()
    # '|||' to be used in files to separate
    # commands and files their output is to go into
    cmd_to_run = line.split(" ||| ")[0]
    output_file = "{0}/{1}".format(MS_LOG_DIR, line.split(" ||| ")[1])

    cmd = "{0} > {1}".format(cmd_to_run, output_file)
    print cmd
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()

# Copy all specified logs to newly created MS log directory
for line in COPY_LOGS:
    line = line.rstrip()
    cp_from = line.split()[0]
    cp_to = "{0}/{1}".format(MS_LOG_DIR, line.split()[1])

    # If directory, copy all of its contents
    if cp_from[-1] == '/':
        collect_logs_funcs.copy_dir(cp_from, cp_to)
    # If multiple (eg. logrotated) files defined in ms_logs_to_copy.txt
    elif cp_from[-1] == '*':
        file_to_cp = (cp_from.rsplit('/', 1)[1]).rsplit('*', 1)[0]
        dir_to_cp_from = cp_from.rsplit('/', 1)[0]
        # List all files in the dir and copy those containing the filename
        # to a new directory
        dir_contents = os.listdir(dir_to_cp_from)
        LOGTRACKED_DIR = "{0}/{1}".format(MS_LOG_DIR, file_to_cp)
        collect_logs_funcs.mkdir_parent(LOGTRACKED_DIR)
        i = 0
        for file_name in dir_contents:
            if (file_to_cp in file_name):
                collect_logs_funcs.copy_file(dir_to_cp_from + '/' + file_name,
                                             LOGTRACKED_DIR)
                i = i+1
    else:
        # Otherwise, just copy the file
        collect_logs_funcs.copy_file(cp_from, cp_to)

# Run script to set passwords on all nodes
# TO DO: FOR ALL SYSTEMS
SET_PASS_SH = "{0}/{1}/reset_passwords.bsh".format(MS_DIR, SYSTEM)
CMD = "sh {0}".format(SET_PASS_SH)
print CMD
subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True).communicate()

# Run script to collect logs off nodes
CMD = "python {0}/collect_node_logs.py {1} {2}".format(
    MS_SCRIPTS_DIR, SYSTEM, SYS_FILE)
print CMD
# PROCESS = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)

collect_logs_funcs.expect_cmd(CMD, PEER_PASSWORD, timeout=900, retries=1)

# Print the output of running the node collection script
# NODE_LOGS = "node_collection_logs.txt"
# print "Logging node collection script output to {0}".format(NODE_LOGS)
# for line in iter(PROCESS.stdout.readline, ''):
#     with open("{0}/{1}".format(MS_LITP_LOGS, NODE_LOGS), "a") as out_file:
#         out_file.write(line)

NODES_FILE = "{0}/nodes.txt".format(MS_LITP_LOGS)

# Check if nodes.txt exists
if os.path.isfile(NODES_FILE):
    # SCP logs from each node to MS
    with open(NODES_FILE) as f:
        NODES_LIST = f.readlines()

    for node in NODES_LIST:
        cmd = "scp -r {0}@{1}:/home/{0}/{1} {2}".format(
            PEER_USER, node.rstrip(), MS_LITP_LOGS)
        print cmd
        child = pexpect.spawn(cmd)
        child.expect(["password:", pexpect.EOF])
        child.sendline(PEER_PASSWORD)
        child.expect(pexpect.EOF)

        # Remove created log directory on each node
        cmd = "rm -rf /home/{0}/{1}*".format(PEER_USER, node.rstrip())
        remove_dir = RunSUCommands(node.rstrip(), PEER_USER,
                                   PEER_PASSWORD, PEER_SU_PASSWORD, cmd)
        remove_dir.run_su_cmds()

# Tar created log directory
CMD = "tar -czf litp_logs.tar.gz litp_logs".format(MS_LITP_LOGS)
print CMD
subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True).communicate()
