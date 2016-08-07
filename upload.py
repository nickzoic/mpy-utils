#!/usr/bin/env python

import serial
import time
from sys import argv

port = serial.Serial("/dev/ttyUSB0", 115200)

for fn in argv[1:]:
  fh = open(fn, "r")

  port.write('_fh = open(%s, "w")\r' % repr(fn))

  while True:
    s = fh.read(50)
    if len(s) == 0: break
    port.write("_fh.write(%s)\r" % repr(s))
    time.sleep(0.1)

  port.write('_fh.close()\r')

port.close()
