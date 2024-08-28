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


class DevChecks(GenericTest):
    """
    Dev checks.
    """

    def setUp(self):
        """ Setup Variables for every test """

        super(DevChecks, self).setUp()

        self.ms_node = self.get_management_node_filename()

    def tearDown(self):
        """ Teardown run after every test """

        super(DevChecks, self).tearDown()

    @attr('pre-reg', 'dev', 'DevChecks')
    def test_01_p_dev_test(self):
        """
        Description:
            For running debug/dev checks for new tests.
        """
        print self.ms_node
        print environ

        if "SED_File" in environ:
            sed_file = environ['SED_File']
            self.log("info", "ENVIRONMENT")
        else:
            sed_file = "/var/tmp"
            self.log("info", "DEFAULT")

        self.log("info", "SED FILE:::::")
        self.log("info", sed_file)

        cmd = "ls {0}".format(sed_file)
        stdout, stderr, rc = self.run_command(self.ms_node, cmd, su_root=True)
        # 2. Ensure there are no errors returned from running the command
        self.assertNotEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, rc)
