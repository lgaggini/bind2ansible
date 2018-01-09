#! /bin/bash
#
# Author: Lorenzo Gaggini - lg@lgaggini.net
# Script to generate ansible static inventory from bind zones
#
# ./bind2ansible.sh

# script configuration
# default ansible user
default_user="root"
# default custom ssh port
custom_port=""
# bind zones path
zones_path="/bind/files/zones/"
# zones filename to parse
zones=(db.my.zone1 db.my.zone2)
# start to parse after this line
parse_after="SERVERS"
# line (records) to include
include_filter=" A "
# lines (vip, windows cluster, etc..) to exclude
exclude_filter="^;"

# global inventory variables
echo "[all:vars]"
echo "ansible_connection=ssh"
echo "ansible_user=${default_user}"
echo "ansible_ssh_common_args='-F /etc/ansible/ansible_ssh_config'"
echo

# common zones
for zone in ${zones[@]}; do
    clusters=$(cat ${zones_path}${zone} | sed -e "1,/$parse_after/d" | grep ${include_filter} | awk '{print $1}' | sort | uniq | grep -vE ${exclude_filter} | sed 's/[^a-Z-]//g' | uniq -c | awk '($1 > 1 )' | awk '{print $2}' | sort | uniq)
    for cluster in $clusters; do
        prod=0
        stg=0
        int=0
        indexes=$(cat ${zones_path}${zone} | awk '{print $1}' | sort | uniq | grep -vE "^;" | grep "^${cluster}" | sed 's/[^0-9]//g' | sort | uniq)
        for index in $indexes; do
            dec_index=$((10#${index}))
            case 1 in
                $((${dec_index}<80 && ${prod}==0)))
                    echo
                    echo "[${cluster}]"
                    prod=1;;
                $((${dec_index}>=80 && ${dec_index} < 90 && ${stg}==0)))
                    echo
                    echo "[${cluster}-stg]"
                    stg=1;;
                $((${dec_index}>=90 && ${int}==0)))
                    echo
                    echo "[${cluster}-int]"
                    int=1;;
            esac
            echo "${cluster}${index}.${zone:3}${custom_port}"
        done
    done
done
