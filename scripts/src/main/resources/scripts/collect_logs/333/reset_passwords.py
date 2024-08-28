from genericpath import exists
from optparse import OptionParser
from os.path import expandvars
from subprocess import PIPE, STDOUT, Popen
from sys import argv
from time import sleep
from pexpect import spawn, EOF


class PasswordReset(object):
    LITP_ADMIN = 'litp-admin'
    ROOT = 'root'

    def get_user_prompt(self, user, hostname):
        if user == 'litp-admin':
            return '.*~]\$\s+$'.format(user, hostname)
        else:
            return '.*~]#\s+$'

    def reset_node_litpadmin_password(self, hostname, current_password,
                                      new_password):
        known_hosts = expandvars('${HOME}/.ssh/known_hosts')
        known_hosts_expect = True
        if exists(known_hosts):
            with open(known_hosts, 'r') as kh:
                for line in kh.readlines():
                    if line.startswith(hostname):
                        known_hosts_expect = False
                        break

        child = spawn('ssh {0}@{1}'.format(self.LITP_ADMIN, hostname))
        print('Initial login to {0} ...'.format(hostname))
        if known_hosts_expect is True:
            child.expect('Are you sure you want to '
                         'continue connecting (yes/no)?')
            print('Updating known hosts for {0} ...'.format(hostname))
            child.sendline('yes')

        child.expect('.*password:')
        print('Sending default password(1) ...')
        child.sendline(current_password.rstrip())

        print('Sending default password(2) ...')
        child.expect('\(current\) UNIX password:')
        child.sendline(current_password.rstrip())

        print('Setting new password ...')
        child.expect('New password:')
        child.sendline(new_password.rstrip())

        print('Confirming new password ...')
        child.expect('Retype new password:')
        child.sendline(new_password.rstrip())

        child.expect(EOF)
        child.close()

        print('Password reset for user {0} on '
              '{1} complete.'.format(self.LITP_ADMIN, hostname))

    def reset_node_root_password(self, hostname, litpadmin_passwd,
                                 current_rootpwd, new_rootpwd):
        child = spawn('ssh {0}@{1}'.format(self.LITP_ADMIN, hostname))
        prompt = self.get_user_prompt(self.LITP_ADMIN, hostname)
        print('Initial login ...')
        child.expect('.*password:')
        child.sendline(litpadmin_passwd.rstrip())
        child.expect(prompt)

        print('Setting {0}\'s password on {1}'.format(self.ROOT, hostname))

        child.sendline('su -')
        child.expect('Password:')
        child.sendline(current_rootpwd)

        print('Sending default password ...')
        child.expect('\(current\) UNIX password:')
        child.sendline(current_rootpwd.rstrip())

        print('Setting new password ...')
        child.expect('New password:')
        child.sendline(new_rootpwd.rstrip())

        print('Confirming new root password ...')
        child.expect('Retype new password:')
        child.sendline(new_rootpwd.rstrip())

        print('Password reset for user {0} on '
              '{1} complete.'.format(self.ROOT, hostname))

        child.expect(self.get_user_prompt(self.ROOT, hostname))

        child.close()

    def exec_process(self, command):
        process = Popen(command, stdout=PIPE, stderr=STDOUT)
        stdout = process.communicate()[0]
        if process.returncode != 0:
            raise IOError(process.returncode, stdout)
        return stdout

    def get_puppet_status(self):
        results = self.exec_process(['/usr/bin/mco', 'puppet', 'status'])
        results = results.split('\n')
        # remove any blank lines ..
        results = filter(None, results)
        agent_applying = -1
        agent_applied = -1
        agent_count = -1
        for index, line in enumerate(results):
            line = line.strip()
            if len(line) == 0:
                continue
            if 'Summary of Daemon Running:' in line:
                agent_count = results[index + 1].split("=")[1].strip()
            elif 'Summary of Applying:' in line:
                cindex = index + 1
                while True:
                    bits = results[cindex].split('=')
                    if 'true' == bits[0].strip():
                        agent_applying = bits[1].strip()
                    elif 'false' == bits[0].strip():
                        agent_applied = bits[1].strip()
                    cindex += 1
                    if results[cindex][0] != ' ':
                        break
        if agent_applied == agent_count:
            agent_applying = 0
        return {
            'agents': agent_count,
            'applying': agent_applying,
            'applied': agent_applied
        }

    def enable_root_ssh(self, value):
        if value == 'yes':
            print('Enabling root ssh access to all nodes')
            _from = 'no'
            _to = 'yes'
        else:
            print('Disabling root ssh access to all nodes')
            _from = 'yes'
            _to = 'no'
        
        # Need to do this on puppet....
        ppfile = '/opt/ericsson/nms/litp/etc/puppet' \
                 '/modules/litp/manifests/mn_node.pp'
        self.exec_process(['/bin/sed', '-i', 's/set PermitRootLogin {0}/'
                                             'set PermitRootLogin {1}/g'.format(_from, _to),
                           ppfile])
        print('Waiting for current puppet run to complete ...')
        while True:
            # Wait for puppet to finish what it's already at
            puppet_status = self.get_puppet_status()
            if puppet_status['applying'] == 0:
                break
            sleep(1)
        print('No agents active, running again with modified sshd config ...')
        self.exec_process(['/usr/bin/mco', 'puppet', 'runonce'])
        while True:
            # Wait for puppet to finish what it's already at
            puppet_status = self.get_puppet_status()
            if puppet_status['applying'] == 0:
                break
            sleep(5)
        print('Puppet agents complete ...')

    def reset_passwords(self, hostname, litpadmin_old_password,
                        litpadmin_new_password,
                        root_old_passwd,
                        root_new_passwd):
        if hostname is None:
            raise KeyError('hostname is null!')
        if litpadmin_old_password is None:
            raise KeyError('Old litp-admin password is null!')
        if litpadmin_new_password is None:
            raise KeyError('New litp-admin password is null!')
        if root_old_passwd is None:
            raise KeyError('Old root password is null!')
        if root_new_passwd is None:
            raise KeyError('New root password is null!')
        self.reset_node_litpadmin_password(hostname, litpadmin_old_password,
                                           litpadmin_new_password)
        self.reset_node_root_password(hostname, litpadmin_new_password,
                                      root_old_passwd, root_new_passwd)

if __name__ == '__main__':
    arg_parser = OptionParser()
    arg_parser.add_option('--hostname', dest='hostname')
    arg_parser.add_option('--litpadmin_old', dest='litpadmin_old')
    arg_parser.add_option('--litpadmin_new', dest='litpadmin_new')
    arg_parser.add_option('--root_old', dest='root_old')
    arg_parser.add_option('--root_new', dest='root_new')
    arg_parser.add_option('--enable_root_ssh', action='store_true')
    arg_parser.add_option('--disable_root_ssh', action='store_true')

    (options, args) = arg_parser.parse_args()  # pylint: disable=W0612
    if len(argv) == 1:
        arg_parser.print_help()
        exit(2)
    pr = PasswordReset()
    if options.enable_root_ssh:
        pr.enable_root_ssh('yes')
    elif options.disable_root_ssh:
        pr.enable_root_ssh('no')
    else:
        pr.reset_passwords(options.hostname,
                       options.litpadmin_old,
                       options.litpadmin_new,
                       options.root_old,
                       options.root_new)
