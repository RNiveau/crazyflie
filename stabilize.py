import logging
import time
from functools import reduce
from threading import Timer

import cflib.crtp  # noqa
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig

from modules.classes import CrazyflieContext, FlyData
from modules.classes import Point

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

    def _startup(self):
        # Unlock startup thrust protection
        self._cf.commander.send_setpoint(0, 0, 0, 0)

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        logger.info('Connected to %s' % link_uri)
        self._startup()
        self._cf.commander.send_setpoint(0, 0, 0, 35000)
        self._context = CrazyflieContext()

        # The definition of the logconfig can be made before connecting
        self._lg_stab = LogConfig(name='Stabilizer / Acc', period_in_ms=10)
        self._lg_stab.add_variable('stabilizer.roll', 'float')
        self._lg_stab.add_variable('stabilizer.pitch', 'float')
        self._lg_stab.add_variable('stabilizer.yaw', 'float')

        self._lg_gyro = LogConfig(name='Gyro', period_in_ms=10)
        self._lg_gyro.add_variable('acc.x', 'float')
        self._lg_gyro.add_variable('acc.y', 'float')
        self._lg_gyro.add_variable('acc.z', 'float')
        self._lg_gyro.add_variable('gyro.x', 'float')
        self._lg_gyro.add_variable('gyro.y', 'float')
        self._lg_gyro.add_variable('gyro.z', 'float')

        # self._lg_motor = LogConfig(name='Motors', period_in_ms=100)
        # self._lg_motor.add_variable('motor.m1', 'int32_t')
        # self._lg_motor.add_variable('motor.m2', 'int32_t')
        # self._lg_motor.add_variable('motor.m3', 'int32_t')
        # self._lg_motor.add_variable('motor.m4', 'int32_t')

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
            self._lg_stab.data_received_cb.add_callback(self._last_ten_point)
            # self._lg_stab.data_received_cb.add_callback(lambda x, y, z: (logger.info(self._stabilize.point)))

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
            # self._lg_gyro.start()
            #   self._lg_motor.start()
        except KeyError as e:
            logger.error('Could not start log configuration,'
                         '{} not found in TOC'.format(str(e)))
        except AttributeError:
            logger.error('Could not add Stabilizer log config, bad configuration.')
        Timer(1.9, self._startup).start()
        Timer(2, self._cf.close_link).start()

    def _last_ten_point(self, timestamp, data, logconf):
        if len(self._context.fly_data) >= 10:
            subset = self._context.fly_data[
                     len(self._context.fly_data) - 11: len(self._context.fly_data) - 1]
            sum_point = reduce(add_point, subset, FlyData(point=Point()))
            sum_point._point.roll /= 10
            sum_point._point.pitch /= 10
            sum_point._point.yaw /= 10
            sum_point._point.roll -= self._context.init_point.roll
            sum_point._point.pitch -= self._context.init_point.pitch
            sum_point._point.yaw -= self._context.init_point.yaw
            # self._cf.commander.send_setpoint(-sum_point._point.roll, -sum_point._point.pitch,
            #                                  -sum_point._point.yaw, 33500)
            print(sum_point)
            print(self._context.init_point)
            print(*subset)

    def _store_data(self, timestamp, data, logconf):
        fly_data = None
        if len(self._context.fly_data) > 0:
            fly_data = self._context.fly_data[len(self._context.fly_data) - 1]
        if 'stabilizer.roll' in data:
            point = Point(data['stabilizer.roll'], data['stabilizer.pitch'], data['stabilizer.yaw'])
            self._context.last_data = point
            if fly_data is None:
                fly_data = FlyData()
                fly_data.point(point)
                self._context.add_data(fly_data)
            elif fly_data.point is not None:
                fly_data = FlyData()
                fly_data.point(point=point)
                self._context.add_data(fly_data)
            else:
                fly_data.point(point=point)
        # if 'acc.x' in data:
        #     self._context.accelerator.x = data['acc.x']
        #     self._context.accelerator.y = data['acc.y']
        #     self._context.accelerator.z = data['acc.z']
        # if 'gyro.x' in data:
        #     self._context.gyro.x = data['gyro.x']
        #     self._context.gyro.y = data['gyro.y']
        #     self._context.gyro.z = data['gyro.z']
        if self._context.init_point is None and 'stabilizer.roll' in data:
            self._context.init_point = Point(data['stabilizer.roll'], data['stabilizer.pitch'],
                                             data['stabilizer.yaw'])

    def _send_position(self, timestamp, data, logconf):
        roll = self._context.init_point.roll - self._context.lastPoint.roll
        pitch = self._context.init_point.pitch - self._context.lastPoint.pitch
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


def add_point(fly_data, fly_data2):
    return FlyData(point=Point(fly_data._point.roll + fly_data2._point.roll,
                               fly_data._point.pitch + fly_data2._point.pitch,
                               fly_data._point.yaw + fly_data2._point.yaw))


if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)
    le = StabilizeRun('radio://0/80/250K')
    while le.is_connected:
        time.sleep(1)
