"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@author: Monika Penkova, Zaheen Sherwani
@date: August 2018, November 2019
@summary: Check CI portal if the version of the RHEL OS Patches is the same as
          the version that is defined in the ECDB scripts.
          The patch_version.txt file needs to be in the same directory as this
          script when running it.
"""

import urllib2
from HTMLParser import HTMLParser

CIPORTAL = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/RHEL-OS-Patch-Set-ISO"


class HTMLTableParser(HTMLParser):
    """
    Class to parse HTML tables
    """
    def __init__(self, name, value, tag):
        HTMLParser.__init__(self)
        self.recording = 0
        self.data = []
        self.name = name
        self.value = value
        self.tag = tag

    def handle_starttag(self, tag, attrs):
        if tag != self.tag:
            return
        if self.recording:
            self.recording += 1
            return
        for name, value in attrs:
            if name == self.name and value == self.value:
                break
        else:
            return
        self.recording = 1

    def handle_endtag(self, tag):
        if tag == self.tag and self.recording:
            self.recording -= 1

    def handle_data(self, data):
        if self.recording:
            self.data.append(data)

    @staticmethod
    def nextItem(item, lst):
        """
        Access the next item on a list
        """
        ind = lst.index(item)
        if ind < (len(lst) - 1):
            return lst[ind + 1]

    def get_latest_patch_ver(self, lst):
        """
        Extract the latest delivered version of the OS Patches
        """
        ind_lst = []
        nlst = []
        for ind, item in enumerate(lst):
            # Using the string 'RHEL_OS_Patch_Set_CXP9034997' as a way
            # to identify each occurance as a new entry
            if "RHEL" in item:
                ind_lst.append(ind)
        # Loop used to split given list into sublists of each occurance
        for item in ind_lst:
            next_occurance = self.nextItem(item, ind_lst)
            nlst.append(lst[item:next_occurance])
        for sub_lst in nlst:
            if sub_lst == []:
                return
            # The last column in the table is 'Obsoleted From'
            # if there is an entry for this,
            # it means that this version has been obsolete
            # and it shouldn't be used.
            # If there is no entry for this column, it will extract
            # the entry from the second column of the table('Version')
            if "ENM" not in sub_lst[-2] and "ENM" in sub_lst[6]:
                return sub_lst[1]


if __name__ == "__main__":
    # Extract the OS Patch version that's currently used
    FLINE = ((open("patch_versions.txt").readline()).rstrip()).split("=")

    DROP, CURRENTVER = FLINE[1].split("::")

    print "Current version used is {0} in drop {1}".format(CURRENTVER, DROP)

    def get_drop():
        """
        Method to get the all drops from table
        """
        # Get the latest drop in the CI Portal
        patches_releases_html = (urllib2.urlopen("{0}/releases/".format(CIPORTAL))).read()

        parser = HTMLTableParser('class', 'RHEL-OS-Patch-Set-ISO_drop', 'a')
        parser.feed(patches_releases_html)
        parser.close()
        return parser.data

    def get_ver():
        """
        Method to get the delivered version of patches
        """
        # Get the version of the OS Patches that was delivered to an ENM drop
        drop_html = (urllib2.urlopen("{0}/{1}/media/"\
                                   .format(CIPORTAL, LATESTDROP))).read()

        parser = HTMLTableParser('class', 'general-table', 'table')
        parser.feed(drop_html)
        parser.close()
        patches_version \
            = HTMLTableParser.get_latest_patch_ver(parser, parser.data)
        return patches_version

    DROPS_LST = get_drop()
    LATESTDROP = DROPS_LST[0]
    LATESTVER = get_ver()

    # If there was no patches delivered in the drop, check next one
    while LATESTVER == None:
        LATESTDROP = DROPS_LST[0]
        DROPS_LST = DROPS_LST[1:]
        LATESTVER = get_ver()

    if LATESTVER == CURRENTVER:
        print "The latest delivered version in the CI Portal is used"
    else:
        FOPEN = open("vars.txt", "w")
        FOPEN.write("latestVersion={0}\n".format(LATESTVER))
        FOPEN.write("latestDrop={0}\n".format(LATESTDROP))
        FOPEN.write("failed=yes\n")
        FOPEN.close()
        print ("There are new OS Patches.\n"
               "Please update scripts with version {0} in drop {1}") \
                   .format(LATESTVER, LATESTDROP)
