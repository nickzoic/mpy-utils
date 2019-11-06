import serial
import string
import atexit
import time
import sys
import os
import fcntl


class ReplIOSerial(object):
    def __init__(self, port="/dev/ttyUSB0", baud=115200, delay=0):
        self.port = serial.Serial(port, baud, timeout=2)
        self.delay = delay

        self.port.dtr = 0
        self.port.rts = 0

    def writebytes(self, data):
        self.port.write(data)

    def readbytes(self):
        bytes_to_read = self.port.inWaiting()
        if not bytes_to_read:
            time.sleep(self.delay / 1000.0)
        return self.port.read(bytes_to_read)

    def readall(self):
        return self.port.read_all()

    def flushinput(self):
        return self.port.reset_input_buffer()


class ReplIOFileHandle(object):
    def __init__(self, infh=sys.stdin, outfh=sys.stdout):
        self.infh = infh
        self.outfh = outfh

        # Set input to non-blocking
        fd = self.infh.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def readbytes(self):
        # Just keep trying to read a byte until there's none left to read
        buf = b""
        while True:
            data = self.infh.buffer.read(1)
            if data == None:
                break
            buf += data
        return buf

    def writebytes(self, data):
        self.outfh.buffer.write(data)
        self.outfh.buffer.flush()

    def readall(self):
        return self.readbytes()

    def flushinput(self):
        return self.readbytes()


class ReplControl(object):
    def __init__(self, io, delay=0, debug=False, reset=True):
        self.io = io
        self.buffer = b""
        self.delay = delay
        self.debug = debug

        self.initialize()

        if reset:
            atexit.register(self.reset)

    def response(self, end=b"\x04"):
        while True:
            self.buffer += self.io.readbytes()
            try:
                r, self.buffer = self.buffer.split(end, 1)
                return r
            except ValueError:
                pass

    def initialize(self):
        # break, break, raw mode, reboot
        self.io.writebytes(b"\x03\x03\x01\x04")
        start = time.time()
        while True:
            resp = self.io.readall()
            if resp.endswith(b"\r\n>"):
                break
            elif time.time() - start > 3:
                if self.debug:
                    self.log("Forcefully breaking the boot.py")
                self.io.writebytes(b"\x03\x03\x01\x04")
            time.sleep(self.delay / 1000.0)
        self.io.flushinput()

    def reset(self):
        self.io.writebytes(b"\x02\x03\x03\x04")

    def command(self, cmd):
        if self.debug:
            self.log(">>> %s" % cmd)
        self.io.writebytes(cmd.encode("ASCII") + b"\x04")
        time.sleep(self.delay / 1000.0)
        ret = self.response()
        err = self.response(b"\x04>")

        if ret.startswith(b"OK"):
            if err:
                if self.debug:
                    self.log("<<< %s" % err)
                return err
            elif len(ret) > 2:
                if self.debug:
                    self.log("<<< %s" % ret[2:])
                try:
                    return eval(ret[2:], {"__builtins__": {}}, {})
                except SyntaxError as e:
                    return e
            else:
                return None

    def statement(self, func, *args):
        return self.command(func + repr(tuple(args)))

    def function(self, func, *args):
        command = "print(repr(%s))" % (func + repr(tuple(args)))
        return self.command(command)

    def variable(self, func, *args):
        return ReplControlVariable(self, func, *args)

    def log(self, msg):
        print(msg, file=sys.stderr)


class ReplControlVariable(object):

    names = [
        "_%s%s" % (x, y) for x in string.ascii_lowercase for y in string.ascii_lowercase
    ]

    def __init__(self, control, func, *args):
        self.control = control
        self.name = self.__class__.names.pop(0)
        self.control.statement("%s=%s" % (self.name, func), *args)

    def get_name(self):
        return self.name

    def method(self, method, *args):
        return self.control.function("%s.%s" % (self.name, method), *args)

    def __del__(self):
        self.control.command("del %s" % self.name)
        self.__class__.names.append(self.name)
