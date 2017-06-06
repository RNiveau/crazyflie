import logging
import time
from threading import Timer

import cflib.crtp  # noqa
from modules.classes import Point
from modules.classes import Position
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig

logging.basicConfig(format="%(asctime)s %(levelname)s:%(name)s:%(message)s", level=logging.INFO)
logger = logging.getLogger("StabilizeRun")


class StabilizeRun:
    """
    Simple logging example class that logs the Stabilizer from a supplied
    link uri and disconnects after 5s.
    """

    def __init__(self, link_uri):
        """ Initialize and run the example with the specified link_uri """

        # Create a Crazyflie object without specifying any cache dirs
        self._cf = Crazyflie(rw_cache="/Users/Xebia/Downloads/cache-crazyflie/")

        # Connect some callbacks from the Crazyflie API
        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        logger.info('Connecting to %s' % link_uri)

        # Try to connect to the Crazyflie
        self._cf.open_link(link_uri)

        # Variable used to keep main loop occupied until disconnect
        self.is_connected = True

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        logger.info('Connected to %s' % link_uri)

        self._stabilize = Position()

        # The definition of the logconfig can be made before connecting
        self._lg_stab = LogConfig(name='Stabilizer / Acc', period_in_ms=10)
        self._lg_stab.add_variable('stabilizer.roll', 'float')
        self._lg_stab.add_variable('stabilizer.pitch', 'float')
        self._lg_stab.add_variable('stabilizer.yaw', 'float')
        self._lg_stab.add_variable('acc.x', 'float')
        self._lg_stab.add_variable('acc.y', 'float')
        self._lg_stab.add_variable('acc.z', 'float')

        self._lg_gyro = LogConfig(name='Gyro', period_in_ms=10)
        self._lg_gyro.add_variable('gyro.x', 'float')
        self._lg_gyro.add_variable('gyro.y', 'float')
        self._lg_gyro.add_variable('gyro.z', 'float')

        self._lg_motor = LogConfig(name='Motors', period_in_ms=100)
        self._lg_motor.add_variable('motor.m1', 'int32_t')
        self._lg_motor.add_variable('motor.m2', 'int32_t')
        self._lg_motor.add_variable('motor.m3', 'int32_t')
        self._lg_motor.add_variable('motor.m4', 'int32_t')

        # Adding the configuration cannot be done until a Crazyflie is
        # connected, since we need to check that the variables we
        # would like to log are in the TOC.
        try:
            self._cf.log.add_config(self._lg_stab)
            self._cf.log.add_config(self._lg_gyro)
            # self._cf.log.add_config(self._lg_motor)
            # This callback will receive the data
            # self._lg_stab.data_received_cb.add_callback(self._stab_log_data)
            self._lg_stab.data_received_cb.add_callback(self._store_data)
            #self._lg_stab.data_received_cb.add_callback(lambda x, y, z: (logger.info(self._stabilize.point)))

            # self._lg_stab.data_received_cb.add_callback(self._send_position)
            #  self._lg_stab.data_received_cb.add_callback(self._stab)
            # self._lg_stab.data_received_cb.add_callback(self._send_position)
            # self._lg_gyro.data_received_cb.add_callback(self._stab_log_data)
            self._lg_gyro.data_received_cb.add_callback(self._store_data)
#            self._lg_gyro.data_received_cb.add_callback(self._stab_log_data)
            # self._lg_gyro.data_received_cb.add_callback(self._send_position)
            # self._lg_motor.data_received_cb.add_callback(self._stab_log_data)
            # This callback will be called on errors
            self._lg_stab.error_cb.add_callback(self._stab_log_error)
            # Start the logging
            self._lg_stab.start()
          #  self._lg_gyro.start()
            #   self._lg_motor.start()
        except KeyError as e:
            logger.error('Could not start log configuration,'
                         '{} not found in TOC'.format(str(e)))
        except AttributeError:
            logger.error('Could not add Stabilizer log config, bad configuration.')
        self._cf.commander.send_setpoint(0, 0, 0, 30000)
        Timer(2, self._cf.close_link).start()

    def _store_data(self, timestamp, data, logconf):
        if 'stabilizer.roll' in data:
            self._stabilize.point.roll = data['stabilizer.roll']
            self._stabilize.point.pitch = data['stabilizer.pitch']
            self._stabilize.point.yaw = data['stabilizer.yaw']
        if 'acc.x' in data:
            self._stabilize.accelerator.x = data['acc.x']
            self._stabilize.accelerator.y = data['acc.y']
            self._stabilize.accelerator.z = data['acc.z']
        if 'gyro.x' in data:
            self._stabilize.gyro.x = data['gyro.x']
            self._stabilize.gyro.y = data['gyro.y']
            self._stabilize.gyro.z = data['gyro.z']
        if self._stabilize.initPoint is None:
            self._stabilize.initPoint = Point()
            self._stabilize.initPoint.roll = data['stabilizer.roll']
            self._stabilize.initPoint.pitch = data['stabilizer.pitch']
            self._stabilize.initPoint.yaw = data['stabilizer.yaw']

    def _send_position(self, timestamp, data, logconf):
        roll = self._stabilize.initPoint.roll - self._stabilize.point.roll
        pitch = self._stabilize.initPoint.pitch - self._stabilize.point.pitch
        logger.info("Send position %f %f %f" % (roll, pitch, 0))
        self._cf.commander.send_setpoint(roll, pitch, 0, 33500)

    def _last_position(self):
        logger.info("Send last position")
        self._cf.commander.send_setpoint(0, 0, 0, 0)

    def _stab_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        logger.error('Error when logging %s: %s' % (logconf.name, msg))

    def _stab_log_data(self, timestamp, data, logconf):
        """Callback froma the log API when data arrives"""
        logger.info('[%d][%s]: %s' % (timestamp, logconf.name, data))

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the speficied address)"""
        logger.error('Connection to %s failed: %s' % (link_uri, msg))
        self.is_connected = False

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        logger.error('Connection to %s lost: %s' % (link_uri, msg))

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        logger.info('Disconnected from %s' % link_uri)
        self.is_connected = False


if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)
    le = StabilizeRun('radio://0/80/250K')
    while le.is_connected:
        time.sleep(1)
