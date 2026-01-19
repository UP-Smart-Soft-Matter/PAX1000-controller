# PAX1000-controller

Python wrapper for the Thorlabs PAX1000 polarimeter using `ctypes` and the official Thorlabs TLPAX DLL. It provides a minimal, direct interface for device initialization, configuration, and polarization measurements.

The creator of this package/repository is not affiliated with ThorLabs.

---

## Features

- Automatic detection of connected PAX1000 devices  
- Configuration of wavelength, scan rate, and measurement mode  
- Single-shot polarization measurements  
- Access to:
  - Azimuth
  - Ellipticity
  - Full Stokes parameters (S0–S3)
  - Degree of polarization (DoP)
  - Degree of linear polarization (DoLP)
  - Degree of circular polarization (DoCP)

---

## Requirements

- Windows (64-bit)
- Python 3
- Thorlabs PAX1000 polarimeter
- Thorlabs VISA installation
- Thorlabs TLPAX DLL  

Default DLL path used in the code:

```
C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLPAX_64.dll
```

Python standard libraries used:

- ctypes
- time
- math
- copy

---

## Installation

````shell
pip install pax1000_controller
````

---

## Usage

### Basic Example

```python
from pax1000_controller import PAX1000

pax = PAX1000(wavelength=491e-9,
              base_scan_rate=60,
              measurement_mode=9,
              dll_lib_path="C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLPAX_64.dll")

data = pax.measure()
print(data)

pax.close()
```

---

## Class: `PAX1000`

### Constructor

```python
PAX1000(wavelength=491e-9, scan_rate=60, measurement_mode=9, dll_lib_path="C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLPAX_64.dll")
```

Parameters:

- `wavelength` (float): Measurement wavelength in meters  
- `scan_rate` (float): Scan rate in Hz  
- `measurement_mode` (int): PAX1000 measurement mode  
- `dll_lib_path` (str): Path to the TLPAX_64.dll

The constructor:
- Searches for connected PAX1000 devices
- Connects to the first available device
- Applies the provided configuration

Measurement modes: 
- 0  – IDLE, no acquisition
- 1  – H512, half rotation, 512-point FFT
- 2  – H1024, half rotation, 1024-point FFT
- 3  – H2048, half rotation, 2048-point FFT
- 4  – F512, full rotation, 512-point FFT
- 5  – F1024, full rotation, 1024-point FFT
- 6  – F2048, full rotation, 2048-point FFT
- 7  – D512, double rotation, 512-point FFT
- 8  – D1024, double rotation, 1024-point FFT
- 9  – D2048, double rotation, 2048-point FFT

---

### `measure()`

Performs a single polarization measurement.

Returns:

```python
{
    "azimuth": float,        # degrees
    "ellipticity": float,    # degrees
    "S0": float,
    "S1": float,
    "S2": float,
    "S3": float,
    "dop": float,            # degree of polarization
    "dolp": float,           # degree of linear polarization
    "docp": float            # degree of circular polarization
}
```

---

### `close()`

Closes the connection to the device and releases all resources.

```python
pax.close()
```

---

## Exceptions

- `DeviceNotFound`  
  Raised if no PAX1000 device is detected.

- `InitialisationError`  
  Raised if device initialization fails.

---

## Notes

- Only the first detected PAX1000 device is used.
- Returned values are deep-copied to avoid side effects from reused ctypes objects.
- Based on the official Thorlabs ctypes example, adapted for Python 3.
