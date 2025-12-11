# modified version of https://github.com/Thorlabs/Light_Analysis_Examples/blob/main/Python/Thorlabs%20PAX1000%20Polarimeters/PAX1000%20using%20ctypes%20-%20Python%203.py

import time
from ctypes import *
import math
import copy


class DeviceNotFound(Exception):
    pass

class InitialisationError(Exception):
    pass


class PAX1000:
    def __init__(self, wavelength=491e-9, scan_rate=60, measurement_mode=9):
        """
        Interface for controlling and reading data from a PAX1000 polarization measurement device.

        Parameters:
            wavelength (float), optional: Wavelength in meters for the measurement (default: 491e-9 m).
            scan_rate (float), optional: Scan rate in Hz (default: 60 Hz).
            measurement_mode (int), optional: Measurement mode of the PAX1000 (default: 9).
        """
        # Load DLL library
        self.__lib = cdll.LoadLibrary("C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLPAX_64.dll")

        # Detect and initialize PAX1000 device
        self.__instrumentHandle = c_ulong()
        self.__IDQuery = True
        self.__resetDevice = False
        self.__resource = c_char_p(b"")
        self.__deviceCount = c_int()

        # Check how many PAX1000 are connected
        self.__lib.TLPAX_findRsrc(self.__instrumentHandle, byref(self.__deviceCount))
        if self.__deviceCount.value < 1:
            print("No PAX1000 device found.")
            raise DeviceNotFound

        # Connect to the first available PAX1000
        self.__lib.TLPAX_getRsrcName(self.__instrumentHandle, 0, self.__resource)
        if not (0 == self.__lib.TLPAX_init(self.__resource.value, self.__IDQuery, self.__resetDevice,
                                           byref(self.__instrumentHandle))):
            print("Error with initialization.")
            raise InitialisationError

        # Short break to make sure the device is correctly initialized
        time.sleep(2)

        # Make settings
        self.__lib.TLPAX_setMeasurementMode(self.__instrumentHandle, measurement_mode)
        self.__lib.TLPAX_setWavelength(self.__instrumentHandle, c_double(wavelength))
        self.__lib.TLPAX_setBasicScanRate(self.__instrumentHandle, c_double(scan_rate))

        # Check settings
        wavelength = c_double()
        self.__lib.TLPAX_getWavelength(self.__instrumentHandle, byref(wavelength))
        mode = c_int()
        self.__lib.TLPAX_getMeasurementMode(self.__instrumentHandle, byref(mode))
        scanrate = c_double()
        self.__lib.TLPAX_getBasicScanRate(self.__instrumentHandle, byref(scanrate))

        # Short break
        time.sleep(5)

    def measure(self):
        """
        Retrieves the latest polarization measurement from the PAX1000.

        Performs a single measurement, returning the azimuth and ellipticity in degrees.

        Returns:
            tuple: (azimuth, ellipticity) in degrees.
        """
        scanID = c_int()
        self.__lib.TLPAX_getLatestScan(self.__instrumentHandle, byref(scanID))

        azimuth = c_double()
        ellipticity = c_double()
        self.__lib.TLPAX_getPolarization(self.__instrumentHandle, scanID.value, byref(azimuth), byref(ellipticity))
        s0 = c_double()
        s1 = c_double()
        s2 = c_double()
        s3 = c_double()
        self.__lib.TLPAX_getStokes(self.__instrumentHandle, scanID.value, byref(s0), byref(s1), byref(s2), byref(s3))

        self.__lib.TLPAX_releaseScan(self.__instrumentHandle, scanID.value)
        time.sleep(0.05)

        dop = math.sqrt(((s1.value**2)+(s2.value**2)+(s3.value**2))/(s0.value**2))
        dolp = math.sqrt(((s1.value**2)+(s2.value**2))/(s0.value**2))
        docp = math.sqrt((s3.value**2)/(s0.value**2))
        power_pol = abs(s1.value) + abs(s2.value) + abs(s3.value)
        power_upol = s0.value - power_pol


        return {"azimuth": copy.deepcopy(math.degrees(azimuth.value)),
                "ellipticity": copy.deepcopy(math.degrees(ellipticity.value)),
                "S0": copy.deepcopy(s0.value),
                "S1": copy.deepcopy(s1.value),
                "S2": copy.deepcopy(s2.value),
                "S3": copy.deepcopy(s3.value),
                "dop": copy.deepcopy(dop),
                "dolp": copy.deepcopy(dolp),
                "docp": copy.deepcopy(docp),
                "power_pol": copy.deepcopy(power_pol),
                "power_upol": copy.deepcopy(power_upol)}

    def close(self):
        """
        Closes the connection to the PAX1000 device and releases resources.
        """
        self.__lib.TLPAX_close(self.__instrumentHandle)
