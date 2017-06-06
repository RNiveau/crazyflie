# -*- coding: utf-8 -*-


class Vector:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def __str__(self):
        return "{x=" + str(self.x) + ", y=" + str(self.y) + ", z=" + str(self.z) + "}"


class Point:
    def __init__(self):
        self.roll = 0
        self.pitch = 0
        self.yaw = 0

    def __str__(self):
        return "{roll=" + str(self.roll) + ", pitch=" + str(self.pitch) + ", yaw=" + str(self.yaw) + "}"


class Position:
    def __init__(self):
        self.initPoint = None
        self.point = Point()
        self.accelerator = Vector()
        self.gyro = Vector()

    def __str__(self):
        return "{initPoint=" + str(self.initPoint) + ", point=" + str(self.point) + ", accelerator=" + str(self.accelerator) + ", gyro=" + str(self.gyro) + "}"
