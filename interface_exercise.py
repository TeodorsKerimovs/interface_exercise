import sys
import threading
import serial
import time

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from PyQt5.QtGui import QPixmap, QPainter, QColor

def create_led_icon(color, size=20):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.black)
    painter.drawEllipse(0, 0, size-1, size-1)
    painter.end()
    return pixmap

from PyQt5.QtWidgets import QCheckBox


class SerialReader(QObject):
    data_received = pyqtSignal(str)

    def __init__(self, port='COM3', baudrate=115200):
        super().__init__()
        self.ser = serial.Serial(port, baudrate, timeout=10)
        self.running = False
        self.send_command("TEMPERATURE_ON")
        self.send_command("VOLTAGE_ON")

    def start(self):
        self.running = True
        threading.Thread(target=self.read_loop, daemon=True).start()

    def stop(self):
        self.running = False
        if self.ser.is_open:
            self.ser.close()

    def read_loop(self):
        while self.running:
            if self.ser.in_waiting:
                line = self.ser.readline().decode(errors='ignore').strip()
                self.data_received.emit(line)
            time.sleep(0.1)

    def send_command(self, command):
        if self.ser.is_open:
            self.ser.write((command + '\r').encode())

class MonitorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.serial = SerialReader(port='/dev/tty.usbmodem11403')
        self.serial.data_received.connect(self.handle_data)
        self.serial.start()
        
    def toggle_temperature(self, checked):
        if checked:
            self.serial.send_command("TEMPERATURE_ON")
        else:
            self.serial.send_command("TEMPERATURE_OFF")

    def toggle_voltage(self, checked):
        if checked:
            self.serial.send_command("VOLTAGE_ON")
        else:
            self.serial.send_command("VOLTAGE_OFF")

    def init_ui(self):
        self.setWindowTitle("Embedded Monitor")

        # Labels for displaying real-time values
        self.temp_label = QLabel("Temperature: -- °C")
        self.volt_label = QLabel("Voltage: -- V")

        self.temp_led = QLabel()
        self.volt_led = QLabel()
        self.temp_led.setPixmap(create_led_icon("gray"))
        self.volt_led.setPixmap(create_led_icon("gray"))

        # Layouts
        layout = QVBoxLayout()

        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_led)
        layout.addLayout(temp_layout)

        volt_layout = QHBoxLayout()
        volt_layout.addWidget(self.volt_label)
        volt_layout.addWidget(self.volt_led)
        layout.addLayout(volt_layout)

        # Toggle switches
        self.temp_toggle = QCheckBox("Temperature Monitoring")
        self.volt_toggle = QCheckBox("Voltage Monitoring")

        self.temp_toggle.setChecked(True)
        self.volt_toggle.setChecked(True)
        self.temp_toggle.toggled.connect(self.toggle_temperature)
        self.volt_toggle.toggled.connect(self.toggle_voltage)
        
        # Add toggles to layout
        layout.addWidget(self.temp_toggle)
        layout.addWidget(self.volt_toggle)

        # Threshold input
        self.temp_thresh_input = QLineEdit()
        self.volt_thresh_input = QLineEdit()

        # Separate Set Buttons for Temp and Volt
        self.temp_set_button = QPushButton("Set Temperature Threshold")
        self.volt_set_button = QPushButton("Set Voltage Threshold")

        # Layout for Thresholds and Buttons
        thresh_layout = QHBoxLayout()
        thresh_layout.addWidget(QLabel("Temp Threshold:"))
        thresh_layout.addWidget(self.temp_thresh_input)
        thresh_layout.addWidget(self.temp_set_button)

        volt_thresh_layout = QHBoxLayout()
        volt_thresh_layout.addWidget(QLabel("Volt Threshold:"))
        volt_thresh_layout.addWidget(self.volt_thresh_input)
        volt_thresh_layout.addWidget(self.volt_set_button)

        layout.addLayout(thresh_layout)
        layout.addLayout(volt_thresh_layout)

        self.setLayout(layout)

        self.temp_set_button.clicked.connect(self.send_temperature_threshold)
        self.volt_set_button.clicked.connect(self.send_voltage_threshold)

    def handle_data(self, msg):
        print("Received:", msg)
        try:
            # Initialize variables for both temperature and voltage
            temp_val = temp_thresh = temp_status = None
            volt_val = volt_thresh = volt_status = None

            # Split the message into parts based on semicolon
            parts = msg.split(";")

            # Sorry for this parsing, there was not time
            # Parse temperature info if present
            if "temperature_measured" in msg:
                temp_val = float(parts[0].split("=")[1]) if len(parts) > 0 else None
                temp_thresh = float(parts[1].split("=")[1]) if len(parts) > 1 else None
                temp_status = parts[2].split("=")[1].strip() if len(parts) > 2 else None

                if "voltage_measured" in msg:
                    volt_val = float(parts[3].split("=")[1]) if len(parts) > 3 else None
                    volt_thresh = float(parts[4].split("=")[1]) if len(parts) > 4 else None
                    volt_status = parts[5].split("=")[1].strip() if len(parts) > 5 else None
                    
            # Parse voltage info if present
            elif "voltage_measured" in msg:
                volt_val = float(parts[0].split("=")[1]) if len(parts) > 0 else None
                volt_thresh = float(parts[1].split("=")[1]) if len(parts) > 1 else None
                volt_status = parts[2].split("=")[1].strip() if len(parts) > 2 else None



            # Update UI
            if temp_val is not None:
                self.temp_label.setText(f"Temperature: {temp_val:.2f} °C (Threshold: {temp_thresh:.2f}) [{temp_status}]")
                self.temp_led.setPixmap(create_led_icon("red" if temp_status == "ALERT" else "green"))

            if volt_val is not None:
                self.volt_label.setText(f"Voltage: {volt_val:.2f} V (Threshold: {volt_thresh:.2f}) [{volt_status}]")
                self.volt_led.setPixmap(create_led_icon("red" if volt_status == "ALERT" else "green"))

        except Exception as e:
            print("Error parsing message:", e)

    def send_temperature_threshold(self):
        try:
            # Retrieve and send the temperature threshold
            t_thresh = float(self.temp_thresh_input.text())
            self.serial.send_command(f"TEMPERATURE_SET_THRESHOLD={int(t_thresh * 1000)}")  # In milli-degrees
            QMessageBox.information(self, "Temperature Threshold Set", "Temperature threshold has been set.")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric temperature threshold.")

    def send_voltage_threshold(self):
        try:
            # Retrieve and send the voltage threshold
            v_thresh = float(self.volt_thresh_input.text())
            self.serial.send_command(f"VOLTAGE_SET_THRESHOLD={int(v_thresh * 1000)}")  # In milli-volts
            QMessageBox.information(self, "Voltage Threshold Set", "Voltage threshold has been set.")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric voltage threshold.")



    def raise_alert(self, temp_status, volt_status):
        alert_msg = "Alert!\n"
        if temp_status == "ALERT":
            alert_msg += "Temperature exceeds threshold!\n"
        if volt_status == "ALERT":
            alert_msg += "Voltage exceeds threshold!"

        QMessageBox.critical(self, "ALERT", alert_msg)

    def closeEvent(self, event):
        self.serial.stop()
        event.accept()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MonitorApp()
    window.resize(500, 150)
    window.show()
    sys.exit(app.exec_())


# sudo chmod 666 /dev/tty.usbmodem11403
# python interface_exercise.py