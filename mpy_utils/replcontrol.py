import serial

class ReplControl(object):
    
  def __init__(self, port='/dev/ttyUSB0', baud=115200, delay=0):
    self.port = serial.Serial(port, baud, timeout=2)
    self.buffer = b""
    self.delay = delay
    self.initialize()
 
  def response(self, end=b"\x04"):
    while True:
      bytes_to_read = self.port.inWaiting()
      self.buffer += self.port.read(bytes_to_read)
      try:
        r, self.buffer = self.buffer.split(end, 1)
        return r
      except ValueError:
        pass
        
  def initialize(self):
    # break, break, reboot, raw mode
    self.port.write(b"\x03\x03\x04\x01");
    while (self.port.read(100)): pass
    #self.port.write(b"import os, sys\r")
    #s = self.port.read(100)
    #if not s.endswith(b"\r\n>>> "): raise("wot")

  def command(self, cmd):
    print(">>> %s" % cmd)
    self.port.write(cmd.encode("ASCII") + b"\x04")
    ret = self.response()
    err = self.response(b"\x04>")

    if ret.startswith(b'OK'):
      if err:
        print("<<< %s" % err)
        return err
      elif len(ret) > 2:
        print("<<< %s" % ret[2:])
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


class ReplControlVariable(object):
 
  counter = 0

  def __init__(self, control, func, *args):
    self.control = control
    self.name = '__v%d' % self.__class__.counter
    self.__class__.counter += 1
    self.control.statement("%s=%s" % (self.name, func), *args)

  def get_name(self):
    return self.name

  def method(self, method, *args):
    return self.control.function("%s.%s" % (self.name, method), *args)
       
  def __del__(self):
    self.control.command("del %s" % self.name)
