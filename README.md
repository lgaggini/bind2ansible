# bind2ansible

bind2ansible is a tool to generate ansible static inventory from bind9 zones files. It's intended to be runned on a post-merge hook (example included) on the repo which hosts the bind zones files but it could be runned also manually.

## Constraints
* bind zones files are all in the same directory and they are named: db.{{ 2ndlevelel }}.{{ tld }}
* clusters hosts are named: {{ cluster }}{{ index }}.{{ 2ndlevelel }}.{{ tld }}
* index identifies if the host is an integration host (>90), a staging host (<90, >80) or production hosts (<90)

## Configuration
At the top of both scripts there are configuration settings:

### bind2ansible.sh

```bash
# default ansible user
default_user="root"
# default custom ssh port
custom_port=""
# bind zones path
zones_path="/bind/files/zones/"
# zones filename to parse
zones=(db.my.zone1 db.my.zone2)
# line (records) to include
include_filter=" A "
# lines (vip, windows cluster, etc..) to exclude
exclude_filter="^;"
```

### post-merge
```bash
# regexp to match zone files on the git repo to monitor for changes
bind_zone_regexp="/bind/files/zones/"
# command to run on monitored files changes, the awk part removes
# duplicate domains based on the last level, the first zone defined
# in bind2ansible has the precedence
bind2ansible_cmd="/usr/local/bin/bind2ansible.sh | awk -F"." '!x[($1)]++'"
# where to write the ansible static inventory
ansible_inventory="/etc/ansible/hosts"
```

## Run
### Manual Run
```bash
/bind2ansible.sh
```

### Post Merge Hook Run
Copy the post-merge script on your repo in the .git/hook folder and if the settings are ok on first git pull including files matching the `bind_zone_regexp` the script will be launched.

## Future plan
A dynamic inventory script (json output) for ansible implementing the same concept