"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     December 2015
@author:    Laura Forbes

Takes a file containing the required arguments and runs an E-CDB installation.
"""

import sys
import os
import subprocess

# Disable output buffering to receive the output instantly
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

MS_IP = ""
SET_SED = ""
XML_FILE = ""
CLUSTER_ID = ""
OS_PATCH_VER = ""
OS_RH7_PATCH_VER = ""
SKIP_CLEAN = "NO"
SKIP_OS_INSTALL = "NO"
SKIP_PATCH_INSTALL = "NO"
LITP_DROP = ""
ENM_DROP = ""
SKIP_LITP = "NO"
SKIP_ENM = "NO"
LITP_ISO = ""
ENM_ISO = ""
SSH_ROOT_MS = ""
CI_VERSION = "latest"
PRODUCT_SET = ""
OS_VERSION = ""
STARS = "*" * 100
STAR_COMMENT = "{0}\n{1}\n{0}"


def get_values_from_file(path_to_envvariables):
    """
    Get relevant values from passed file.
    """
    global MS_IP, SSH_ROOT_MS, CLUSTER_ID, SET_SED, XML_FILE, LITP_DROP
    global LITP_ISO, ENM_DROP, ENM_ISO, OS_PATCH_VER
    global SKIP_CLEAN, SKIP_OS_INSTALL, SKIP_PATCH_INSTALL, SKIP_LITP, SKIP_ENM
    global CI_VERSION, OS_RH7_PATCH_VER, PRODUCT_SET, OS_VERSION

    with open(path_to_envvariables, 'r') as infile:
        for line in infile:
            if 'msip' in line:
                MS_IP = line.split("=")[1].rstrip()
                SSH_ROOT_MS = "ssh -o UserKnownHostsFile=/dev/null -o " \
                              "StrictHostKeyChecking=no -o " \
                              "ServerAliveInterval=30 root@{0} ".format(MS_IP)
            elif 'clusterId' in line:
                CLUSTER_ID = line.split("=")[1].rstrip()
            elif 'setSED' in line:
                SET_SED = line.split("=")[1].rstrip()
            elif 'xmlFile' in line:
                XML_FILE = line.split("=")[1].rstrip()
            elif 'LITPDrop' in line:
                LITP_DROP = line.split("=")[1].rstrip()
            elif 'LITPIso' in line:
                LITP_ISO = line.split("=")[1].rstrip()
            elif 'ENMDrop' in line:
                ENM_DROP = line.split("=")[1].rstrip()
            elif 'ENMIso' in line:
                ENM_ISO = line.split("=")[1].rstrip()
            elif 'skipOsPatch' in line:
                SKIP_PATCH_INSTALL = line.split("=")[1].rstrip()
            elif 'OSPatchVer' in line:
                OS_PATCH_VER = line.split("=")[1].rstrip()
            elif 'RHEL7PatchVer' in line:
                OS_RH7_PATCH_VER = line.split("=")[1].rstrip()
            elif 'skipTearDown' in line:
                SKIP_CLEAN = line.split("=")[1].rstrip()
            elif 'skipOsInstall' in line:
                SKIP_OS_INSTALL = line.split("=")[1].rstrip()
            elif 'skipLitp' in line:
                SKIP_LITP = line.split("=")[1].rstrip()
            elif 'skipEnm' in line:
                SKIP_ENM = line.split("=")[1].rstrip()
            elif 'cifwk' in line:
                CI_VERSION = line.split("=")[1].rstrip()
            elif 'productSet' in line:
                PRODUCT_SET = line.split("=")[1].rstrip()
            elif 'OSversion' in line:
                OS_VERSION = line.split("=")[1].rstrip()

def run_install():
    """
    Runs an installation with the LITP ISO,
    ENM ISO and OS Patches specified.
    """
    info = "ENSURING LITP IS NOT IN MAINTENANCE MODE BY " \
           "SETTING THE ENABLED PROPERTY TO FALSE"
    print STAR_COMMENT.format(STARS, info)

    cmd = "{0} litp update -p /litp/maintenance " \
          "-o enabled=false".format(SSH_ROOT_MS)
    print cmd
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    stderr = process.communicate()[1]
    if stderr is not None:
        sys.exit("Unable to set LITP Maintenance 'enabled' property to false.")

    os_version_flag = ""
    if OS_VERSION:
        os_version_flag = " --osVersion {0}_x86".format(OS_VERSION)

    print "CI Framework version"
    print CI_VERSION
    # Construct install command
    cmd = "/proj/lciadm100/cifwk/{9}/bin/cicmd deployment --clusterid {0}" \
          " --installType initial_install --environment physical --product " \
          "ENM --skipOsInstall {1} --skipPatchInstall"\
          " {2} --deployProduct LITP2 --skipLitpInstall {3} "\
          "--litpDrop {4}::{5} --skipEnmInstall {6} --setSED" \
          " {7} --xmlFile {8} --productSet {10}{11}".format(CLUSTER_ID,
                SKIP_OS_INSTALL, SKIP_PATCH_INSTALL, SKIP_LITP, LITP_DROP,
                LITP_ISO, SKIP_ENM, SET_SED, XML_FILE,
                CI_VERSION, PRODUCT_SET, os_version_flag)

    if ENM_DROP != "":
        cmd + " --drop {0}::{1}".format(ENM_DROP, ENM_ISO)
    if OS_PATCH_VER != "":
        cmd + " --osPatchVersion {0}".format(OS_PATCH_VER)
    if OS_RH7_PATCH_VER != "":
        cmd + " --osRhel7PatchVersion={0}".format(OS_RH7_PATCH_VER)

    install_msg = "INSTALLATION OF THE FOLLOWING WILL BEGIN"
    if SKIP_CLEAN != "YES":
        install_msg += " AFTER THE SYSTEM IS CLEANED:"
    else:
        cmd += " --skipTearDown YES"

    install_info = ""

    if SKIP_OS_INSTALL == "NO":
        install_info += "\nRed Hat OS {0}".format(OS_VERSION)
    if SKIP_PATCH_INSTALL == "NO":
        install_info += "\nOS Patches {0}".format(
                OS_PATCH_VER)
    if SKIP_LITP == "NO":
        install_info += "\nLITP {0}".format(LITP_ISO)
    if SKIP_ENM == "NO":
        install_info += "\nENM {0}".format(ENM_ISO)

    info = install_msg + install_info

    print STAR_COMMENT.format(STARS, info)

    print cmd
    subprocess.check_call(cmd, shell=True)

    info = "SUCCESSFULLY COMPLETED INSTALLATION OF: {0}".format(install_info)
    print STAR_COMMENT.format(STARS, info)

get_values_from_file(sys.argv[1])
run_install()