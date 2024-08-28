"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes

Run this script from your local machine or gateway
to get MS and node logs of specified system.

Run this script like:
python collect_logs.py <SYSTEM>
Ex. python collect_logs.py 38
"""
import os
import sys
import subprocess
from collect_logs_funcs import CollectLogsFuncs

collect_logs_funcs = CollectLogsFuncs
# Disable output buffering to receive the output instantly
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SYSTEM = sys.argv[1]
SYS_FILE = "sys_info.txt"
SYS_FILE_LOC = "{0}/{1}/{2}".format(DIR_PATH, SYSTEM, SYS_FILE)
MS_IP = ""
MS_PASSWORD = ""
# Default file locations on MS
MS_DIR = "/root/Collect_Logs"
MS_LITP_LOGS = "/root/litp_logs"
MS_SCRIPTS_DIR = "{0}/scripts".format(MS_DIR)
FUNCS_SCRIPT = "collect_logs_funcs.py"
MS_COLLECT_SCRIPT = "{0}/collect_ms_logs.py".format(MS_SCRIPTS_DIR)


def get_system_info():
    """
    Retrieve info about system from system file.
    """
    global MS_IP, MS_PASSWORD, MS_DIR, MS_LITP_LOGS
    global MS_SCRIPTS_DIR, FUNCS_SCRIPT, MS_COLLECT_SCRIPT

    # Read file with system-specific information
    with open(SYS_FILE_LOC, 'r') as infile:
        for line in infile:
            if 'ms_ip' in line:
                MS_IP = line.split("=")[1].rstrip()
            elif 'ms_password' in line:
                MS_PASSWORD = line.split("=")[1].rstrip()
            elif 'ms_dir' in line:
                MS_DIR = line.split("=")[1].rstrip()
            elif 'MS_LITP_LOGS' in line:
                MS_LITP_LOGS = line.split("=")[1].rstrip()
            elif 'ms_scripts_dir' in line:
                tmp = line.split("=")[1].rstrip()
                MS_SCRIPTS_DIR = "{0}/{1}".format(MS_DIR, tmp)
            elif 'functions_script' in line:
                FUNCS_SCRIPT = line.split("=")[1].rstrip()
            elif 'ms_collect_script' in line:
                tmp = line.split("=")[1].rstrip()
                MS_COLLECT_SCRIPT = "{0}/{1}".format(MS_SCRIPTS_DIR, tmp)


def collect_logs():
    """
    Collect logs from MS and nodes of given system.
    """
    mkdir = 'ssh root@{0} -C "mkdir {1}"'.format(MS_IP, MS_DIR)
    scp_scripts = "scp -r {0}/scripts/ root@{1}:{2}".format(
        DIR_PATH, MS_IP, MS_DIR)
    scp_funcs = "scp {0}/{1} root@{2}:{3}".format(
        DIR_PATH, FUNCS_SCRIPT, MS_IP, MS_SCRIPTS_DIR)
    scp_sys_files = "scp -r {0}/{1}/ root@{2}:{3}/{1}".format(
        DIR_PATH, SYSTEM, MS_IP, MS_DIR)
    ms_sys_file = "{0}/{1}/{2}".format(MS_DIR, SYSTEM, SYS_FILE)
    collect_cmd = 'ssh root@{0} -C "python {1} {2} {3}"'.format(
        MS_IP, MS_COLLECT_SCRIPT, SYSTEM, ms_sys_file)
    print collect_cmd
    scp_back = "scp -r root@{0}:{1}.tar.gz .".format(MS_IP, MS_LITP_LOGS)
    remove_dirs = 'ssh root@{0} -C "rm -rf {1}; rm -rf {2}*"'.format(
        MS_IP, MS_DIR, MS_LITP_LOGS)

    # If MS_PASSWORD != "NONE", use pexpect
    if MS_PASSWORD != "NONE":
        # Create directory on MS to store log files
        collect_logs_funcs.expect_cmd(mkdir, MS_PASSWORD)
        # SCP the scripts folder to the new directory
        collect_logs_funcs.expect_cmd(scp_scripts, MS_PASSWORD)
        # SCP the functions script
        collect_logs_funcs.expect_cmd(scp_funcs, MS_PASSWORD)
        # SCP files specific to system
        collect_logs_funcs.expect_cmd(scp_sys_files, MS_PASSWORD)
        # Run script on MS to collect logs
        collect_logs_funcs.expect_cmd(collect_cmd, MS_PASSWORD, timeout=900, retries=0)
        # SCP the logs collected to the current machine
        collect_logs_funcs.expect_cmd(scp_back, MS_PASSWORD)
        # Remove the created directories on the MS
        collect_logs_funcs.expect_cmd(remove_dirs, MS_PASSWORD)
    else:
        # Create directory on MS to store log files
        process = subprocess.Popen(
            mkdir, stdout=subprocess.PIPE, shell=True).wait()

        # SCP the scripts folder to the new directory
        scp_scripts += "/scripts"
        process = subprocess.Popen(
            scp_scripts, stdout=subprocess.PIPE, shell=True).wait()

        # SCP files specific to system
        process = subprocess.Popen(
            scp_sys_files, stdout=subprocess.PIPE, shell=True).wait()

        # SCP the functions script
        process = subprocess.Popen(
            scp_funcs, stdout=subprocess.PIPE, shell=True).wait()

        # Run script on MS to collect logs
        #process = subprocess.Popen(
        # collect_cmd, stdout=subprocess.PIPE, shell=True).wait()
        process = subprocess.Popen(
            collect_cmd, stdout=subprocess.PIPE, shell=True)
        out, err = process.communicate()
        for line in out:
            with open("collection_logs.txt", "a") as out_file:
                out_file.write(line)

        # SCP the logs collected to the current machine
        process = subprocess.Popen(
            scp_back, stdout=subprocess.PIPE, shell=True).wait()

        # Remove the created directories on the MS
        print "Removing created dirs on the MS"
        process = subprocess.Popen(
            remove_dirs, stdout=subprocess.PIPE, shell=True).wait()

get_system_info()
collect_logs()
