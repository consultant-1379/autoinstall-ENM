"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     December 2015
@author:    Laura Forbes

Takes a file containing the required upgrade arguments and runs an E-CDB upgrade.
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
PRODUCT_SET = ""
OS_PATCH_VER = ""
OS_RH7_PATCH_VER = ""
LITP_DROP = ""
ENM_DROP = ""
SKIP_LITP = "NO"
SKIP_ENM = "NO"
LITP_ISO = ""
ENM_ISO = ""
PREV_LITP_ISO = "N/A"
PREV_ENM_ISO = "N/A"
PREV_OS_PATCHES = "N/A"
PREV_OS_RH7_PATCHES = "N/A"
SKIP_OS_PATCHES = False
SSH_ROOT_MS = ""
CI_VERSION = "latest"

STARS = "*" * 100
STAR_COMMENT = "{0}\n{1}\n{0}"

# To do: Upgrade LITP only
# To do: Do something when node unlocking fails...?


def get_prev_isos():
    """
    Get LITP, ENM and RHEL patch ISO versions from
    /software/autoDeploy/ for informational purposes.
    """
    global PREV_LITP_ISO, PREV_ENM_ISO, PREV_OS_PATCHES, PREV_OS_RH7_PATCHES

    # Get LITP and ENM ISO versions from /software/autoDeploy/ for info
    cmd = "{0} ls /software/autoDeploy/ -lt".format(SSH_ROOT_MS)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    audo_deploy_dir = process.communicate()[0]

    if "ERIClitp_CXP9024296-" in audo_deploy_dir:
        PREV_LITP_ISO = audo_deploy_dir.split(
            "ERIClitp_CXP9024296-")[1].split(".iso")[0]
    else:
        PREV_LITP_ISO = "N/A"
        print "NO LITP ISO FOUND IN /software/autoDeploy/"

    if "ERICenm_CXP9027091-" in audo_deploy_dir:
        PREV_ENM_ISO = audo_deploy_dir.split(
            "ERICenm_CXP9027091-")[1].split(".iso")[0]
    else:
        PREV_ENM_ISO = "N/A"
        print "NO ENM ISO FOUND IN /software/autoDeploy/"

    if "RHEL_OS_Patch_Set_CXP9034997-" in audo_deploy_dir:
        PREV_OS_PATCHES = audo_deploy_dir.split(
            "RHEL_OS_Patch_Set_CXP9034997-")[1].split(".iso")[0]
    else:
        PREV_OS_PATCHES = "N/A"
        print "NO RHEL6 OS PATCH ISO FOUND IN /software/autoDeploy/"
    if "RHEL7_OS_Patch_Set_CXP9035024-" in audo_deploy_dir:
        PREV_OS_RH7_PATCHES = audo_deploy_dir.split(
            "RHEL7_OS_Patch_Set_CXP9035024-")[1].split(".iso")[0]
    else:
        PREV_OS_RH7_PATCHES = "N/A"
        print "NO RHEL7 OS PATCH ISO FOUND IN /software/autoDeploy/"


def get_values_from_file(path_to_envvariables):
    """
    Get relevant values from passed file.
    """
    global MS_IP, SSH_ROOT_MS, SET_SED, XML_FILE, CLUSTER_ID, PRODUCT_SET
    global LITP_DROP, LITP_ISO, ENM_DROP, ENM_ISO, SKIP_LITP, SKIP_ENM
    global OS_PATCH_VER, SKIP_OS_PATCHES, CI_VERSION, OS_RH7_PATCH_VER

    with open(path_to_envvariables, 'r') as infile:
        for line in infile:
            if "msip" in line:
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
                SKIP_OS_PATCHES = line.split("=")[1].rstrip()
            elif 'OSPatchVer' in line:
                OS_PATCH_VER = line.split("=")[1].rstrip()
            elif 'RHEL7PatchVer' in line:
                OS_RH7_PATCH_VER = line.split("=")[1].rstrip()
            elif 'skipLitp' in line:
                SKIP_LITP = line.split("=")[1].rstrip()
            elif 'skipEnm' in line:
                SKIP_ENM = line.split("=")[1].rstrip()
            elif 'cifwk' in line:
                CI_VERSION = line.split("=")[1].rstrip()
            elif 'productSet' in line:
                PRODUCT_SET = line.split("=")[1].rstrip()


def pre_upgrade_steps():
    """
    Ensure LITP is not in Maintenance Mode.
    Remove any LITP/ENM/RHEL OS patch ISOs in /software/autoDeploy/
    to free up space as that directory is snapshotted during upgrades.
    Run command to remove snapshots.
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

    get_prev_isos()

    info = "REMOVING ANY LITP/ENM ISOS AND OS PATCH TAR " \
           "FILES FROM /software/autoDeploy/"
    print STAR_COMMENT.format(STARS, info)

    if SKIP_LITP == "NO":
        # Remove All LITP ISOs and MD5s from /software/autoDeploy/
        cmd = "{0} rm -f /software/autoDeploy/ERIClitp_CXP9024296-*".format(
                SSH_ROOT_MS)
        print cmd

        subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    if SKIP_ENM == "NO":
        # Remove All ENM ISOs and MD5s from /software/autoDeploy/
        cmd = "{0} rm -f /software/autoDeploy/ERICenm_CXP9027091-*".format(
                SSH_ROOT_MS)
        print cmd

        subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    if SKIP_OS_PATCHES == "NO" or SKIP_OS_PATCHES == "RHEL7":
        # Remove All OS Patch iso and MD5 files from /software/autoDeploy
        cmd = "{0} rm -f /software/autoDeploy/"\
                "RHEL_OS_Patch_Set_CXP9034997-*".format(SSH_ROOT_MS)
        print cmd

        subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    if SKIP_OS_PATCHES == "NO" or SKIP_OS_PATCHES == "RHEL6":
        cmd = "{0} rm -f /software/autoDeploy/"\
                "RHEL7_OS_Patch_Set_CXP9035024-*".format(SSH_ROOT_MS)
        print cmd

        subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    info = "REMOVING SNAPSHOTS"
    print STAR_COMMENT.format(STARS, info)

    cmd = "/proj/lciadm100/cifwk/{0}/bin/cicmd deployment " \
          "--clusterid {1} --environment physical --product ENM " \
          "--snapShot remove_snapshot".format(CI_VERSION, CLUSTER_ID)

    print cmd
    subprocess.check_call(cmd, shell=True)

    info = "SNAPSHOT REMOVAL COMPLETE"
    print STAR_COMMENT.format(STARS, info)


def run_upgrade():
    """
    Runs an upgrade with the LITP ISO, ENM ISO and/or OS Patches specified.
    """
    upgr_info = ""
    # Construct upgrade command
    cmd = "/proj/lciadm100/cifwk/{0}/bin/cicmd deployment " \
          "--clusterid {1} --environment physical --product ENM " \
          "--installType upgrade_install --setSED {2} " \
          "--xmlFile {3} --productSet {4}".format(CI_VERSION, CLUSTER_ID, SET_SED, 
                                                  XML_FILE, PRODUCT_SET)

    if SKIP_OS_PATCHES == "NO":
        cmd += " --skipPatchInstall NO"

        if OS_PATCH_VER != "":
            upgr_info += "\nFROM OS PATCHES {0} TO OS PATCHES {1}".format(
                PREV_OS_PATCHES, OS_PATCH_VER)
            cmd += " --osPatchVersion {0}".format(OS_PATCH_VER)
        if OS_RH7_PATCH_VER != "":
            upgr_info += "\nFROM OS RHEL 7 PATCHES {0} TO OS RHEL 7 PATCHES {1}".format(
                PREV_OS_RH7_PATCHES, OS_RH7_PATCH_VER)
            cmd += " --osRhel7PatchVersion={0}".format(OS_RH7_PATCH_VER)

    elif SKIP_OS_PATCHES == "RHEL6":
        cmd += " --skipPatchInstall RHEL6"

        if OS_RH7_PATCH_VER != "":
            upgr_info += "\nFROM OS RHEL 7 PATCHES {0} TO OS RHEL 7 PATCHES {1} ".format(
                PREV_OS_RH7_PATCHES, OS_RH7_PATCH_VER)
            cmd += " --osRhel7PatchVersion={0}".format(OS_RH7_PATCH_VER)

    elif SKIP_OS_PATCHES == "RHEL7":
        cmd += " --skipPatchInstall RHEL7"

        if OS_PATCH_VER != "":
            upgr_info += "\nFROM OS PATCHES {0} TO OS PATCHES {1}".format(
                PREV_OS_PATCHES, OS_PATCH_VER)
            cmd += " --osPatchVersion {0}".format(OS_PATCH_VER)

    else:  # YES case
        cmd += " --skipPatchInstall YES"

    if SKIP_LITP == "NO":
        upgr_info += "\nFROM LITP {0} TO LITP {1}".format(
                PREV_LITP_ISO, LITP_ISO)
        cmd += " --litpDrop {0}::{1}".format(LITP_DROP, LITP_ISO)
    else:
        cmd += " --skipLitpInstall YES"

    if SKIP_ENM == "NO":
        # NOT UPGRADING ENM DOES NOT WORK --> NEED TO IMPLEMENT
        if ENM_DROP != "":
            upgr_info += "\nFROM ENM {0} TO ENM {1}".format(PREV_ENM_ISO, ENM_ISO)
            cmd += " --drop {0}::{1}".format(ENM_DROP, ENM_ISO)
        else:
            upgr_info += "\nFROM ENM {0} TO LATEST IN PRODUCT SET {1}".format(
                PREV_ENM_ISO, PRODUCT_SET)
    else:
        # NEED TO IMPLEMENT UPGRADING LITP ONLY
        # ADDING BELOW WILL ONLY DOWNLOAD LITP ISO
        cmd += " --skipEnmInstall YES"

    info = "STARTING UPGRADE" + upgr_info

    print STAR_COMMENT.format(STARS, info)

    print cmd
    subprocess.check_call(cmd, shell=True)

    info = "UPGRADE OF THE FOLLOWING SUCCESSFULLY COMPLETED: {0}".format(
            upgr_info)
    print STAR_COMMENT.format(STARS, info)

get_values_from_file(sys.argv[1])
pre_upgrade_steps()
run_upgrade()

