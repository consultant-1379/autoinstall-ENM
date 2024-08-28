#!/usr/bin/env python

import sys
import os
from run_sshcmds import NodeConnect


print "Collecting LITP logs from the system..."

print sys.argv
if len(sys.argv) != 2:
    print "Not enough arguments passed: USAGE - " \
          "python log_collection.py <MS-IP-ADDRESS>"
    sys.exit(1)

# GET MS NODE INFORMATION
ms_ip = sys.argv[1]
ms_passwd = "12shroot"

# SCP FILES TO MS

node = NodeConnect(ms_ip, "root", ms_passwd)
# COPY THE LOG COLLECTION SCRIPTS ACROSS TO THE MS
local_path = os.path.dirname(os.path.realpath(__file__)) + "/collectlogs.sh"
remote_path = "/tmp/collectlogs.sh"
#print "Copy of %s to %s on %s" % (local_path, remote_path, ms_ip)
node.copy_file_to(local_path, remote_path)
local_path = os.path.dirname(os.path.realpath(__file__)) + "/scp_file.exp"
remote_path = "/tmp/scp_file.exp"
#print "Copy of %s to %s on %s" % (local_path, remote_path, ms_ip)
node.copy_file_to(local_path, remote_path)
local_path = os.path.dirname(os.path.realpath(__file__)) + "/key_setup.exp"
remote_path = "/tmp/key_setup.exp"
#print "Copy of %s to %s on %s" % (local_path, remote_path, ms_ip)
node.copy_file_to(local_path, remote_path)

local_path = os.path.dirname(os.path.realpath(__file__)) + "/reset_passwords.bsh"
remote_path = "/tmp/reset_passwords.bsh"
#print "Copy of %s to %s on %s" % (local_path, remote_path, ms_ip)
node.copy_file_to(local_path, remote_path)

local_path = os.path.dirname(os.path.realpath(__file__)) + "/reset_passwords.py"
remote_path = "/tmp/reset_passwords.py"
#print "Copy of %s to %s on %s" % (local_path, remote_path, ms_ip)
node.copy_file_to(local_path, remote_path)

cmd = "sh /tmp/collectlogs.sh > /tmp/message_collection_log.log"
stdout, stderr, exit_code = node.run_command(cmd, logs=False)
'''if exit_code != 0 or stderr != [] or stdout != []:
    print "----------------------------------------------"
    print stdout
    print stderr
    print exit_code
    print "ERROR: Node collection script failed"
    print "----------------------------------------------"
    exit(1)'''

cmd = "ls /tmp/ | grep 'litp_messages.tar.gz'"
stdout, stderr, exit_code = node.run_command(cmd, logs=False)
if exit_code != 0 or stderr != [] or stdout == []:
    print "----------------------------------------------"
    print stdout
    print stderr
    print exit_code
    print "ERROR: No log .tar.gz file exists"
    print "----------------------------------------------"
    exit(1)

home_dir = os.environ["HOME"]
if "WORKSPACE" in os.environ:
    home_dir = os.environ["WORKSPACE"]


remote_path = "/tmp/message_collection_log.log"
local_path = home_dir + "/" + "message_collection_log.log"
print "Copy of %s from %s to %s" % (remote_path, ms_ip, local_path)
node.copy_file_from(remote_path, local_path)

remote_path = "/tmp/" + stdout[0]
local_path = home_dir + "/" + stdout[0]
print "Copy of %s from %s to %s" % (remote_path, ms_ip, local_path)
node.copy_file_from(remote_path, local_path)

cmd = "rm -rf %s /tmp/message_collection_log.log /tmp/collectlogs.sh " \
      "/tmp/scp_file.exp /tmp/key_setup.exp" % remote_path
stdout, stderr, exit_code = node.run_command(cmd, logs=False)
if exit_code != 0 or stderr != [] or stdout != []:
    print "----------------------------------------------"
    print stdout
    print stderr
    print exit_code
    print "ERROR: Deletion of files failed"
    print "----------------------------------------------"
    exit(1)
