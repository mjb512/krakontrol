import array
import colorsys
import logging
import time

import usb.core
import threading
import openhwmon
import subprocess

from nzxt_device import NZXTDevice, NZXTCrashException

logger = logging.getLogger(__name__)

# USB packet padding. Will be truncated by tx
padding = [0x00] * 65

RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
WHITE = (255,255,255)
BLACK = (0,0,0)

POWERSHELL = "C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe"

def flatten(list_of_colours):
    "Take a list of RGB tuples, flatten into a single list"
    return [i for sublist in list_of_colours for i in sublist]

def rotate(list_to_rotate, turns):
    "Rotate a list"
    return list_to_rotate[-turns:] + list_to_rotate[:-turns]

def interpolate(t1, t2):
    "Return a tuple half way between 2 given ones"
    return tuple(int(sum(x)/2) for x in zip(t1, t2))


class KrakenManager(object):
    devices = {}

    def __init__(self):
        #self.reset(1)
        try:
            self.__my_init()
        except NZXTCrashException as e:
            serial = e.args[0]
            logging.error("Crashed trying to init {}".format(serial))
            self.reset(serial)
            self.__my_init()

        self._monitor_die = threading.Event()
        self._monitor = threading.Thread(target=self.monitorThread)
        self._monitor.name = "monitor"
        self._monitor.daemon = True
        self._monitor.start()

        self.openhwmon = openhwmon.OpenHardwareMonitor()

    @property
    def cputemp(self):
        return self.openhwmon.cputemp

    def __my_init(self):
        "Fires up the Kraken!"
        found = usb.core.find(idVendor= 0x1e71,
                              idProduct=0x170e,
                              find_all=True)
        for i in found:
            logging.info("Mgr found device {}".format(i.serial_number))
            self.devices[i.serial_number] = Kraken(i)

    def restart(self, serial):
        "Drop the device, reset the hardware, and re-add"
        del(self.devices[serial])
        self.reset(serial)
        dev = usb.core.find(idVendor=0x1e71, serial_number=serial)
        try:
            self.devices[serial] = Kraken(dev)
        except Exception:
            return None
        return True

    def reset(self, serial):
        "Launch powershell to reset the device"
        logging.info("Resetting {}".format(serial))
        rv = subprocess.call([POWERSHELL, "-ExecutionPolicy","ByPass",
                     ". \"./reset.ps1\";", \
                     "&resetDevice('USB\\VID_1E71&PID_170E\\6D834660505')"])
        logging.info("reset rv={}".format(rv))
        return rv

    def status(self):
        print("Status:")
        for i in self.devices.keys():
            print(i)

    def exit(self):
        for i in self.devices.items():
            i.exit()
        self._monitor_die.set()
        self._cputemp_die.set()

    def monitorThread(self, freq=20.0):
        "React to any devices marked as crashed"
        logging.debug("monitorThread starting")
        while not self._monitor_die.is_set():
            for i in self.devices:
                if self.devices[i].crashed.is_set():
                    logging.warning("crashed device {} found. Resetting"\
                                    .format(i))
                    while True:
                        if self.restart(i): break
            time.sleep(1.0/freq)

    def whoosh(self, id=None):
        try:
            if id:
                return self.devices[id].whoosh()

            for i in self.devices.values():
                i.whoosh()
        except NZXTCrashException:
            logging.error("Crash")
            return None

    def run(self):
        "TODO: Fix this shit algo!!!"
        tmin = 50
        tmax = 70
        while True:
            time.sleep(1)
            t = self.cputemp
            if t is None: next
            logging.debug(self.cputemp)

            if t < tmin:
                pump = 60
                fans = 20
            elif t > tmax:
                pump = 100
                fans = 100
            else:
                pump = int(100*(t-tmin)/(tmax-tmin))
                fans = int(100*(t-tmin)/(tmax-tmin))
            if t > tmin:
                hue = 0.33333 * (t-tmin)/(65-tmin)
            else: hue = 0
            # give a proportional colour between green and red
            col = colorsys.hsv_to_rgb(0.33333 - hue, 1, 1)

            for i in self.devices.values():
                i.fan = fans
                i.pump = pump
                i.ring_setcol(tuple(round(i*255) for i in col))


class Kraken(NZXTDevice):
    def __init__(self, dev):
        self._temp = None
        self._fan = None
        self._fanrpm = None
        self._pump = None
        self._pumprpm = None
        self._status = None

        NZXTDevice.__init__(self, dev)

        self.pump = 60
        self.fan = 30

    def handle_read(self, data):
        if sum(data[-8:]) == 0:
            self.parse_1_57(data)
        else:
            self.parse_status(data)

    @property
    def status(self):
        return self._status

    @property
    def temp(self):
        return self._temp

    @property
    def fanrpm(self):
        return self._fanrpm

    @property
    def fan(self):
        return self._fan

    @fan.setter
    def fan(self, percent):
        "Set fans to N percent. HW minimum is 25%"
        assert isinstance(percent, int)
        assert 0 <= percent <= 100
        if percent < 25: percent = 25
        if percent == self.fan: return
        logging.info("Setting fan(s) to {}%".format(percent))
        self.write([0x02, 0x4d, 0x00, 0x00, percent])
        self._fan = percent

    @property
    def pumprpm(self):
        return self._pumprpm

    @property
    def pump(self):
        return self._pump

    @pump.setter
    def pump(self, percent):
        "Set pump to N percent. HW minimum is 60%"
        assert isinstance(percent, int)
        assert 0 <= percent <= 100
        if percent < 60: percent = 60
        if percent == self.pump: return
        logging.info("Setting pump to {}%".format(percent))
        self.write([0x02, 0x4d, 0x40, 0x00, percent])
        self._pump = percent

    def parse_1_57(self, p):
        "Parse response to [1,0x57]"
        expected = array.array('B',
            [0x04, 0x48, 0x0a, 0x25, 0xbf, 0x15, 0xa4, 0x5a] + [0x00] * 9)
        if p == expected:
            logging.debug("Normal [0x01, 0x57] response received")
        else:
            logging.info("exp: " + [hex(i) for i in expected])
            logging.info("got: " + [hex(i) for i in p])

    def parse_status(self, p):
        "Parse status line"
        if p[0]  != 0x04: print("*** p[{}] == {}".format(0,p[0]))
        self._temp = p[1] + 4 + (p[2] / 10.0)
        self._fanrpm = p[3] * 256 + p[4]
        self._pumprpm = p[5] * 256 + p[6]
        if p[7]  != 0x00: print("*** p[{}] == {}".format(7, hex(p[7])))
        if p[8]  != 0x00: print("*** p[{}] == {}".format(8, hex(p[8])))
        if p[9]  != 0x00: print("*** p[{}] == {}".format(9, hex(p[9])))
        if p[10] != 0xab: print("*** p[{}] == {}".format(10,hex(p[10])))
        if p[11] != 0x02: print("*** p[{}] == {}".format(11,hex(p[11])))
        if p[12] != 0x00: print("*** p[{}] == {}".format(12,hex(p[12])))
        if p[13] != 0x01: print("*** p[{}] == {}".format(13,hex(p[13])))
        if p[14] != 0x08: print("*** p[{}] == {}".format(14,hex(p[14])))
        if p[15] == 0:
            self._status = "uninitialised"
        elif p[15] == 0x1e:
            self._status = "normal"
        elif p[15] == 0x1f:
            self._status = "0x01 0x56 has been issued"
        else:
            print("*** p[{}] == {}".format(15,hex(p[15])))
            st = "?"
        if p[16] != 0x00: print("*** p[{}] == {}".format(16,p[16]))

        logging.debug("Temp: {}, Fan: {} rpm, Pump: {} rpm, State: {}"\
            .format(self.temp, self.fanrpm, self.pumprpm, self.status))

    def ring_setcol(self, rgb):
        "Set the ring a static colour"
        header = [0x02, 0x4c, 0x02, 0x00, 0x02]
        self.write(header + [i for i in rgb]*9)

    def logo_setcol(self, rgb):
        "Set the logo a static colour"
        header = [0x02, 0x4c, 0x01, 0x00, 0x02]
        self.write(header + list(rgb))

    def whoosh2(self):
        while True:
            for i in range(100):
                self.fan = i

    def whoosh(self):
        self.write([1,0x57])
        i = interpolate
        order = [RED, BLACK, GREEN, BLACK, BLUE, BLACK, WHITE, BLACK]
        #order = [RED, i(RED,GREEN), GREEN, i(GREEN,BLUE), BLUE,
        #         i(BLUE,WHITE), WHITE, i(WHITE,RED)]

        logo = [0x14, 0xb0, 0x58]
        #ring = [0xb0, 0x14, 0x58] * 8
        ring = flatten(order)
        lights = { 'both':0, 'logo':1, 'ring':2 }
        effect = {
            'fixed': 0,
            'ring fading': 1,
            'spectrum wave': 2,
            'ring marquee': 3,
            'ring covering marquee': 4,
            'ring alternating wave': 5, # lights can be 0x0a for 'rotating'
            'breathing': 6,
            'pulse': 7,
            'tai chi': 8, # ??? crash?
            'ring water cooler': 9,
            'ring loading': 10
        }
        #l=0x00 # lights['logo']
        #e=2 # effect
        #d=[2,0x4c,l,e,0x02]
        #self.write(d + logo + ring)
        #d=[2,0x4c,l,e,0x22]
        #self.write(d + [255,0,0] + flatten(rotate(order,2)))
        ##d=[2,0x4c,l,e,0x42]
        ##self.write(d + [0,0,255] + flatten(rotate(order,4)))
        #self.write([1,0x57])

        #time.sleep(10);import sys;sys.exit(1)
        self.write([0xc0, 0xc0])
        time.sleep(3)
        header = [0x02, 0x4c, lights['both'], 0x00, 0x00]
        while True:
            for i in range(8):
                p = flatten(rotate(order, i))
                #data = header + list(BLUE) + p
                data = header + list(order[i%4 * 2]) + p
                self.write(data)
                time.sleep(5)


# When it's crashed, resetting doesn't work - need to reset parent hub
# or controller, which we can't do through python.
#
#  Get-CimInstance Win32_PnPEntity | where DeviceID -match '170e'
#
#  (Get-CimInstance Win32_PnPEntity | where DeviceID -match 'VID_1E71&PID_170E' | where Service -match 'HidUsb').PNPDeviceID
#USB\VID_1E71&PID_170E\6D834660505
#  Disable-PnpDevice -InstanceId $id -Confirm:$false

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    try:
        a = KrakenManager()
        a.status()
    #time.sleep(0.5)
    #a.pump = 60
    #a.fan = 30
        #a.run()
        #while True:
        a.whoosh()
        time.sleep(3)
        a.exit()
    except KeyboardInterrupt:
        print(threading.enumerate())
