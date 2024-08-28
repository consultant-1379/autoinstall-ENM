"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     January 2016
@author:    Laura Forbes

Script to get parameters required to run an E-CDB installation or upgrade.
Parameters are written to job_params.txt.
Appends Jenkins Build Description to envVariables file.
Run this script with the path to envVariables as an argument.
"""

import sys
import os
import subprocess
import time
import json

# Disable output buffering to receive the output instantly
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

MS_IP = ""
RUN_TYPE = ""
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
BUILD_NUM = ""
CI_VERSION = "latest"
PRODUCT_SET = ""
ARTIFACT_URL = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/"
ARTIFACT_ENM = "ERICenm_CXP9027091"


def print_star_comment(comment):
    """
    Prints the given comment with a line of 100 stars above and below it.
    """
    stars = "*" * 100
    print "{0}\n{1}\n{0}".format(stars, comment)


def get_green_product_set(drop):
    """
    Gets the latest GREEN product set for the drop specified

    :param str drop: The specified drop e.g. '20.08'
    :return: The latest GREEN product set version e.g. '20.08.110'
    :rtype: str
    """
    cmd_get_prod_set = 'wget -q -O - --no-check-certificate "' \
                       + ARTIFACT_URL + \
                       'getLastGoodProductSetVersion/' \
                       '?drop={0}&' \
                       'productSet=ENM"'.format(drop.split(':')[0])

    wget_process = subprocess.Popen(cmd_get_prod_set,
                                    stdout=subprocess.PIPE, shell=True)
    enm_prod_set = wget_process.communicate()[0]
    return enm_prod_set


def get_artifact_version_from_product_set(product_set, artifact):
    """
    Gets an artifact's version from the product set specified

    :param str product_set: The specified product set e.g. '20.08.107'
    :param str artifact: The artifact to search for e.g. 'ERICenm_CXP9027091'
    :return: The artifact version in the product set e.g. '1.92.106'
    :rtype: str
    """
    if "::" not in product_set or "GREEN" in product_set \
            or "LATEST" in product_set:
        enm_prod_set = get_green_product_set(product_set)
    else:
        enm_prod_set = product_set.split("::")[1]

    cmd_get_set_contents = 'wget -q -O - --no-check-certificate "' \
                           + ARTIFACT_URL + \
                           'getProductSetVersionContents/' \
                           '?productSet=ENM&version={0}"' \
                                .format(enm_prod_set)

    wget_process = subprocess.Popen(cmd_get_set_contents,
                                   stdout=subprocess.PIPE, shell=True)
    contents = wget_process.communicate()[0]
    product_set_contents = json.loads(contents)

    artifact_version = ""
    for item in product_set_contents[0]["contents"]:
        if item["artifactName"] == artifact:
            try:
                artifact_version = item["version"]
                break
            except KeyError:
                print "Warning: Version information not found for artifact"
                break
    else:
        print "Warning: Artifact not found"

    return artifact_version


def get_latest_iso(drop, product):
    """
    Gets the latest ISO of the product specified
    (LITP or ENM) in the given Drop.

    :param str drop: The specified drop e.g. '20.08'
    :param str product: The product to search for e.g. 'LITP'
    :return: The latest ISO version in the drop e.g. '2.114.3'
    :rtype: str
    """
    if "::" not in drop or "GREEN" in drop \
            or "LATEST" in drop:

        if product == "LITP":
            cmd = 'wget -q -O - --no-check-certificate "' \
                  + ARTIFACT_URL + 'getlatestisover/?drop' \
                  '={0}&product=LITP"'.format(drop.split(":")[0])
            wget_litp_process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                                 shell=True)
            iso_ver = wget_litp_process.communicate()[0]

        elif product == "ENM":
            iso_ver = get_artifact_version_from_product_set(
                drop, "ERICenm_CXP9027091")

        return iso_ver
    else:
        return drop.split("::")[1]


def get_values_from_file(path_to_envvariables):
    """
    Get values from Jenkins passed into envVariables.
    """
    global MS_IP, RUN_TYPE, CLUSTER_ID, SET_SED, XML_FILE
    global LITP_DROP, LITP_ISO, ENM_DROP, ENM_ISO, OS_PATCH_VER
    global SKIP_CLEAN, SKIP_OS_INSTALL, SKIP_LITP, SKIP_ENM, BUILD_NUM
    global CI_VERSION, OS_RH7_PATCH_VER, PRODUCT_SET, OS_VERSION

    with open(path_to_envvariables, 'r') as infile:
        for line in infile:
            if 'msip' in line:
                MS_IP = line.split("=")[1].rstrip()
            elif 'RunType' in line:
                RUN_TYPE = line.split("=")[1].rstrip()
            elif 'clusterId' in line:
                CLUSTER_ID = line.split("=")[1].rstrip()
            elif 'setSED' in line:
                SET_SED = line.split("=")[1].rstrip()
            elif 'xmlFile' in line:
                XML_FILE = line.split("=")[1].rstrip()
            elif 'LITPDrop' in line:
                LITP_DROP = line.split("=")[1].rstrip()
                LITP_ISO = get_latest_iso(LITP_DROP, "LITP")
            elif 'ENMDrop' in line:
                ENM_DROP = line.split("=")[1].rstrip()
                if ENM_DROP != "":
                    ENM_ISO = get_latest_iso(ENM_DROP, "ENM")
            elif 'OSPatchVer' in line:
                OS_PATCH_VER = line.split("=")[1].rstrip()
            elif 'ENMPatchVer' in line:
                OS_RH7_PATCH_VER = line.split("=")[1].rstrip()
            elif 'skipTearDown' in line:
                SKIP_CLEAN = line.split("=")[1].rstrip()
            elif 'skipOsInstall' in line:
                SKIP_OS_INSTALL = line.split("=")[1].rstrip()
            elif 'skipLitp' in line:
                SKIP_LITP = line.split("=")[1].rstrip()
            elif 'skipEnm' in line:
                SKIP_ENM = line.split("=")[1].rstrip()
            elif 'buildNum' in line:
                BUILD_NUM = line.split("=")[1].rstrip()
            elif 'cifwk' in line:
                CI_VERSION = line.split("=")[1].rstrip()
            elif 'productSet' in line:
                PRODUCT_SET = line.split("=")[1].rstrip()
            elif 'OSversion' in line:
                OS_VERSION = line.split("=")[1].rstrip()

def create_build_desc(desc_file):
    """
    Creates a Jenkins Build Description and appends it to given file.
    """
    global LITP_DROP, ENM_DROP, SKIP_ENM, SKIP_PATCH_INSTALL

    # For installs, if LITP is not being installed, then ENM can't be installed
    # if RUN_TYPE == "Install" and SKIP_LITP == "YES":
    #    SKIP_ENM = "YES"

    if "::" in LITP_DROP:
        LITP_DROP = LITP_DROP.split("::")[0].rstrip()
    if "::" in ENM_DROP:
        ENM_DROP = ENM_DROP.split("::")[0].rstrip()

    # For installs, if RHEL OS is not being reinstalled, do not apply patches
    if RUN_TYPE == "Install":
        if SKIP_OS_INSTALL == "YES":
            SKIP_PATCH_INSTALL = "YES"
    else:
        # If a patch version is not specified for
        # an upgrade, then don't upgrade patches
        skip_rhel6_patches = False
        skip_rhel7_patches = False
        if OS_PATCH_VER == "":
            skip_rhel6_patches = True
        if OS_RH7_PATCH_VER == "":
            skip_rhel7_patches = True

        if skip_rhel7_patches and skip_rhel6_patches:
            SKIP_PATCH_INSTALL = "YES"
        if skip_rhel7_patches and not skip_rhel6_patches:
            SKIP_PATCH_INSTALL = "RHEL7"
        if skip_rhel6_patches and not skip_rhel7_patches:
            SKIP_PATCH_INSTALL = "RHEL6"
        if not skip_rhel7_patches and not skip_rhel6_patches:
            SKIP_PATCH_INSTALL = "NO"

    build_descr = "buildDesc={0}".format(RUN_TYPE)
    if SKIP_LITP != "YES":
        build_descr += " LITP {0}::{1}".format(LITP_DROP, LITP_ISO)
    if SKIP_ENM != "YES":
        enm_ver=""
        ps_drop = ENM_DROP
        if ps_drop == "":
            ps_drop = PRODUCT_SET.split("::")[0].rstrip()
            enm_ver = get_artifact_version_from_product_set(
                PRODUCT_SET, ARTIFACT_ENM)

        build_descr += " - ENM {0}::{1}".format(ps_drop, enm_ver)
    if SKIP_PATCH_INSTALL != "YES":
        if OS_PATCH_VER == "":
            patch_ver = get_artifact_version_from_product_set(
                PRODUCT_SET, "RHEL_OS_Patch_Set_CXP9034997")
        else:
            patch_ver = OS_PATCH_VER

        build_descr += " - Patches {0}".format(patch_ver)

    with open(desc_file, "a") as build_desc_file:
        build_desc_file.write(build_descr + "\n")

        # For Healthchecks:
        build_desc_file.write("litp_iso_version={0} {1} #{2}\n".format(
                LITP_ISO, RUN_TYPE, BUILD_NUM))

        # For Short Loop Tests:
        build_desc_file.write("iso={0}\n".format(ENM_ISO))

        # For Updating Confidence Level in CI Portal:
        build_desc_file.write("LITP_ISO={0}\n".format(LITP_ISO))


def create_params_file(file_name):
    """
    Creates a file with the specified name containing the parameters required
    to run the ecdb_autoinstall.py and ecdb_autoupgrade.py scripts.
    """
    with open(file_name, "w") as param_file:
        param_file.write("msip={0}\n".format(MS_IP))
        param_file.write("clusterId={0}\n".format(CLUSTER_ID))
        param_file.write("setSED={0}\n".format(SET_SED))
        param_file.write("xmlFile={0}\n".format(XML_FILE))
        param_file.write("skipOsPatch={0}\n".format(SKIP_PATCH_INSTALL))
        param_file.write("skipLitp={0}\n".format(SKIP_LITP))
        param_file.write("LITPDrop={0}\n".format(LITP_DROP))
        param_file.write("LITPIso={0}\n".format(LITP_ISO))
        param_file.write("skipEnm={0}\n".format(SKIP_ENM))
        param_file.write("ENMDrop={0}\n".format(ENM_DROP))
        param_file.write("ENMIso={0}\n".format(ENM_ISO))
        param_file.write("OSPatchVer={0}\n".format(OS_PATCH_VER))
        param_file.write("RHEL7PatchVer={0}\n".format(OS_RH7_PATCH_VER))
        param_file.write("cifwk={0}\n".format(CI_VERSION))
        param_file.write("productSet={0}\n".format(PRODUCT_SET))
        param_file.write("OSversion={0}\n".format(OS_VERSION))

        if RUN_TYPE == "Install":
            param_file.write("skipTearDown={0}\n".format(SKIP_CLEAN))
            param_file.write("skipOsInstall={0}\n".format(SKIP_OS_INSTALL))


def ensure_litp_iso_downloadable():
    """
    Due to CIS-69171, any new LITP ISO needs to be
    copied to arm901 before E-CDB begins.
    This method attempts to trigger the copy of the ISO from arm101 to
    arm901 if it is not already present on arm901, and asserts that
    the ISO can be downloaded from arm901.
    """
    info = "CHECKING IF LITP ISO {0} CAN BE " \
           "DOWNLOADED FROM ARM-901 TO GATEWAY".format(LITP_ISO)
    print_star_comment(info)

    if '0.79::' in LITP_DROP:
        url_snippet = "litp/iso_test/rhel7_7"
    # Else if using Black ISOs contained in Drop 0.0, use different URL
    elif '0.0::' in LITP_DROP:
        url_snippet = "litp/iso_test"
    else:
        url_snippet = "nms/litp"

    arm901_litp = "https://arm901-eiffel004.athtem.eei.ericsson.se:" \
                  "8443/nexus/content/repositories/litp_releases/com/" \
                  "ericsson/{0}/ERIClitp_CXP9024296/" \
                  "{1}/ERIClitp_CXP9024296-{1}.iso".format(url_snippet,
                                                          LITP_ISO)

    # Download ISO to /tmp/ on gateway
    # Try 6 times with 10 minutes between each try
    download_litp = "wget -q {0} -P /tmp/".format(arm901_litp)

    success = False
    tries = 0
    while not success:
        print download_litp
        rc = subprocess.call(download_litp, shell=True)
        tries += 1

        if 0 == rc:
            success = True
        else:
            print "\nUNABLE TO DOWNLOAD LITP ISO {0}".format(LITP_ISO)
            if tries < 6:
                comment = "SLEEPING 10 MINUTES BEFORE TRYING AGAIN"
                print_star_comment(comment)
                time.sleep(600)
            else:
                comment = "{0}\n{1}\n{0}".format(
                    "*" * 100, "WILL NOT ATTEMPT ANY MORE RETRIES. EXITING.")
                sys.exit(comment)

    comment = "ISO {0} SUCCESSFULLY DOWNLOADED. " \
              "REMOVING ISO FROM /tmp".format(LITP_ISO)
    print_star_comment(comment)
    rm_iso = "rm -f /tmp/ERIClitp_CXP9024296-{0}.iso*".format(LITP_ISO)
    print rm_iso
    subprocess.Popen(rm_iso, stdout=subprocess.PIPE, shell=True)


get_values_from_file(sys.argv[1])
ensure_litp_iso_downloadable()
create_build_desc("envVariables")
create_params_file("job_params.txt")