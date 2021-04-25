import sys
import utime

from machine import I2C, Pin

from pca9685 import *


class MecanumWheel(object):
    MAX_SPEED = 2400
    MIN_SPEED = 400
    def __init__(self, motor: PCA9685, dials: tuple, speed: int = 1200, step: int = 200):
        self.motor = motor
        self.dials = dials
        self.speed = speed  # 初始速度
        self.step = step  # 速度微调台阶
        self.status = 0  # 0 - 停止, 1 - 前进， -1 - 后退
        self._brake()
        print('wheel init with {} {} {}'.format(dials, speed, step))
    
    # 调速
    def speed(self, opt: str):
        if opt == '+':
            speed = self.speed + self.step
            speed = speed if speed < MecanumWheel.MAX_SPEED else MecanumWheel.MAX_SPEED
            if speed > self.speed:
                self.speed = speed
                self.move(self.status)
                print('wheel {} speed up to {}'.format(self.dials, self.speed))
        elif opt == '-':
            speed = self.speed - self.step
            speed = speed if speed > MecanumWheel.MIN_SPEED else MecanumWheel.MIN_SPEED
            if speed < self.speed:
                self.speed = speed
                self.move(self.status)
                print('wheel {} speed down to {}'.format(self.dials, self.speed))
        else:
            print('wheel {} unknow opt {} {}'.format(self.dials, opt, self.speed))
    
    # 前进
    def _forward(self):
        self.motor.pwm(self.dials[0], self.speed, 0)
        self.motor.pwm(self.dials[1], 0, 0)
        print('wheel {} forward {}'.format(self.dials, self.speed))

    # 后退
    def _backward(self):
        self.motor.pwm(self.dials[0], 0, 0)
        self.motor.pwm(self.dials[1], self.speed, 0)
        print('wheel {} backward {}'.format(self.dials, self.speed))
    
    # 停止
    def _brake(self):
        self.motor.pwm(self.dials[0], 0, 0)
        self.motor.pwm(self.dials[1], 0, 0)
        print('wheel {} stop {}'.format(self.dials, self.speed))
    
    def move(self, status: int):
        self.status = status
        if self.status == 0:
            self._brake()
        elif self.status > 0:
            self._forward()
        else:
            self._backward()


class MecanumVehicle(object):
    motor_dials = ((1, 0), (2, 3), (5, 4), (6, 7))  # 四路马达

    def __init__(self, scl_pin: int, sda_pin: int):
        self.pca = PCA9685(I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin)))  # mode1
        self.pca.freq(1600)
        print('PCA9685 inited')
        self.wheels = []
        for dials in MecanumVehicle.motor_dials:
            self.wheels.append(MecanumWheel(self.pca, dials, 1900))

    def _indicate_wheels(self, flags: list):
        for i in range(4):
            self.wheels[i].move(flags[i])
    #    ↑A-----B↑   
    #     |  ↑  |
    #     |  |  |
    #    ↑C-----D↑
    def move_clock12(self):
        self._indicate_wheels([1, 1, 1, 1])
        
    #    ↓A-----B↓ 
    #     |  |  |
    #     |  ↓  |
    #    ↓C-----D↓
    def move_clock6(self):
        self._indicate_wheels([-1, -1, -1, -1])

    #    =A-----B↑   
    #     |   ↖ |
    #     | ↖   |
    #    ↑C-----D=
    def move_clock10(self):
        self._indicate_wheels([0, 1, 1, 0])

    #    ↓A-----B↑   
    #     |  ←  |
    #     |  ←  |
    #    ↑C-----D↓
    def move_clock9(self):
        self._indicate_wheels([-1, 1, 1, -1])
    
    #    ↓A-----B=   
    #     | ↙   |
    #     |   ↙ |
    #    =C-----D↓
    def move_clock8(self):
        self._indicate_wheels([-1, 0, 0, -1])

    #    ↑A-----B=   
    #     | ↗   |
    #     |   ↗ |
    #    =C-----D↑
    def move_clock2(self):
        self._indicate_wheels([1, 0, 0, 1])

    #    ↑A-----B↓   
    #     |  →  |
    #     |  →  |
    #    ↓C-----D↑
    def move_clock3(self):
        self._indicate_wheels([1, -1, -1, 1])

    #    =A-----B↓   
    #     |   ↘ |
    #     | ↘   |
    #    ↓C-----D=
    def move_clock4(self):
        self._indicate_wheels([0, -1, -1, 0])

    #    ↑A-----B↓   
    #     | ↗ ↘ |
    #     | ↖ ↙ |
    #    ↑C-----D↓
    def move_clockwise(self):
        self._indicate_wheels([1, -1, 1, -1])

    #    ↓A-----B↑   
    #     | ↙ ↖ |
    #     | ↘ ↗ |
    #    ↓C-----D↑
    def move_anticlockwise(self):
        self._indicate_wheels([-1, 1, -1, 1])

    #    =A-----B=  
    #     |  =  |
    #     |  =  |
    #    =C-----D=
    def stop(self):
        self._indicate_wheels([0, 0, 0, 0])
    
    def speed(self, opt: str, motors: list = None):
        if not motors:
            motors = range(4)
        for i in motors:
            self.wheels[i].speed(opt)
