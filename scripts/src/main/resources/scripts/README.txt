OBSOLETED TCS
==============

TEST: test_01_p_check_service_groups

TMS-ID: N/A

DESCRIPTION: Perform a healthcheck on the service
             groups of the HA nodes in the deployment.

REASON OBSOLETED: Covered by test case 3

GERRIT LINK: N/A
-----------------------------------------------------

TEST: test_02_p_install_enm_utils

TMS-ID: N/A

DESCRIPTION: Install TOR utilities internal package, which contains ENM Util
             binaries, ensuring there are no errors.
             Alternatively, a specific upgrade version may be passed to Jenkins.

REASON OBSOLETED: Test case was causing failures due to changes in the TOR utils.
                  The test case had negligible benefit in verifying ENM initial install.

GERRIT LINK: N/A
----------------------------------------------------
