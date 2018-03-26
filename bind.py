#!/usr/bin/env python2

'''
Custom dynamic inventory script for Ansible
to build inventory from bind zones configuration
files. Configuration is performed by the bind.ini
file.
'''

import os
import sys
import argparse
import re
import logging
from string import digits, letters, punctuation
from sets import Set

try:
    import json
except ImportError:
    import simplejson as json

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser


class BindInventory(object):

    # empty inventory for testing.
    def _empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # init the log
    def _log_init(self):
        self.logger = logging.getLogger('bind')
        FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
        logging.basicConfig(format=FORMAT, level=logging.INFO)

    def __init__(self):
        self.inventory = self._empty_inventory()
        self.read_cli()
        self.read_settings()
        self._log_init()

        # called with `--list`.
        if self.args.list:
            # self.inventory = self.example_inventory()
            self.inventory = self.zones_parse()
        # called with `--host [hostname]`.
        elif self.args.host:
            # not implemented, since we return _meta info `--list`.
            self.inventory = self._empty_inventory()
        # if no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self._empty_inventory()

        print json.dumps(self.inventory)

    # read the command line args passed to the script.
    def read_cli(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', action='store')
        self.args = parser.parse_args()

    # read the settings from the ini file
    def read_settings(self):
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/bind.ini')
        self.basepath = config.get('bind', 'zones_path')
        self.zones = config.get('bind', 'zones').split(',')
        self.include = config.get('bind', 'include_filter').strip('"')
        self.exclude = config.get('bind', 'exclude_filter').strip('"')

    # parse the bind zone files
    def zones_parse(self):
        basepath = self.basepath
        zones = self.zones
        include = self.include
        exclude = self.exclude
        inventory = {'_meta': {'hostvars': {}}}
        for zone in zones:
            zone_path = self.get_zone_path(zone)
            clusters = self.get_clusters(zone_path)
            for cluster in clusters:
                self.logger.debug(cluster)
                inventory[cluster] = {}
                prod = stg = dev = single_cluster = False
                idxs = self.get_indexes(zone_path, cluster)
                self.logger.debug(idxs)
                for idx in idxs:
                    host = '%s%s.%s' % (cluster, idx, zone[3:])
                    self.logger.debug(host)
                    if not idx and not single_cluster:
                        # single host cluster
                        inventory[cluster]['hosts'] = []
                        inventory[cluster]['hosts'].append(host)
                        single_cluster = True
                        continue
                    idxn = int(idx)
                    if idxn < 80 and not prod:
                        inventory[cluster]['hosts'] = []
                        prod = True
                    elif idxn >= 80 and idxn < 90 and not stg:
                        inventory[cluster]['hosts'] = []
                        stg = True
                    elif idxn >= 90 and not dev:
                        inventory[cluster]['hosts'] = []
                        dev = True
                    inventory[cluster]['hosts'].append(host)
        return inventory

    # get a list of cluster
    def get_clusters(self, zone_path):
        basepath = self.basepath
        include = self.include
        exclude = self.exclude
        clusters = Set()
        with open(zone_path, 'r') as zone_src:
            # strip out empty lines
            lines = filter(None, (line.rstrip() for line in zone_src))
            for l in lines:
                if re.search(include, l) and not re.search(exclude, l):
                    self.logger.debug(l.split()[0].translate(None, digits))
                    clusters.add(l.split()[0].translate(None, digits))
        return sorted(clusters)

    # get a list of indexes for cluster
    def get_indexes(self, zone_path, cluster):
        idxs = Set()
        with open(zone_path, 'r') as zone_src:
            for l in zone_src:
                if l.startswith(cluster) and \
                   re.search(self.include, l) and \
                   not re.search(self.exclude, l):
                    idx = l.split()[0].translate(None, letters)
                    idxs.add(idx.translate(None, punctuation))
        return sorted(idxs)

    # return the path of a bind zone file
    def get_zone_path(self, zone):
        return os.path.join(self.basepath, zone)


# get the inventory.
BindInventory()
