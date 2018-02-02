
"""
(ophyd) Devices that might be useful at the APS using BlueSky

.. autosummary::
   
    ~sscanRecord  
    ~sscanDevice
    ~swaitRecord
    ~swait_setup_random_number
    ~swait_setup_gaussian
    ~swait_setup_lorentzian
    ~swait_setup_incrementer
    ~userCalcsDevice
    ~EpicsMotorWithDial
    ~EpicsMotorWithServo
    ~EpicsMotorShutter

"""

# Copyright (c) 2017-2018, UChicago Argonne, LLC.  See LICENSE file.


from .synApps_ophyd import *
from ophyd import Component, EpicsMotor, Device
from bluesky.plan_stubs import mv, mvr, abs_set, wait


class EpicsMotorWithDial(EpicsMotor):
    """
    add motor record's dial coordinates to EpicsMotor
    
    USAGE::
    
        m1 = EpicsMotorWithDial('xxx:m1', name='m1')
    
    """
    dial = Component(EpicsSignal, ".DRBV", write_pv=".DVAL")


class EpicsMotorWithServo(EpicsMotor):
    """extend basic motor support to enable/disable the servo loop controls"""
    
    # values: "Enable" or "Disable"
    servo = Component(EpicsSignal, ".CNEN", string=True)


class EpicsMotorShutter(Device):
    """
    a shutter, implemented with an EPICS motor
    
    USAGE::
        tomo_shutter = EpicsMotorShutter("2bma:m23", name="tomo_shutter")
        tomo_shutter.closed_position = 1.0      # default
        tomo_shutter.open_position = 0.0        # default
        tomo_shutter.open()
        tomo_shutter.close()
        
        # or, when used in a plan
        def planA():
            yield from abs_set(tomo_shutter, "open", group="O")
            yield from wait("O")
            yield from abs_set(tomo_shutter, "close", group="X")
            yield from wait("X")
        def planA():
            yield from abs_set(tomo_shutter, "open", wait=True)
            yield from abs_set(tomo_shutter, "close", wait=True)
        def planA():
            yield from mv(tomo_shutter, "open")
            yield from mv(tomo_shutter, "close")
    """
    motor = Component(EpicsMotor, "")
    closed_position = 1.0
    open_position = 0.0
    _tolerance = 0.01
    
    def isopen(self):
        return abs(self.motor.position - self.open_position) <= self._tolerance
    
    def isclosed(self):
        return abs(self.motor.position - self.closed_position) <= self._tolerance
    
    def open(self):
        """move motor to BEAM NOT BLOCKED position, interactive use"""
        self.motor.move(self.open_position)
    
    def close(self):
        """move motor to BEAM BLOCKED position, interactive use"""
        self.motor.move(self.closed_position)

    def set(self, value, *, timeout=None, settle_time=None):
        """
        `set()` is like `put()`, but used in BlueSky plans

        Parameters
        ----------
        value : "open" or "close"
        timeout : float, optional
            Maximum time to wait. Note that set_and_wait does not support
            an infinite timeout.
        settle_time: float, optional
            Delay after the set() has completed to indicate completion
            to the caller

        Returns
        -------
        status : DeviceStatus
        """

        # using put completion:
        # timeout and settle time is handled by the status object.
        status = DeviceStatus(
            self, timeout=timeout, settle_time=settle_time)

        def put_callback(**kwargs):
            status._finished(success=True)

        if value.lower() == "open":
            pos = self.open_position
        elif value.lower() == "close":
            pos = self.closed_position
        else:
            msg = "value should be either open or close"
            msg + " : received " + str(value)
            raise ValueError(msg)
        self.motor.user_setpoint.put(
            pos, use_complete=True, callback=put_callback)

        return status
