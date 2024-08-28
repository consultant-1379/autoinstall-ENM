"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     August 2015
@author:    Laura Forbes
"""

from litp_generic_test import GenericTest, attr
from os import environ


class ECDBCleanSystem(GenericTest):
    """
    Cleans the E-CDB system to prepare for a new installation.
    Cleans up LITP, SAN LUNs, SFS, cobbler, puppet and yum repositories.
    """

    def setUp(self):
        """ Setup Variables for every test """

        super(ECDBCleanSystem, self).setUp()

        self.ms_node = self.get_management_node_filename()

    def tearDown(self):
        """ Teardown run after every test """

        super(ECDBCleanSystem, self).tearDown()

    @attr('pre-reg', 'revert', 'ECDBCleanSystem', 'ECDBCleanSystem_tc01')
    def test_01_p_clean_ecdb_system(self):
        """
        Description:
            Run a command to clean the E-CDB system.

        Usage:
            Set up the Jenkins job to take a String Parameter named
            SED_File that will take a value that is the path to
            the Site Engineering Document (SED) file to be used in
            the teardown command of the cleanup. If not set, the default value
            used is /var/tmp/MASTER_siteEngineering.txt

        Actions:
            1. Check if the SED_File String Parameter was set.
                a. If set, use the passed value for teardown script.
                b. If not set, use default value.
            2. Run command to clean the system on the MS.
            3. Ensure there are no errors returned from running the command.
        """
        # 1. Check if the SED_File String Parameter was set
        # 1a. If set, use the passed value for teardown script
        if "SED_File" in environ:
            sed_file_path = environ['SED_File']
        # 1b. If not set, use default value
        else:
            sed_file_path = "/var/tmp/MASTER_siteEngineering.txt"

        # 2. Run command to clean the system on the MS
        clean_cmd = "/opt/ericsson/enminst/bin/teardown.sh -y --sed " \
                    "{0} --command clean_all".format(sed_file_path)
        stdout, stderr, rc = self.run_command(
            self.ms_node, clean_cmd, su_root=True, su_timeout_secs=1800)
        # 3. Ensure there are no errors returned from running the command
        self.assertNotEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, rc)
