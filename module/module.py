#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
# This module imports hosts and services configuration from a MySQL Database
# Queries for getting hosts and services are pulled from shinken-specific.cfg configuration file.

try:
    import MySQLdb
except ImportError:
    MySQLdb = None

try:
    import chardet
except ImportError:
    chardet = None

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['arbiter'],
    'type': 'mysql_import',
    'external': False,
    'phases': ['configuration'],
}


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.debug("[MySQLImport]: Get MySQL importer instance for plugin %s" % plugin.get_name())
    if not MySQLdb:
        raise Exception('Missing module python-mysqldb. Please install it.')
    host = plugin.host
    login = plugin.login
    password = plugin.password
    database = plugin.database
    reqlist = {}
    reqlist['hosts'] = getattr(plugin, 'reqhosts', None)
    reqlist['commands'] = getattr(plugin, 'reqcommands', None)
    reqlist['timeperiods'] = getattr(plugin, 'reqtimeperiods', None)
    reqlist['notificationways'] = getattr(plugin, 'reqnotificationways', None)
    reqlist['services'] = getattr(plugin, 'reqservices', None)
    reqlist['servicegroups'] = getattr(plugin, 'reqservicegroups', None)
    reqlist['contacts'] = getattr(plugin, 'reqcontacts', None)
    reqlist['contactgroups'] = getattr(plugin, 'reqcontactgroups', None)
    reqlist['hostgroups'] = getattr(plugin, 'reqhostgroups', None)
    reqlist['hostdependencies'] = getattr(plugin, 'reqhostdependencies', None)
    reqlist['servicedependencies'] = getattr(plugin, 'reqservicedependencies', None)
    reqlist['realms'] = getattr(plugin, 'reqrealms', None)
    reqlist['schedulers'] = getattr(plugin, 'reqschedulers', None)
    reqlist['pollers'] = getattr(plugin, 'reqpollers', None)
    reqlist['brokers'] = getattr(plugin, 'reqbrokers', None)
    reqlist['reactionners'] = getattr(plugin, 'reqreactionners', None)
    reqlist['receivers'] = getattr(plugin, 'reqreceivers', None)

    instance = MySQL_importer_arbiter(plugin, host, login, password, database, reqlist)
    return instance


# Retrieve hosts from a MySQL database
class MySQL_importer_arbiter(BaseModule):
    def __init__(self, mod_conf, host, login, password, database, reqlist):
        BaseModule.__init__(self, mod_conf)
        self.host = host
        self.login = login
        self.password = password
        self.database = database
        self.reqlist = reqlist

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[MySQLImport]: Try to open a MySQL connection to %s" % self.host)
        try:
            self.conn = MySQLdb.connect(host=self.host,
                        user=self.login,
                        passwd=self.password,
                        db=self.database)
        except MySQLdb.Error, e:
            logger.error("[MySQLImport] Error %d: %s" % (e.args[0], e.args[1]))
            raise
        logger.info("[MySQLImport]: Connection opened")

    def ensure_encoding(self, value):
        try:
            value.decode('utf-8')
        except UnicodeDecodeError, e:
            encoding = chardet.detect(value)['encoding'] or 'latin1'
            logger.warning("[MySQLImport]: Error decoding string " + \
                "(value='%s', encoding='%s')" % (value, encoding) + \
                ". Failing back to utf-8")
            value = value.decode(encoding).encode('utf-8')
        return value

    # Main function that is called in the CONFIGURATION phase
    def get_objects(self):
        if not hasattr(self, 'conn'):
            logger.error("[MySQLImport]: Problem during init phase")
            return {}

        # Create variables for result
        r = {}

        cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)

        # For all parameters
        for k, v in self.reqlist.iteritems():
            r[k] = []

            if(v != None):
                result_set = {}
                logger.info("[MySQLImport]: Getting %s configuration from database" % (k))

                try:
                    cursor.execute(v)
                    result_set = cursor.fetchall()
                except MySQLdb.Error, e:
                    logger.error("[MySQLImport]: Error %d: %s" % (e.args[0], e.args[1]))

                # Create set with result
                for row in result_set:
                    h = {}
                    for column in row:
                        if row[column]:
                            value = str(row[column])
                            if chardet:
                                value = self.ensure_encoding(value)
                            h[column] = value
                    r[k].append(h)

        cursor.close()
        self.conn.close()
        del self.conn

        logger.debug("[MySQLImport]: Returning to Arbiter the object: %s" % str(r))
        return r
