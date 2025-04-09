# interface_exercise

This is a PyQt5-based graphical user interface (GUI) that monitors and controls an embedded system's temperature and voltage readings through serial communication.

## Features

- **Real-time Monitoring**: Displays current temperature and voltage readings.
- **Threshold Settings**: Allows the user to set custom temperature and voltage thresholds.
- **Alert System**: Displays LED-like indicators (green/red) and alerts when readings exceed set thresholds.
- **Serial Communication**: Uses the `pyserial` library to communicate with the embedded system.

## Requirements

- Python 3.x
- PyQt5
- pyserial

Install the required libraries using pip:


```
pip install pyqt5 pyserial
```

## Modify Port

1. **Find the correct port** where your embedded device is connected:

   - On **Windows**, it will usually appear as `COMx` (e.g., `COM3`, `COM4`).
   - On **macOS/Linux**, it might be something like `/dev/tty.usbmodemXXXX` or `/dev/ttyUSB0`.

2. **Update the port in the code**:
   
   In the `SerialReader` class, locate the following line:

   ```
   self.serial = SerialReader(port='/dev/tty.usbmodemXXXX')
   ```

   
## How to Run
```
python interface_exercise.py
   ```
