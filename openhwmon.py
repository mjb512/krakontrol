import logging
import threading
import time
import pythoncom
import wmi

class OpenHardwareMonitor(object):
    def __init__(self):
        self.cputemp = None
        self._cputemp_die = threading.Event()
        self._cputemp = threading.Thread(target=self.cpuTempMonitorThread)
        self._cputemp.name = "cputemp"
        self._cputemp.daemon = True
        self._cputemp.start()

    def exit(self):
        self._cputemp_die.set()

    def cpuTempMonitorThread(self, freq=1.0):
        "Keep cpu temperature updated"
        pythoncom.CoInitialize()
        try:
            w = wmi.WMI(namespace="root\OpenHardwareMonitor")
            while not self._cputemp_die.is_set():
                self.cputemp = w.Sensor(Name='CPU Package',
                                        SensorType='Temperature')[0].Value
                time.sleep(1.0/freq)
        finally:
            pythoncom.CoUninitialize()

if __name__ == '__main__':
    o = OpenHardwareMonitor()
    while True:
        print(o.cputemp)
        time.sleep(1)
