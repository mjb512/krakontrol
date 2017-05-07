# krakontrol
Alternative control software for NZXT's Kraken AIO cooler

# WARNING!

This software is incomplete, unsupported and MAY BRICK YOUR HARDWARE!
Also, it doesn't actually do much in its current state.

For now it should be used as reading material only!

# Requirements
LibUSB
python
pyusb (pip install pyusb)

Zadig. Change MCP2200 USB Serial Port Emulator (Interface 2) to use WinUSB instead of HidUsb


# TODO

* Grid+
 * V2 hardware examination
   * Connections to the MCP2200
   * Sniff comms to the STM8S5K6s (serial, i2c...?)

* Hue+
  * Change bus config from 2+2 to something else
