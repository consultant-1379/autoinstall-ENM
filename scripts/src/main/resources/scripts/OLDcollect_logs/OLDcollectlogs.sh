#! /bin/bash

# Run the reset passwords script to ensure that peer node passwords are set
# Need to copy reset_passwords scripts to MS in log_collection.py
#sh reset_passwords.bsh

# MAKE DIRECTORY TO COPY LOGS TO
mkdir /tmp/logs/
# MAKE DIRECTORY FOR MS SPECIFIC LOGS
mkdir /tmp/logs/ms_logs/
mkdir /tmp/logs/ms_logs/plugins
mkdir /tmp/logs/ms_logs/var_log_litp/
mkdir /tmp/logs/ms_logs/cobbler/
mkdir /tmp/logs/ms_logs/httpd/
mkdir /tmp/logs/ms_logs/hyperic/
mkdir /tmp/logs/ms_logs/tuned/

list_message_files=( $(ls /var/log/ | grep messages) )
for line in "${list_message_files[@]}"
do
    cp /var/log/$line /tmp/logs/ms_logs/$line.log
done
cp /var/log/mcollective.log /tmp/logs/ms_logs/mcollective.log
cp /var/log/mcollective-audit.log /tmp/logs/ms_logs/mcollective-audit.log
cp /var/lib/litp/core/model/LAST_KNOWN_CONFIG /tmp/logs/ms_logs/LAST_KNOWN_CONFIG
cp /opt/ericsson/enminst/log/patch_rhel.log /tmp/logs/ms_logs/patch_rhel.log
cp /var/log/boot.log /tmp/logs/ms_logs/boot.log
cp /var/log/yum.log /tmp/logs/ms_logs/yum.log
cp -r /opt/ericsson/nms/litp/etc/puppet/manifests/plugins/* /tmp/logs/ms_logs/plugins/
cp -r /var/log/litp/* /tmp/logs/ms_logs/var_log_litp/
cp -r /var/log/cobbler/* /tmp/logs/ms_logs/cobbler/
cp -r /var/log/httpd/* /tmp/logs/ms_logs/httpd/
cp -r /var/log/hyperic/* /tmp/logs/ms_logs/hyperic/
cp -r /var/log/tuned/* /tmp/logs/ms_logs/tuned/
cp /var/tmp/enm-version /tmp/logs/ms_logs/enm-version
cp /etc/litp-release /tmp/logs/ms_logs/litp-release
cp /var/log/enminst.log /tmp/logs/ms_logs/enminst.log
litp show_plan > litp_plan.txt
cp litp_plan.txt /tmp/logs/ms_logs/litp_plan.txt

# MAKE DIRECTORIES FOR EACH OF THE PEER HOSTS

#get_peer_nodes=( $(litp show -rp / | grep -v "inherited from" | grep -B1 "type: node" | grep -v type | grep "/") )
get_peer_nodes=( $(litp show -rp /deployments/enm/clusters/ | grep -v "inherited from" | grep -B1 "type: node" | grep -v type | grep "/") )
for line in "${get_peer_nodes[@]}"
do
    hostnamei=( $(litp show -p $line | grep hostname | sed 's/        hostname: //g' ) )
    mkdir /tmp/logs/$hostnamei
    expect logs/key_setup.exp $hostnamei
    expect logs/scp_file.exp $hostnamei "/var/log/messages*" /tmp/logs/$hostnamei/
    cpy_mess=( $(ls /tmp/logs/$hostnamei/ | grep messages) )
    for line1 in "${cpy_mess[@]}"
    do
        mv logs/$hostnamei/$line1 /tmp/logs/$hostnamei/$line1.log
    done
    expect logs/scp_file.exp $hostnamei /var/log/litp/litp_libvirt.log /tmp/logs/$hostnamei/
    expect logs/scp_file.exp $hostnamei "/var/VRTSvcs/log/*" /tmp/logs/$hostnamei/
    expect logs/scp_file.exp $hostnamei "/etc/VRTSvcs/conf/config/main.cf*" /tmp/logs/$hostnamei/
    expect logs/scp_file.exp $hostnamei /var/log/mcollective.log /tmp/logs/$hostnamei/mcollective.log
    expect logs/scp_file.exp $hostnamei /var/log/mcollective-audit.log /tmp/logs/$hostnamei/mcollective-audit.log
    expect logs/scp_file.exp $hostnamei "/var/coredumps/*" /tmp/logs/$hostnamei/
    expect logs/scp_file.exp $hostnamei /var/log/boot.log /tmp/logs/$hostnamei/boot.log
done
echo ""
tar -Pzcvf /tmp/litp_messages.tar.gz /tmp/logs/
ls /tmp/logs
rm -rf /tmp/logs/
