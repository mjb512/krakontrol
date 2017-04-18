VID: 1e71
PID 170e

Received
========

`04 26 08 02 05 09 19 00 00 00 ab 02 00 01 08 1e 00`

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


Pump
====

02 4d 40 00 3c	pump fixed 60%
02 4d 40 00 46	pump fixed 70%
02 4d 40 00 64	pump fixed 100%
02 4d 40 00 4c	pump silent

Fans
====

02 4d 00 00 19	fans fixed 25%
02 4d 00 00 1e	fans fixed 30%
02 4d 00 00 64	fans fixed 100%

Light Examples
==============

Logo off, ring green
```
02 4c 01 00 02 00 00 00 ( 00 00 ff ) * 8
02 4c 02 00 02 00 00 00 ( 28 ea 1e ) * 8
```

Logo on blue, ring green
```
02 4c 01 00 02 00 00 ff ( 00 00 ff ) * 8
02 4c 02 00 02 ea 28 1e ( 28 ea 1e ) * 8
```

Logo
====

Logo f6110a
```
02 4c 01 00 02 11 f6 0a ( f6 11 0a ) * 8
```

Logo breathing f41c06
```
02 4c 01 06 02 1c f4 06 ( f4 1c 06 ) * 8  = mid speed
02 4c 01 06 04 1c f4 06 ( f4 1c 06 ) * 8  = fast speed
02 4c 01 06 00 1c f4 06 ( f4 1c 06 ) * 8  = slow speed
```

Logo breathing f41c06 + 24ef08 + ffb900
```
02 4c 01 06 00 1c f4 06 ....
02 4c 01 06 20 ef 24 08 ( 24 ef 08 ) * 8
02 4c 01 06 40 b9 ff 00 ( ff b9 00 ) * 8
```

Fading RGB
```
02 4c 01 01 02 00 ff 00 ( ff 00 00 ) * 8
02 4c 01 01 22 ff 00 00 ( 00 ff 00 ) * 8
02 4c 01 01 42 00 00 ff ( 00 00 ff ) * 8
```

Pulse red
```
02 4c 01 07 02 00 ff 00 ( ff 00 00 ) * 8
```

Music - Level
```
               /------\-------------------------------------/------\
02 4c 00 00 02 e5 00 ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 e5 ff
02 4c 00 00 02 b2 00 ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 b2 ff
02 4c 00 00 02 66 00 ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 66 ff
02 4c 00 00 02 ff 00 ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 ff ff
```

```
02 4c 00 00 02 00 3c ff ff 00 00 ff a2 00 ff ff 00 00 ff 00 00 ff ff 3c 00 ff
```

Music sync
```
02 4c 00 00 02 e5 00 ff ( 00 e5 ff) *
```

Ring
====

Ring marquee b01458
```
02 04c 02 03 02 14 b0 58 ( b0 14 58 ) * 8
```

Covering marquee
```
02 4c 02 04 02 00 00 ff ( 00 00 ff ) * 8
02 4c 02 04 22 ff 00 00 ( 00 ff 00 ) * 8
```

Spectrum wave
```
02 4c 02 02 02 00 00 ff ( 00 00 ff ) * 8
02 4c 02 02 00 ... Slow
02 4c 02 02 04 ... fast
02 4c 12 02 02 ... mid backwards
```

Alternating wave
```
02 4c 02 05 02 col1
02 4c 02 05 22 col2

02 4c 0a 05 02 col1 - moving
02 4c 0a 05 22 col2

            x0 ... slow
            x4 ... fast
```

Tai Chi
```
02 4c 02 08 xx
```

Water Cooler
```
02 4c 02 09 02 blue
```

Loading
```
02 4c 02 0a 02 ...col
```


Startup
=======

```
<-- 04 1a 09 01 da 06 f1 00 00 00 ab 02 00 01 08 1e 00 (normal)

--> URB setup. GET DESCRIPTOR 0x03
<-- String: 6D834660505
<-- Status success
--> 01 57
<-- 04 48 0a 25 bf 15 a4 5a

--> 02 4c 00 00 02 00 00 ff ( 00 00 ff ) * 8  (both on blue?)
( probe for serial, mfg, etc)
--> 02 4d 00 00 19 (fan 25%)
--> 02 4d 40 00 3c (pump 60%)
```
