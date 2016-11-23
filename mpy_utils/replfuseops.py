import errno
import stat
import posix
import fuse
import os

BUFSIZ = 50

class ReplFuseOps(fuse.Operations):
    def __init__(self, remote):
        self.remote = remote
        self.filehandles = []
        self.remote.command("import os")

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        return 0

    def chmod(self, path, mode):
        raise fuse.FuseOSError(errno.EACCES)

    def chown(self, path, uid, gid):
        raise fuse.FuseOSError(errno.EACCES)

    def getattr(self, path, fh=None):
        s = self.remote.function('os.stat', path)
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
        dirents.extend(self.remote.function('os.listdir', path))
        return dirents

    def readlink(self, path):
        return path

    def rmdir(self, path):
        return self.remote.function('os.rmdir', path)

    def mkdir(self, path, mode):
        return self.remote.function('os.mkdir', path)

    def statfs(self, path):
        r = self.remote.function('os.statvfs', path)
        return dict(zip(['f_bsize','f_frsize','f_blocks','f_bfree','f_bavail','f_files','f_ffree','f_favail','f_fsid','f_flag'], r))

    def unlink(self, path):
        return self.remote.function('os.remove', path)

    def rename(self, old, new):
        return self.remote.function('os.rename', old, new)

    # File methods
    # ============

   
    def _open(self, path, mode):
        num = len(self.filehandles)
        self.filehandles.append(self.remote.variable('open', path, mode))
        return num
 
    def open(self, path, flags):
        mode = "rb" if (flags & posix.O_RDONLY) else "rb+"
        return self._open(path, mode)

    def create(self, path, mode, fi=None):
        return self._open(path, "wb")

    def read(self, path, length, offset, fh):
        self.filehandles[fh].method('seek', offset)
        buf = b''
        while len(buf) < length:
            size = length - len(buf) if length - len(buf) < BUFSIZ else BUFSIZ;
            r = self.filehandles[fh].method('read', size)
            if r is None or len(r) == 0: break
            buf += r
            print(len(buf))
        return buf

    def write(self, path, buf, offset, fh):
        length = len(buf)
        self.filehandles[fh].method('seek', offset)
        total = 0
        while total < length:
            size = length - total if length - total < BUFSIZ else BUFSIZ;
            total += self.filehandles[fh].method('write', buf[total:total+size])
        return total

    def flush(self, path, fh):
        return self.filehandles[fh].method('flush')

    def release(self, path, fh):
        return self.filehandles[fh].method('close')

    def fsync(self, path, fdatasync, fh):
        raise fuse.FuseOSError(errno.EACCES)
