# Kraken X62

VID: 1e71
PID: 170e

### Status messages

The reply to a `0x01 0x57` command sent by CAM at startup is this:
```
04 48 0a 25 bf 15 a4 5a
```
I have no idea what this means.


At regular intervals (4Hz if no commands are being sent, up to around 17Hz
if you're flooding the device) the Kraken will send an unsolicited message
which looks like this:

```
04 26 08 02 05 09 19 00 00 00 ab 02 00 01 08 1e 00
```

broken down:

```
00 04
01 26 temp. 26 = 42, 27 = 43, 2a=46 = liquid temp in c - 4 degs
02 08 temp decimal (0-9)
03 02 fan rpm msb
04 05 fan rpm lsb
05 09 pump rpm msb
06 19 pump rpm lsb
07 00
08 00
09 00
10 ab
11 02
12 00
13 01
14 08
15 1e - 00 at usb init. Initial lighting?
16 00
```

byte 15 will be 0x1f if you send a `0x01 0xNN` command where NN in [0x54, 0x55, 0x56, 0x5a]
byte 15 will be 0x00 if you send a `0x01 0x58` command

### Fan/pump speed

```
02 4d 00 00 nn	fans speed percent (min 0x19=25%, max 0x64=100%)
02 4d 40 00 nn	pump speed percent (min 0x3c=60%, max 0x64=100%)
```

### Light Control

Does the '02' speed do anything on fixed?
Do the padding RGB vals do anything?


#### Command format

```
02 4c <rw> <0e> <bs> <logo GG RR BB> <ring RR GG BB * 8>
```
r = ring rotation (0=forwards, 1=backwards)
w = device. 0=both, 1=logo, 2=ring, a=ring rotating (alternating wave)
e = effect id
b = bank i.e. for multicolour effects. values seen = 0,2,4
s = speed (0=slow, 4=fast)

For specifying multiple colour banks, send the command multiple times
with the 'b' incrementing each time, specifying the relevant colours with it

Note the logo is specified as GRB whereas the ring uses RGB to specify colour

For ring lighting, sometimes the colours are all used, however some effects
may only use the first (or in the case of 'spectrum wave', will disregard
them all)

#### Effects

| EffectID | Name | Applies to | Colours | Notes
|---|------------------|------|---------|-------
| 0 | Fixed            | Both | 1   |
| 1 | Fading           | Ring |     |
| 2 | Spectrum wave    | Both | 0   |
| 3 | Marquee          | Ring | 1-n |
| 4 | Covering marquee | Ring | 1-n |
| 5 | Alternating wave | Ring | 2   | Can use device 0xa
| 6 | Breathing        | Both | 1-n |
| 7 | Pulse            | Both |     |
| 8 | Tai Chi          | Ring |     | Can't get to work?
| 9 | Water cooler     | Ring | 0   |
|10 | Loading          | Ring | 1   |

### Music

CAM essentially just throws lots of 'fixed' effect commands down to the
Kraken. Some testing shows it's actually possible to flood the Kraken X62
with 500 messages per second on the author's computer. Strangely that's
an exact figure (constant 30,000 +/- 10 per minute). The lights don't update
at that rate however, as flickering is evident.

Here's a dump of "level" from CAM. Trailing zeros skipped.
Note GRB logo colour is same as the last ring (RGB) light

```
               /------\-------------------------------------/------\
02 4c 00 00 02 e5 00 ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 e5 ff
02 4c 00 00 02 b2 00 ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 b2 ff
02 4c 00 00 02 66 00 ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 66 ff
02 4c 00 00 02 ff 00 ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 ff ff
               /------\----------------------------------------------/------\
02 4c 00 00 02 00 3c ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 ff ff 3c 00 ff
```

# Serial Devices

These show up as Microchip MCP2200 devices which have both HID interfaces and
serial port devices.  It's the latter we use to speak to these via a very
similar protocol to the Kraken

It's important to use a bit of software called "Zadig" to change the USB
driver for the HID device to WinUSB, else pyusb doesn't want to talk to them


`0xc0` appears to be a common 'ping' command sent from the host
Commands beginning `0x4n` appear to be 'set' commands
Commands beginning `0x8n` appear to be status requests


## Hue+

Communication appears to be at 256kbps (256000 bps, not base2)

### Status response

The Hue+ responds to `0xc0`with `0x01`
Successful commands return `0x01`
Failed commands return `0x02`

### Firmware update

I managed to capture this process, which is a dead simple 2-step process:

Send the `0x4c` command and receive an `0x01` ack. The LED will blink 1Hz.
Now send the firmware file in 128 byte chunks each preceded by `0xaa`.
Receive an `0x01` response to each chunk.
Zero pad the last chunk.
CAM takes 211s to deliver a 47KB firmware file, the delay is waiting for the acks.

Send the `0x50` command and wait a few minutes for a `0x03` response. Presumably
this reads the file you've just sent and copies it to somewhere non-volatile.


## Grid

The grid really is a pile of crap. It can't keep some fans running below
around 60% without constantly spinning them up and down. It also appears
there is no way to set speeds under what it thinks is 450rpm!

Communication appears to be at 4800bps, or maybe slightly off that since
comms seems unreliable

#### Status response

The Grid responds to `0xc0`with `0x21`
Successful commands return `0x01`
Failed commands return `0x02`

#### Querying

n = channel number

```
send: 84 0n           - get current pwm output (0-2910)
recv: c0 00 00 0b 5c  - 2908

send: 85 0n           - get current power draw (watts)
recv: c0 00 00 00 18  - 2.4W

send: 8a 0n           - get current rpm
recv: c0 00 00 01 c2  - 450rpm
```

Note rpm readings change infrequently and are always rounded to a convenient
value.

#### Setting

n = channel number
v = value (0x00 = off, 0x04 = 20%, 0x0c = 100%)

```
44 0n c0 00 00 0v 00
```
