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
import test_constants as const


class ECDBHealthcheck(GenericTest):
    """
    Performs a healthcheck on an E-CDB installation.
    """

    def setUp(self):
        """ Setup Variables for every test """

        super(ECDBHealthcheck, self).setUp()

        self.ms_node = self.get_management_node_filename()
        self.service_groups_check = list()
        self.vms_check = list()

    def tearDown(self):
        """ Teardown run after every test """

        super(ECDBHealthcheck, self).tearDown()

    def _active_standby_check(self, stdout, ha_type_index, group_index,
                              service_state_index, system_index):
        """
        Description:
            For each service group with a HAType value of "active-standby",
            ensure that one system has a ServiceState of "ONLINE" and the
            other has a ServiceState of "OFFLINE" for that group.

        Args:
            stdout (list): Output from running command to get information
                    on the service groups of the HA nodes in the deployment.
            ha_type_index (int): Index of HAType heading in output.
            group_index (int): Index of Group heading in output.
            service_state_index (int): Index of ServiceState heading in output.
            system_index (int): Index of System heading in output.

        Actions:
            a. Append all of the group names with HAType
                    "active-standby" as a key to a dictionary.
            b. Add ServiceState of service to dictionary as a value.
            c. Assert that "ONLINE" and "OFFLINE" are present
                    as values in all entries of the dictionary.
        """
        active_standby = dict()
        for entry in stdout:
            entry = entry.split()
            # a. Append all of the group names with HAType
            #       "active-standby" as a key to a dictionary.
            if entry[ha_type_index] == 'active-standby':
                active_standby[entry[group_index]] = []

        for entry in stdout:
            entry = entry.split()
            group_name = entry[group_index]
            # b. Add ServiceState of service to dictionary as a value.
            if group_name in active_standby:
                if entry[service_state_index] == "ONLINE":
                    active_standby[group_name].append("ONLINE")
                elif entry[service_state_index] == "OFFLINE":
                    active_standby[group_name].append("OFFLINE")
                else:
                    active_standby[group_name].append("FAULTED")

                self.assertFalse("FAULTED" in active_standby[group_name],
                    "Service Group {0} on system {1} is neither ONLINE or "
                        "OFFLINE.".format(group_name, entry[system_index]))

        # c. Assert that "ONLINE" and "OFFLINE" are
        #       present as values in all entries of the dictionary
        for entry in active_standby:
            systems = []
            # Get system names for error messages
            for line in stdout:
                line = line.split()
                if entry in line:
                    systems.append(line[system_index])

            self.assertTrue("ONLINE" in active_standby[entry],
                            "{0} on both {1} and {2} is OFFLINE".format(
                                entry, systems[0], systems[1]))
            self.assertTrue("OFFLINE" in active_standby[entry],
                            "{0} on both {1} and {2} is ONLINE".format(
                                entry, systems[0], systems[1]))

    #attr('revert', 'ECDBHealthcheck', 'ECDBHealthcheck_tc01')
    def obsolete_01_p_check_service_groups(self):
        """
        Description:
            Perform a healthcheck on the service
                groups of the HA nodes in the deployment.

        Actions:
            1. Run command to get information on the
                service groups of the HA nodes in the deployment.
            2. Get the column headings from the info returned.
            3. For each line, add GroupState value in the line to a dictionary.
            4. For each GroupState in the dictionary, ensure it is set to 'OK'.
            5. For each service group with a HAType value of "active-standby",
                ensure that one system has a ServiceState of "ONLINE" and
                    the other has a ServiceState of "OFFLINE" for that group.
        """
        pass

    #attr('revert', 'ECDBHealthcheck', 'ECDBHealthcheck_tc02')
    def obsolete_02_p_install_enm_utils(self):
        """
        Description:
            Install TOR utilities internal package, which contains ENM Util
            binaries, ensuring there are no errors.
            Alternatively, a specific upgrade version may be passed to Jenkins.
        Actions:
            1. Set package details, retrieving TOR utilities production
                package version, that must be the same of internal package
                that is going to be installed.
            2. Download rpm from Nexus and create torutils flag
            3. Uninstall possible packages installed that may conflict.
            4. Install new TOR utils internal package.
            5. Check if update_enmutils_rpm_version String Parameter was set.
            6. Run command to install the latest ENM Utils rpm.
            7. Ensure there are no errors returned from running the command.
        """
        pass

    @attr('revert', 'ECDBHealthcheck', 'ECDBHealthcheck_tc03')
    def test_03_p_enm_healthcheck(self):
        """
        Description:
            Perform a healthcheck on all VMs in the deployment.

        Actions:
            1. Run command to get status of the deployment.
            2. Ensure the four checks passed.
            3. Ensure all service groups are in their correct state and
                the system is in a working state.
            4. Optionally remove packages that were installed in
                test_02_p_install_enm_utils to avoid package conflicts.
                Remove torutils flag.
        """
        # 1. Run command to get status of the deployment.
        cmd = '/opt/ericsson/enminst/bin/enm_healthcheck.sh -v'
        stdout, stderr, rcode = self.run_command(
            self.ms_node, cmd, su_root=True, su_timeout_secs=600,
            execute_timeout=1)
        self.assertNotEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, rcode)

        # 2. Ensure the four checks passed.
        self.assertTrue(self.is_text_in_list(
                'Node Status: PASSED', stdout))
        self.assertTrue(self.is_text_in_list(
                'Service Status: PASSED', stdout))
        self.assertTrue(self.is_text_in_list(
                'ENM VCS Cluster System Status: PASSED', stdout))
        self.assertTrue(self.is_text_in_list(
                'ENM VCS Service Group Status: PASSED', stdout))

        # 3. Ensure all service groups are in their correct
        #       state and the system is in a working state.
        cmd = "/opt/ericsson/enminst/bin/enm_healthcheck.sh --action " \
              "enminst_healthcheck system_service_healthcheck " \
              "vcs_cluster_healthcheck vcs_service_group_healthcheck"

        stdout, stderr, rcode = self.run_command(
            self.ms_node, cmd, su_root=True, su_timeout_secs=600,
            execute_timeout=1)
        self.assertNotEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, rcode)

        self.assertTrue(self.is_text_in_list(
                'Successfully Completed ENM System Healthcheck', stdout))
        self.assertTrue(self.is_text_in_list(
                'Successfully Completed Service Healthcheck', stdout))
        self.assertTrue(self.is_text_in_list(
                'Successfully Completed VCS Cluster', stdout))
        self.assertTrue(self.is_text_in_list(
            'Successfully Completed VCS Service Group Healthcheck', stdout))

    @attr('revert', 'ECDBHealthcheck', 'ECDBHealthcheck_tc04')
    def test_04_p_check_node_passwords(self):
        """
        Description:
            Verify that nodes use the correct password.

        Actions:
            1. Runs mco ping on MS to gather all nodes on system.
            2. Ssh onto each node in system to validate password.
        """
        # 1. Run command on node to verify node is accessible.
        ms_hostname, _, _ = self.run_command(self.ms_node,
                "hostname", default_asserts=True)
        cmd = "{0} ping".format(const.MCO_EXECUTABLE)
        ping_output, std_err, _ = self.run_command(self.ms_node,
                cmd, execute_timeout=5)
        self.assertEqual([], std_err,
                "There was an error {0}".format(std_err))
        self.log("info", "ping_output :{0}".format(ping_output))

        nodes = [node.split()[0] for node in ping_output
            if "time" in node and ms_hostname[0] not in node]

        self.log("info", "List of nodes: {0}".format(nodes))
        for node in nodes:
            self.log("info", "Current node is: {0}".format(node))
            std_out, std_err, rc = self.run_command_via_node(self.ms_node,
                node, "hostname")
            self.assertEqual([], std_err,
                "There was an error {0}".format(std_err))
            self.assertEqual(0, rc, "Return code is {0}".format(rc))
            self.log("info", "std_out: {0}. std_err: {1}. rc: {2}"
                .format(std_out, std_err, rc))
            self.assertTrue(std_out[3] == node,
                "Node {0} is not accessible.".format(node))
