from nzxt_device import NZXTDevice, NZXTCrashException

class HuePlus(NZXTDevice):
    def __init__(self, dev):
        NZXTDevice.__init__(self, dev)
