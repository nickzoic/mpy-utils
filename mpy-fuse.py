#!/usr/bin/env python3

import os
import sys
import errno
import argparse
import serial
import stat
import posix
import fuse

parser = argparse.ArgumentParser(
    description="FUSE mount a device using only the REPL"
)
parser.add_argument('--port', default='/dev/ttyUSB0', help='serial port device')
parser.add_argument('--baud', default=115200, type=int, help='port speed in baud')
parser.add_argument('--delay', default=100.0, type=float, help='delay between lines (ms)')
parser.add_argument('mount_point')
args = parser.parse_args()

port = serial.Serial(args.port, args.baud, timeout=2)

BUFSIZ = 50

def remote_initialize():
    port.write(b"\x04");
    while (port.read(100)): pass
    port.write(b"import os, sys\r")
    s = port.read(100)
    if not s.endswith(b"\r\n>>> "): raise("wot")

def safe_eval(s):
    try:
        return eval(s, {"__builtins__": {}}, {})
    except SyntaxError as e:
        print("Got %s" % e)

def remote_command(command):
    port.write(b"try: print(repr(%s))\rexcept Exception as e: print(b'!'+repr(e))\r\r" % command)
    port.readline()
    port.readline()
    port.readline()
    retn = port.readline()
    if retn.startswith(b'!'):
        return retn[1:]
    else:
        return safe_eval(retn)

def remote_function(func, *args):
    command = func + repr(tuple(args)).encode("ASCII")
    return remote_command(command)

def remote_filehandle(fh, func, *args):
    command = b"_fh%d=" % fh + func + repr(tuple(args)).encode("ASCII")
    port.write(command + b"\r")
    port.readline()

class MicroPythonOps(fuse.Operations):
    def __init__(self):
        remote_initialize()
        print("READY")
        self.fh_count = 0

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        return 0

    def chmod(self, path, mode):
        raise fuse.FuseOSError(errno.EACCES)

    def chown(self, path, uid, gid):
        raise fuse.FuseOSError(errno.EACCES)

    def getattr(self, path, fh=None):
        s = remote_function(b'os.stat', path)
        if type(s) is bytes:
           raise fuse.FuseOSError(errno.ENOENT)

        mode = (stat.S_IFDIR | 0o755) if stat.S_ISDIR(s[0]) else (stat.S_IFREG | 0o644);
        return {
          'st_mode': mode,
          'st_nlink': 2,
          'st_size': s[6] or 4096,
          'st_uid': os.getuid(),
          'st_gid': os.getgid()
        }

    def readdir(self, path, fh):
        dirents = ['.', '..']
        dirents.extend(remote_function(b'os.listdir', path))
        return dirents

    def readlink(self, path):
        return path

    def rmdir(self, path):
        return remote_function(b'os.rmdir', path)

    def mkdir(self, path, mode):
        return remote_function(b'os.mkdir', path)

    def statfs(self, path):
        r = remote_function(b'os.statvfs', path)
        return dict(zip(['f_bsize','f_frsize','f_blocks','f_bfree','f_bavail','f_files','f_ffree','f_favail','f_fsid','f_flag'], r))

    def unlink(self, path):
        return remote_function(b'os.remove', path)

    def rename(self, old, new):
        return remote_function(b'os.rename', old, new)

    # File methods
    # ============

    def open(self, path, flags):
        print("open %s %s" % (path, flags))
        self.fh_count += 1
        mode = "rb" if (flags & posix.O_RDONLY) else "rb+"
        remote_filehandle(self.fh_count, b'open', path, mode)
        return self.fh_count

    def create(self, path, mode, fi=None):
        print("create %s %s" % (path, mode))
        self.fh_count += 1
        remote_filehandle(self.fh_count, b'open', path, "wb")
        return self.fh_count

    def read(self, path, length, offset, fh):
        remote_function(b'_fh%d.seek' % fh, offset)
        buf = b''
        while len(buf) < length:
            size = length - len(buf) if length - len(buf) < BUFSIZ else BUFSIZ;
            r = remote_function(b'_fh%d.read' % fh, size)
            if r is None or len(r) == 0: break
            buf += r
            print(len(buf))
        return buf

    def write(self, path, buf, offset, fh):
        length = len(buf)
        remote_function(b'_fh%d.seek' % fh, offset)
        total = 0
        while total < length:
            size = length - total if length - total < BUFSIZ else BUFSIZ;
            total += remote_function(b'_fh%d.write' % fh, buf[total:total+size])
        return total

    def flush(self, path, fh):
        return remote_command(b'_fh%d.flush()' % fh)

    def release(self, path, fh):
        return remote_command(b'_fh%d.close()' % fh)

    def fsync(self, path, fdatasync, fh):
        raise fuse.FuseOSError(errno.EACCES)
        return self.flush(path, fh)


def main(mount_point):
    fuse.FUSE(
        operations=MicroPythonOps(),
        fsname="mpy-fuse:%s" % args.port,
        mountpoint=mount_point,
        nothreads=True,
        foreground=True
    )

if __name__ == '__main__':
    main(args.mount_point)
