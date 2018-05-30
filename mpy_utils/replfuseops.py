import errno
import stat
import posix
import fuse
import os

BUFSIZ = 50


class ReplFuseOps(fuse.Operations):
    def __init__(self, remote, base_path=""):
        self.remote = remote
        self.base_path = base_path
        self.filehandles = []
        self.remote.command("import os")

    # Filesystem methods
    # ==================

    def getattr(self, path, fh=None):
        s = self.remote.function("os.stat", os.path.join(self.base_path, path))
        if type(s) is bytes:
            raise fuse.FuseOSError(errno.ENOENT)

        mode = (stat.S_IFDIR | 0o750) if stat.S_ISDIR(s[0]) else (stat.S_IFREG | 0o640)
        return {
            "st_mode": mode,
            "st_nlink": 2,
            "st_size": s[6],
            "st_uid": os.getuid(),
            "st_gid": os.getgid(),
        }

    def readdir(self, path, fh):
        dirents = [".", ".."]
        dirents.extend(
            self.remote.function("os.listdir", os.path.join(self.base_path, path))
        )
        return dirents

    def readlink(self, path):
        return path

    def rmdir(self, path):
        return self.remote.function("os.rmdir", os.path.join(self.base_path, path))

    def mkdir(self, path, mode):
        return self.remote.function("os.mkdir", os.path.join(self.base_path, path))

    def statfs(self, path):
        r = self.remote.function("os.statvfs", os.path.join(self.base_path, path))
        return {
            "f_bsize": r[0],
            "f_frsize": r[1],
            "f_blocks": r[2],
            "f_bfree": r[3],
            "f_bavail": r[4],
            "f_flag": 0,
        }

    def unlink(self, path):
        return self.remote.function("os.remove", os.path.join(self.base_path, path))

    def rename(self, old, new):
        return self.remote.function(
            "os.rename",
            os.path.join(self.base_path, old),
            os.path.join(self.base_path, new),
        )

    # File methods
    # ============

    def _open(self, path, mode):
        num = len(self.filehandles)
        var = self.remote.variable("open", os.path.join(self.base_path, path), mode)
        self.filehandles.append((var, path))
        return num

    def open(self, path, flags):
        if flags & posix.O_WRONLY:
            mode = "wb"
        elif flags & posix.O_RDWR:
            mode = "rb+"
        else:
            mode = "rb"
        return self._open(path, mode)

    def create(self, path, mode, fi=None):
        return self._open(path, "wb")

    def read(self, path, length, offset, fh):
        self.filehandles[fh][0].method("seek", offset)
        buf = b""
        while len(buf) < length:
            size = length - len(buf) if length - len(buf) < BUFSIZ else BUFSIZ
            r = self.filehandles[fh][0].method("read", int(size))
            if r is None or len(r) == 0:
                break
            buf += r
        return buf

    def write(self, path, buf, offset, fh):
        length = len(buf)
        self.filehandles[fh][0].method("seek", offset)
        total = 0
        while total < length:
            size = length - total if length - total < BUFSIZ else BUFSIZ
            total += self.filehandles[fh][0].method("write", buf[total : total + size])
        return total

    def truncate(self, path, size, fh=None):
        if size == 0:
            fh = self._open(path, "wb")
            self.filehandles[fh][0].method("close")
            self.filehandles[fh] = None
        else:
            # not implemented
            raise fuse.FuseOSError(errno.ENOTSUP)

    def flush(self, path, fh):
        return self.filehandles[fh][0].method("flush")

    def release(self, path, fh):
        self.filehandles[fh][0].method("close")
        self.filehandles[fh] = None

    def fsync(self, path, fdatasync, fh):
        for fh in self.filehandles:
            if fh is not None and fh[1] == path:
                fh[0].method("flush")
