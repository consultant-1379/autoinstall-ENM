#!/bin/bash

# COPYRIGHT Ericsson 2020
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.

# @since:     February 2020
# @author:    Laurence Canny
# @summary:   Verify iptables and ip6tables have been applied to
#             vms that are not blacklisted.
# @result:    fw rules and number of fw ruls are written to
#             results.out and ip6results.out for both whitelisted
#             and blacklisted services

# Prerequisites:
# Tests must be called from LMS

script=$(readlink -f "$0")
script_path=$(dirname "${script}")

SSH_CMD="ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no -n -i ${HOME}/.ssh/vm_private_key cloud-user@"
LITP_SHOW="litp show -p /software/services"
wl_services="${script_path}"/wl_services.out
wl_service_ips="${script_path}"/wl_service_ips.out
bl_service_ips="${script_path}"/bl_service_ips.out
blacklisted_vms_in_deployment="${script_path}"/blacklisted_vms_present.out
results="${script_path}"/results.out
ip6results="${script_path}"/ip6results.out
wl_ipv6_service_ips="${script_path}"/wl_ipv6_service_ips.out
bl_ipv6_service_ips="${script_path}"/bl_ipv6_service_ips.out
ipv6_conn="${script_path}"/ipv6_conn.out
temp_file=$(mktemp)
pass=12shroot

blacklist_vms=( 'amos' 'apeps1' 'apeps2' 'apeps3' 'apeps4' 'apeps5' 'apeps6' \
                'asrkafka1' 'asrlfwd1' 'asrlfwd2' 'asrlservice' 'asrltopologyservice' \
                'cnom' 'ebskafka1' 'ebsstream1' 'ebsstream2' 'ebsstream3' 'ebsstream4' \
                'ebsstream5' 'ebsstream6' 'ebsstream7' 'ebsstream8' 'ebsstream9' \
                'ebsstream10' 'ebsstream11' 'ebsstream12' 'ebsstreamcontroller1' \
                'ebsstreamtopology' 'elementmanager' 'eventlvsrouter' 'kafka1' \
                'lvsrouter' 'msstr1' 'ops' 'reg1' 'scripting' 'scriptinglvsrouter' \
                'smrsserv' 'sparkMaster' 'sparkWorker1' 'sparkWorker2' 'sparkWorker3' \
                'sparkWorker4' 'sparkWorker5' 'sparkWorker6' 'sparkWorker7' \
                'sparkWorker8' 'sparkWorker9' 'sparkWorker10' 'streamingasrlvsrouter' \
                'streamingebslvsrouter' 'streaminglvsrouter' 'winfiol' 'zoo1' 'nbalarmip' )

containsElement () {

  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1

}

copy_key_to_peernode () {

    node=$1
    key_type=$2

    if [ "${key_type}" == "cloud" ];then
        echo ">>>>> Copying cloud key to ${node}"
        scp /root/.ssh/vm_private_key litp-admin@"${node}":/home/litp-admin/.ssh
    else
        echo ">>>>> Copying litp-admin key to ${node}"
        /usr/bin/expect << EOD
spawn ssh-copy-id -i /root/.ssh/id_rsa.pub litp-admin@${node}
expect {
"*assword: "
}
send "${pass}\r"
sleep 1
EOD
    fi
}

check_for_results_file() {

    now_timestamp=$(date +%s)

    results_files=" ${results} ${ip6results} ${ipv6_conn} "

    for file in ${results_files};do
        if [ -f "${file}" ]; then
            mv "${file}" "${file}"_"${now_timestamp}"
        fi
    done

}

get_address_from_model () {

    services_to_check=$1
    service_ips=$2
    ip_type=$3

    if [[ ${ip_type} =~ v6 ]];then
        interface=vm_network_interfaces/services
    else
        interface=vm_network_interfaces/internal
    fi

    while read line;
    do
        # Check if the service is of type vm-service
        service_type=$(${LITP_SHOW}/"${line}" | grep type)
        if [[ ${service_type} =~ vm-service ]]; then
            vm_ip=$(${LITP_SHOW}/"$line"/"${interface}" -o "${ip_type}")
            if [[ "${vm_ip}" =~ ^[0-9]{1,3}\. ]] || [[ "${vm_ip}" =~ ^(2001:) ]]; then
                echo "${line}" "${vm_ip}" >> "${service_ips}"
            fi
        fi
    done < "${services_to_check}"

}

check_iptables_on_vm () {

    service_ips=$1

    # Hardening should be applied to these vms. ssh to the
    # ip's and check for the ip tables
    while read line;
    do
        service=$(echo "${line}" | awk '{print $1}')

        # Get the number of ip's associated with a single vm
        ip_count=$(echo "$(IFS=' '; set -f; set -- $line; echo $#)")
        # Start from count 2 as it's the first ip
        for (( i=2 ; i<="${ip_count}" ; i++ ))
        do
            ip=$(echo "${line}" | awk -v I="$i" '{print $I}')

            # Get the iptables rules
            echo "# iptables rules for $service #" >> "${results}"
            if ! ${SSH_CMD}"${ip}" "hostname; sudo /sbin/iptables -L; sudo /sbin/iptables --list --line-numbers | sed '/^num\|^$\|^Chain/d' | wc -l;echo" >> "${results}"; then
                echo -e "Cannot ssh to $line - check subnet\n" >> "${results}"
            fi

            # Get the ip6tables rules
            echo "# ip6tables rules for $service #" >> "${ip6results}"
            if ! ${SSH_CMD}"${ip}" "hostname; sudo /sbin/ip6tables -L; sudo /sbin/ip6tables --list --line-numbers | sed '/^num\|^$\|^Chain/d' | wc -l;echo" >> "${ip6results}"; then
                echo -e "Cannot ssh to $line - check subnet\n" >> "${ip6results}"
            fi
        done
    done < "${service_ips}"

}

process_wl_vms () {

    ${LITP_SHOW} > "${wl_services}"
    # Remove first 5 lines
    sed -i 1,5d "${wl_services}"
    # Remove tabs and slashes from service names
    sed -i 's/[ \t]*\///' "${wl_services}"

    # Check for results files and rename them if present
    check_for_results_file

    cp -f "${wl_services}" "${temp_file}"

    while read line;
    do
        if containsElement "${line}" "${blacklist_vms[@]}"; then
            echo "${line}" >> "${blacklisted_vms_in_deployment}"
            sed -i "s/${line}//" "${wl_services}"
        fi
    done < "${temp_file}"

    # Remove blank lines
    sed -i '/^$/d' "${wl_services}"

    # Get the ip address(es) for the whitelisted services
    get_address_from_model "${wl_services}" "${wl_service_ips}" "ipaddresses"
    get_address_from_model "${wl_services}" "${wl_ipv6_service_ips}" "ipv6addresses"

    # Remove commas
    sed -i 's/,/ /g' "${wl_service_ips}"
    sed -i 's/,/ /g' "${wl_ipv6_service_ips}"

    # Hardening should be applied to these vms. ssh to the
    # ip's and check for the ip tables
    check_iptables_on_vm "${wl_service_ips}"

}

process_bl_vms () {

    # Get the ip address(es) for the blacklisted services
    get_address_from_model "${blacklisted_vms_in_deployment}" "${bl_service_ips}" "ipaddresses"
    get_address_from_model "${blacklisted_vms_in_deployment}" "${bl_ipv6_service_ips}" "ipv6addresses"

    # Remove commas
    sed -i 's/,/ /g' "${bl_service_ips}"
    sed -i 's/,/ /g' "${bl_ipv6_service_ips}"

    echo "###############################" | tee -a "${results}" "${ip6results}"
    echo "     BLACKLISTED SERVICES      " | tee -a "${results}" "${ip6results}"
    echo "###############################" | tee -a "${results}" "${ip6results}"

    # Hardening should NOT be applied to these vms. ssh to the
    # ip's and check for the ip tables
    check_iptables_on_vm "${bl_service_ips}"

}

clean_up () {

    ###
    # Remove files that need to be created
    #  on each iteration
    remove_files=" ${blacklisted_vms_in_deployment} ${bl_service_ips} ${wl_service_ips} ${wl_services} ${wl_ipv6_service_ips} ${bl_ipv6_service_ips} ${temp_file} "

    for file in ${remove_files};do
        rm -f "${file}"
    done

}

test_conn_using_ipv6 () {


    ipv6_service_ips=$1
    service=$2
    node=$3

    if ! ssh -o PasswordAuthentication=no -q litp-admin@"${node}" exit; then
        copy_key_to_peernode "${node}"
    fi
    if ! ssh -q litp-admin@"${node}" "[ -f ~/.ssh/vm_private_key ]"; then
        copy_key_to_peernode "${node}" "cloud"
    fi

    echo "Verify ${service} ipv6 SSH connection from a peer node inside ENM to VM node" >> "${ipv6_conn}"

    while read line;
    do

        vm_name=$(echo "${line}" | awk '{print $1}')

        # Get the number of ip's associated with a single vm
        ip_count=$(echo "$(IFS=' '; set -f; set -- $line; echo $#)")
        # Start from count 2 as it's the first ip
        for (( i=2 ; i<="${ip_count}" ; i++ ))
        do
            ipv6_addr=$(echo "${line}" | awk -v I="$i" '{print $I}')

            echo "*** ${vm_name} ***" >> "${ipv6_conn}"
            ssh -n -q litp-admin@"${node}" "ssh -q -o ConnectTimeout=3 -o StrictHostKeyChecking=no -n -i \${HOME}/.ssh/vm_private_key cloud-user@${ipv6_addr} \"hostname\"" >> "${ipv6_conn}"
        done
    done < "${ipv6_service_ips}"

}

run_test_conn_using_ipv6 () {

# Can pass in any peer node here
# or loop through peer nodes to test
# ipv6 connectivity from all peer nodes
peers=$(mco find | grep -v db | grep -v ms)
peer_node=$(echo ${peers} | awk '{print $1}')

test_conn_using_ipv6 "${wl_ipv6_service_ips}" "WHITELIST" "${peer_node}"
test_conn_using_ipv6 "${bl_ipv6_service_ips}" "BLACKLIST" "${peer_node}"

}

process_wl_vms
process_bl_vms
run_test_conn_using_ipv6
clean_up
