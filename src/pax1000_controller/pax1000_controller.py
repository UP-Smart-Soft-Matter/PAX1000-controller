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
    def __init__(self,
                 wavelength=491e-9,
                 base_scan_rate=60,
                 measurement_mode=9,
                 dll_lib_path="C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLPAX_64.dll"):
        """
                Python wrapper for a Thorlabs PAX1000 polarimeter using the vendor DLL.

                Initializes the device, applies measurement configuration, and prepares
                the instrument for continuous polarization scans.

                Args:
                    wavelength (float, optional): Optical wavelength in meters used for analysis.
                    base_scan_rate (float, optional): Fundamental scan rate in Hz configured on the device.
                    measurement_mode (int, optional): Acquisition mode defining rotation count and FFT resolution.

                        0  – IDLE, no acquisition
                        1  – H512, half rotation, 512-point FFT
                        2  – H1024, half rotation, 1024-point FFT
                        3  – H2048, half rotation, 2048-point FFT
                        4  – F512, full rotation, 512-point FFT
                        5  – F1024, full rotation, 1024-point FFT
                        6  – F2048, full rotation, 2048-point FFT
                        7  – D512, double rotation, 512-point FFT
                        8  – D1024, double rotation, 1024-point FFT
                        9  – D2048, double rotation, 2048-point FFT

                    dll_lib_path (str): Absolute path to the TLPAX 64-bit DLL.
                """
        if measurement_mode in range(1, 4):
            scan_rate_multiplier = 1
        elif measurement_mode in range(4, 7):
            scan_rate_multiplier = 0.5
        elif measurement_mode in range(7, 10):
            scan_rate_multiplier = 0.25
        else:
            raise InitialisationError("Invalid measurement mode.")

        self.base_scan_rate = base_scan_rate
        self.actual_scan_rate = base_scan_rate * scan_rate_multiplier

        self.__sleep_time = 1/self.actual_scan_rate

        # Load DLL library
        self.__lib = cdll.LoadLibrary(dll_lib_path)

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
        self.__lib.TLPAX_setBasicScanRate(self.__instrumentHandle, c_double(base_scan_rate))

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
        Acquires the most recent polarization scan from the instrument.

        Reads azimuth, ellipticity, and Stokes parameters from the latest completed
        scan, computes polarization metrics, and returns all values in a dictionary.

        Returns:
            dict:
                azimuth (float): Polarization azimuth angle in degrees
                ellipticity (float): Polarization ellipticity angle in degrees
                S0–S3 (float): Stokes parameters
                dop (float): Degree of polarization
                dolp (float): Degree of linear polarization
                docp (float): Degree of circular polarization
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

        time.sleep(self.__sleep_time)

        dop = math.sqrt(((s1.value**2)+(s2.value**2)+(s3.value**2))/(s0.value**2))
        dolp = math.sqrt(((s1.value**2)+(s2.value**2))/(s0.value**2))
        docp = math.sqrt((s3.value**2)/(s0.value**2))


        return {"azimuth": copy.deepcopy(math.degrees(azimuth.value)),
                "ellipticity": copy.deepcopy(math.degrees(ellipticity.value)),
                "S0": copy.deepcopy(s0.value),
                "S1": copy.deepcopy(s1.value),
                "S2": copy.deepcopy(s2.value),
                "S3": copy.deepcopy(s3.value),
                "dop": copy.deepcopy(dop),
                "dolp": copy.deepcopy(dolp),
                "docp": copy.deepcopy(docp)}

    def close(self):
        """
        Terminates communication with the polarimeter.

        Releases the instrument handle and unloads internal resources associated
        with the active PAX1000 session.
        """
        self.__lib.TLPAX_close(self.__instrumentHandle)
