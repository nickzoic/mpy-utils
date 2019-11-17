# mpy-utils v0.1.10

Utility programs for Micropython ...

* bin/mpy-upload : copy files in to a device using only the REPL.
* bin/mpy-sync : copy whole directory structure
* bin/mpy-fuse : mount a device into the filesystem using FUSE ...
* bin/mpy-watch : watch a directory for changes and send the diffs

[This package is also available through PyPI](https://pypi.python.org/pypi/mpy-utils/)

## Using serial ports directly

All four utilities by default will connect directly to /dev/ttyUSB0 at 115200 baud.

These can be overridden with the `-port` and `--baud` parameters.

## Using serial ports attached to stdin/stdout

[picocom](https://github.com/npat-efault/picocom) is a terminal emulator program that allows you to specify external file transfer programs. The external program is launched with the serial port attached to stdin and stdout.

The mpy-utils have a `--pipe` option which enables this usage.

eg. The following command will set mpy-sync as the picocom file-send program.

```
picocom -b 115200 -s "mpy-sync --pipe --reset" /dev/ttyUSB0
```

From within picocom, hit ctrl-A ctrl-S to initiate file-send mode. Type in the filename to send (tab-completion seems to be available), and hit enter. The file will be sent via mpy-sync, and you'll be returned to picocom.

You can also specify the filenames on the picocom/mpy-sync command-line, and from picocom, just his ctrl-A ctrl-S and enter. No filenames needed.

## Submitting Pull Requests

Before submitting a pull request, please add yourself to the list of contributors below,
and install [black](https://github.com/ambv/black) so you can reformat your code using
the following command:

```
black *.py bin/* mpy_utils/*.py
```

This will hopefully prevent me from ever having to think about source code formatting again.

## CONTRIBUTORS

* [Nick Moore](https://github.com/nickzoic)
* [Paul Dwerryhouse](https://github.com/pdwerryhouse)
* [Umut Karcı](https://github.com/Cediddi)
* [Eric Poulsen](https://github.com/MrSurly)
* [Jeff Gough](https://github.com/jeffmakes)

