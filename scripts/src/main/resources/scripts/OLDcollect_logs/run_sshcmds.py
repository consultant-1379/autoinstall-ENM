"""
Test
"""

import paramiko
import time
import socket
import StringIO
#import os
#import test_constants
#import string
import subprocess
import pexpect

class NodeConnect():
    """
    Test
    """

    def __init__(self, ipaddr="", username="", password=""):
        """
        """
        self.ipv4 = ipaddr
        self.username = username
        self.password = password
        self.ipv6 = None
        self.hostname = None
        self.host = None
        self.port = 22
        self.ssh = None
        # timeout for establishing ssh connection
        self.timeout = 10
        self.retry = 0
        # stdout and stderr buffer size, modify if necessary
        self.out_bufsize = 4096
        self.err_bufsize = 4096
        # 60 seconds timeout for I/O channel operations
        self.session_timeout = 60
        # Timeout to wait for output after execution of a cmd
        self.execute_timeout = 0.25
        
    def __connect(self, username=None, password=None):
        """Connect to a node using paramiko.SSHCLient

        Args:
           username  (str): username to override
           password  (str): password to override
           ipv4     (bool): switch between ipv4 and ipv6

        Returns:
           bool

        Raises:
           BadHostKeyException, AuthenticationException, SSHException,
           socket.error
        """
        self.retry += 1

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.host = self.ipv4
        username = self.username
        password = self.password
        try:
            ssh.connect(self.host,
                        port=self.port,
                        username=username,
                        password=password,
                        timeout=self.timeout)
            self.ssh = ssh
            self.retry = 0
            return True
        except paramiko.BadHostKeyException, except_err:
            self.__disconnect()
            raise
        except paramiko.AuthenticationException, except_err:
            self.__disconnect()
            raise
        except paramiko.SSHException or socket.error, except_err:
            if (self.retry < 2):
                time.sleep(5)
                self.__disconnect()
                return self.__connect(username, password)
            else:
                self.__disconnect()
                raise
        except Exception as except_err:
            print "Error connecting to node on {0}: {1}".\
                format(self.host, str(except_err))

            raise

    def __disconnect(self):
        """Close the paramiko.SSHClient
        """
        if self.ssh:
            try:
                self.ssh.close()
                self.ssh = None
            except Exception as except_err:
                print "Error disconnecting: {1}".\
                    format(str(except_err))
                self.ssh = None
        else:
            self.ssh = None

    def run_command(self, cmd, username=None, password=None, logs=True):
        """Run command on node
           stdout, stderr, rc (list, list, integer)
        """

        if logs:
            print "[{0}@{1}]# {2}".format(self.username,
                                              self.ipv4, cmd)

        stdout, stderr, exit_code = self.execute(
            cmd, username, password, logs=logs)

        return stdout, stderr, exit_code

    def execute(self, cmd, username=None, password=None, logs=True):
        """
        Test
        """
        username = self.username
        password = self.password
        if not self.ssh:
            self.__connect(username, password)
        if self.ssh:
            channel = self.ssh.get_transport().open_session()
            channel.settimeout(self.session_timeout)
            try:
                channel.exec_command(cmd)

                contents = StringIO.StringIO()
                errors = StringIO.StringIO()

                timed_out = False

                returnc = channel.recv_exit_status()

                while (True):

                    if channel.recv_ready():
                        data = channel.recv(self.out_bufsize)
                        while data:
                            contents.write(data)
                            data = channel.recv(self.out_bufsize)

                        break
                    if channel.recv_stderr_ready():
                        error = channel.recv_stderr(self.err_bufsize)
                        while error:
                            errors.write(error)
                            error = channel.recv_stderr(self.err_bufsize)

                        break

                    # After timeout we do one more loop to check
                    # if output buffers are ready and then we exit
                    if timed_out:
                        break

                    if not timed_out:
                        time.sleep(self.execute_timeout)
                        timed_out = True

            except socket.timeout, except_err:
                print 'Socket timeout error: {0}'.format(except_err)
                raise
            finally:
                if channel:
                    channel.close()

            if logs:
                print contents.getvalue()
                print errors.getvalue()
                print returnc

            out = self.__process_results(contents.getvalue())
            err = self.__process_results(errors.getvalue())

            self.__disconnect()

        return out, err, returnc

    def __process_results(self, result):
        """
        Test
        """
        processed = []
        for item in result.split('\n'):
            if item.strip():
                processed.append(item.strip())
        return processed

    def copy_file_to(self, local_filepath, remote_filepath):
        """
        Copy a file to the node using paramiko.SFTP
        """
        if not self.ssh:
            self.__connect()

        if self.ssh:

            try:
                sftp_session = self.ssh.open_sftp()
                sftp_session.put(local_filepath, remote_filepath)
            except IOError, except_err:
                raise
            finally:
                self.__disconnect()

    def copy_file_from(self, remote_filepath, local_filepath):
        """
        Copy a file to the node using paramiko.SFTP
        """
        if not self.ssh:
            self.__connect()

        if self.ssh:

            try:
                sftp_session = self.ssh.open_sftp()
                sftp_session.get(remote_filepath, local_filepath)
            except IOError, except_err:
                raise
            finally:
                self.__disconnect()
