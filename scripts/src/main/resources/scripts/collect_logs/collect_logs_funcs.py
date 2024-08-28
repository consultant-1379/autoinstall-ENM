"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2016
@author:    Laura Forbes
"""
import os
import shutil
import errno
import pexpect


class CollectLogsFuncs:

    @staticmethod
    def mkdir_parent(path):
        """
        Takes path of directory to create.
        Creates any parent directories, if needed.
        """
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    @staticmethod
    def copy_file(source, dest):
        """
        Blah
        """
        try:
            shutil.copy(source, dest)
        except:
            print "File {0} does not exist.".format(source)

    @staticmethod
    def copy_dir(source, dest):
        """
        Blah
        """
        try:
            shutil.copytree(source, dest)
        except:
            print "Directory {0} does not exist.".format(source)

    @staticmethod
    def expect_cmd(command, password, timeout=30, retries=3):
        """
        Bluh
        """
        print command
        child = pexpect.spawn(command, timeout=timeout)
        index = child.expect(["password:", "Are you sure you want to continue connecting", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            print "Prompted for password... responding with {0}".format(password)
            child.sendline(password)
            child.wait()
            child.expect([pexpect.EOF, pexpect.TIMEOUT])
            # Print the output
            print child.before
        elif index == 1:
            print "Host verification confirmation ... responding 'yes'"
            child.sendline("yes")
            child.expect(["password:", pexpect.EOF, pexpect.TIMEOUT])
            child.sendline(password)
            child.wait()
            child.expect([pexpect.EOF, pexpect.TIMEOUT])
            # Print the output
            print child.before
        elif index == 2:
            print "Command executed."
        elif index == 3:
            print "Timed out waiting for password or host key verification."
            if retries > 0:
                new_retries = retries-1
                new_timeout = timeout+30
                print "Reattempting with {0} second timeout".format(new_timeout)
                return CollectLogsFuncs.expect_cmd(command, password, timeout=new_timeout, retries=new_retries)
            else:
                raise Exception("Failed to establish ssh connection. Unable to execute command {0}".format(command))
        else:
            raise Exception("Unexpected response during execution of {0}, could not handle: {1}".format(command, child.before))
        return True

    @staticmethod
    def copy_file_bash(source, dest, directory=False):
        """
        NOT USED
        """
        # If a directory is to be copied, use recursive
        if directory:
            return "cp {0} {1} -r".format(source, dest)

        return "cp {0} {1}".format(source, dest)
