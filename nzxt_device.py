import logging
import threading
import time

import serial
from serial.tools.list_ports import comports
import usb.core
import usb.util

USB_VID_MICROCHIP = 0x04d8
USB_VID_NZXT = 0x1e71
USB_PID_MCP2200 = 0x00df
USB_PID_X62 = 0x170e

#__ALL__ = [ "NZXTDevice", "NZXTCrashException",
#           USB_VENDOR_NZXT, USB_PRODUCT_X62 ]

def find_kraken():
    # Find the kraken first
    return usb.core.find(idVendor=USB_VID_NZXT,
                         idProduct=USB_PID_X62,
                         find_all=True)

# Now find the grid and hue which are Microchip MCP2200 devices
# http://www.microchip.com/wwwproducts/en/en546923
# http://ww1.microchip.com/downloads/en/DeviceDoc/93066A.pdf
# I can't read/write to these under Windows/PyUSB so use serial
def find_hue_plus():
    rv = []
    for i in comports():
        try:
            if not ((i.vid == USB_VID_MICROCHIP) and
                    (i.pid == USB_PID_MCP2200)):
                next
            logging.info("{} might be a hue+".format(i[0]))
            ser = serial.Serial(i[0], 256000, timeout=1)
            ser.read(16384) # empty buffer
            ser.write([0xc0])
            if array.array('B', ser.read()) != array.array('B', [0x01]):
                next
            ser.write([])
            if array.array('B', ser.read()) != array.array('B', [0x01]):
                next
        except Exception as e:
            logging.exception(e)

class NZXTCrashException(Exception): pass


class NZXTDevice(object):
    def __init__(self, dev):
        self.crashed = threading.Event()
        self.__reader_die = threading.Event()
        self._dev = dev
        self.serial_number = dev.serial_number

        self.txcount = 0
        self.txbytes = 0
        self.txtime = time.time()

        logging.debug("Using USB device. {}".format(dev.__repr__()))
        # Only one configuration on this thing
        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0,0)]

        self._rx = usb.util.find_descriptor(intf,
            custom_match = lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_IN)
        assert self._rx is not None
        logging.debug("RX endpoint {}".format(self._rx.__repr__()))

        self._tx = usb.util.find_descriptor(intf,
            custom_match = lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_OUT)
        assert self._tx is not None
        logging.debug("TX endpoint {}".format(self._tx.__repr__()))

        self._reader = threading.Thread(target=self.readerThread)
        self._reader.name = "reader"
        self._reader.daemon = True
        self._reader.start()

    def exit(self):
        logging.info("Stopping")
        try:
            self.__reader_die.set()
            #self.__reader.join()
        except AttributeError:
            pass

    def write(self, data, debug=False):
        """
        Write one packet to device, padded if necessary
        It seems everything needs padding to 65 bytes apart from 2-byte
        commands
        """
        if len(data) == 2:
            self.__do_write(data, debug=debug)
        else:
            self.__do_write(data + [0x00] * (65-len(data)), debug=debug)

    def __do_write(self, data, retries = 5, debug=False):
        if debug is True:
            logging.debug("TX: {}".format([hex(i) for i in data]))
        for i in range(retries):
            try:
                bytes = self._tx.write(data, timeout=100)
                self.txcount += 1
                self.txbytes += bytes
                return bytes
            except IOError as e:
                #logging.exception(e)
                logging.debug("retrying")
        self.__panic()

    def __panic(self):
        usb.util.dispose_resources(self._dev)
        self.crashed.set()
        logging.info("crashed after {} writes totalling {} bytes"\
                     .format(self.txcount, self.txbytes))
        self.exit()
        raise NZXTCrashException(self.serial_number)


    def readerThread(self, freq=20.0):
        "Read from device in background, freq is in Hz"
        logging.info("Starting reader thread")
        while not self.__reader_die.is_set():
            rv = self.read()
            if rv is not None:
                self.handle_read(rv)
            time.sleep(1.0/freq)

    def read(self):
        "Read one packet from buffer, or None if nothing to read"
        bufsize = 17
        try:
            return self._rx.read(bufsize, timeout=1)
        except usb.core.USBError:
            return None
        except OSError as e:
            #logging.exception(e)
            logging.error("OSException on read")
            return None

    def handle_read(self, data):
        "Handle received data"
        logging.debug("RX: " + [hex(i) for i in data])
