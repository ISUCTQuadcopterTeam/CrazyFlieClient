'''
Created on Apr 18, 2015

@author: Patrickboyle
'''
# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2014 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.

"""
Simple example that connects to the first Crazyflie found, ramps up/down
the motors and disconnects.
"""

import time, sys
from threading import Thread

#FIXME: Has to be launched from within the example folder
sys.path.append("../lib")
import cflib
from cflib.crazyflie import Crazyflie

import cflib.crtp
from cfclient.utils.logconfigreader import LogConfig

import logging
logging.basicConfig(level=logging.ERROR)

class MotorRampExample:
    """Example that connects to a Crazyflie and ramps the motors up/down and
    the disconnects"""
    def __init__(self, link_uri):
        """ Initialize and run the example with the specified link_uri """

        self._cf = Crazyflie()

        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        self._cf.open_link(link_uri)

        print "Connecting to %s" % link_uri

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        self._lg_stab = LogConfig(name="Stabilizer", period_in_ms=10)
        #self._lg_stab.add_variable("stabilizer.roll", "float")
        #self._lg_stab.add_variable("stabilizer.pitch", "float")
        #self._lg_stab.add_variable("stabilizer.yaw", "float")
        self._lg_stab.add_variable("stabilizer.thrust", "float")

        
        self._cf.log.add_config(self._lg_stab)
        if self._lg_stab.valid:
            # This callback will receive the data
            self._lg_stab.data_received_cb.add_callback(self._stab_log_data)
            # This callback will be called on errors
            self._lg_stab.error_cb.add_callback(self._stab_log_error)
            # Start the logging
            self._lg_stab.start()
        else:
            print("Could not add logconfig since some variables are not in TOC")
        # Start a separate thread to do the motor test.
        # Do not hijack the calling thread!
        Thread(target=self._ramp_motors).start()
        
    def _stab_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print "Error when logging %s: %s" % (logconf.name, msg)

    def _stab_log_data(self, timestamp, data, logconf):
        """Callback froma the log API when data arrives"""
        print "[%d][%s]: %s" % (timestamp, logconf.name, data)
    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the speficied address)"""
        print "Connection to %s failed: %s" % (link_uri, msg)

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print "Connection to %s lost: %s" % (link_uri, msg)

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print "Disconnected from %s" % link_uri

    
    def _ramp_motors(self):
        thrust = 45000
        thrust_step = 250
        
        self._cf.param.set_value("flightmode.althold", "False")  
        self._cf.commander.send_setpoint(0,0,0,0)
        totalTime = 0 
        self._cf.commander.send_setpoint(0, 0, 0, 60000)
        time.sleep (.5)
        self._cf.commander.send_setpoint(0, 0, 0, 60000)
        self._cf.param.set_value("flightmode.althold", "True")
        #time.sleep (.5)
        while totalTime <= 1:
            self._cf.commander.send_setpoint(0, -1, 0, 44500)
            time.sleep (.1)
            totalTime += .01
            
        #self._cf.param.set_value("flightmode.althold", "False")
        time.sleep (.5)      
        while thrust >=5000:    
            thrust -= thrust_step
            self._cf.commander.send_setpoint(0, 0, 0, thrust)
            time.sleep (.01)
        
        self._cf.commander.send_setpoint(0, 0, 0, 0)  
        print "done"
        self._cf.close_link()    
    
if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    # Scan for Crazyflies and use the first one found
    print "Scanning interfaces for Crazyflies..."
    available = cflib.crtp.scan_interfaces()
    print "Crazyflies found:"
    for i in available:
        print i[0]

    if len(available) > 0:
        le = MotorRampExample(available[0][0])
    else:
        print "No Crazyflies found, cannot run example"