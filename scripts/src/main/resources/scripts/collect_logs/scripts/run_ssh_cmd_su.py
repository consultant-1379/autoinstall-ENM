"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes

Modified from http://blog.timmattison.com/archives/2014/02/13/
    how-to-execute-a-command-on-a-remote-server-that-requires-you-to-su-or-sudo

Run this script with the following arguments:
python run_ssh_cmd_su.py SSH_IP USER USER_PASSWORD SU_PASSWORD COMMAND_TO_RUN
"""

import paramiko
import time


class RunSUCommands:
    """
    Run commands on a remote system as root user.
    """

    def __init__(self, system_ip, system_username,
                 system_ssh_password, system_su_password, cmd):
        """
        Set up variables.
        """
        self.system_ip = system_ip
        self.system_username = system_username
        self.system_ssh_password = system_ssh_password
        self.system_su_password = system_su_password
        self.cmd = cmd
        self.shell = None

    def cmd_wait_time(self, command, wait_time, should_print):
        """
        Run a command and wait the given time.
        """
        # Send the command
        self.shell.send(command)

        # Wait for the time specified
        time.sleep(wait_time)

        # Flush the receive buffer
        receive_buffer = self.shell.recv(1024)

        # Print the receive buffer, if necessary
        if should_print:
            print receive_buffer

    def cmd_wait_end(self, command, wait_string, should_print):
        """
        Execute a command or set of commands and
            wait for the given string to be printed.
        """
        # Send the command
        self.shell.send(command)

        # Create a new receive buffer
        receive_buffer = ""

        while wait_string not in receive_buffer:
            # Flush the receive buffer
            receive_buffer += self.shell.recv(1024)

        # Print the receive buffer, if necessary
        if should_print:
            print receive_buffer

    def run_cmds(self):
        """
        Blah
        """
        # Create an SSH client
        client = paramiko.SSHClient()

        # Make sure that we add the remote server's SSH key automatically
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the client
        client.connect(self.system_ip, username=self.system_username,
                       password=self.system_ssh_password)

        # Create a raw shell
        self.shell = client.invoke_shell()

        # Send the command
        self.cmd_wait_time("{0}\n".format(self.cmd), 1, True)

        # Close the SSH connection
        client.close()

    def run_su_cmds(self):
        """
        Blah
        """
        try:
            # Create an SSH client
            client = paramiko.SSHClient()

            # Make sure that we add the remote server's SSH key automatically
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the client
            client.connect(self.system_ip, username=self.system_username,
                           password=self.system_ssh_password)

            # Create a raw shell
            self.shell = client.invoke_shell()

            # Send the su command
            self.cmd_wait_time("su\n", 1, True)

            # Send the client's su password followed by a newline
            self.cmd_wait_time(self.system_su_password + "\n", 1, True)

            root_cmd = "{0}\necho 'End of command(s)'\n".format(self.cmd)
            root_cmd_result = "End of command(s)"

            # Send command followed by a newline and wait for the completion string
            self.cmd_wait_end(root_cmd, root_cmd_result, True)

            # Close the SSH connection
            client.close()
        except Exception as except_err:
            print "Connection error: {0}"\
                .format(except_err)
            client.close()
