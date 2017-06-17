# -*- coding: utf-8 -*-


class Vector:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return "{x=" + str(self.x) + ", y=" + str(self.y) + ", z=" + str(self.z) + "}"


class Point:
    def __init__(self, roll=0, pitch=0, yaw=0):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw

    def __str__(self):
        return "{roll=" + str(self.roll) + ", pitch=" + str(self.pitch) + ", yaw=" + str(
            self.yaw) + "}"


class FlyData:
    def __init__(self, point=None, accelerator=None, gyro=None):
        self._point = point
        self._accelerator = accelerator
        self._gyro = gyro

    def __str__(self):
        return "{point=" + str(self._point) + ", accelerator=" + str(
            self._accelerator) + ", gyro=" + str(self._gyro) + "}"

    def accelerator(self, x, y, z):
        self._accelerator = Vector(x, y, z)
        return self

    def gyro(self, x, y, z):
        self._gyro = Vector(x, y, z)
        return self

    def point(self, roll=0, pitch=0, yaw=0, point=None):
        if point is not None:
            self._point = point
        else:
            self._point = Point(roll, pitch, yaw)
        return self


class CrazyflieContext:
    def __init__(self):
        self.init_point = None
        self.last_data = None
        self.fly_data = []

    def __str__(self):
        return "{init_point=" + str(self.init_point) + ", last_data=" + str(
            self.last_data) + ", fly_data=" + str(''.join(str(e) for e in self.fly_data)) + "}"

    def add_data(self, fly_data):
        self.fly_data.append(fly_data)
