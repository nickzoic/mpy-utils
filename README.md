# mpy-utils v0.1.7

Utility programs for Micropython ...

* bin/mpy-upload : copy files in to a device using only the REPL.
* bin/mpy-sync : copy whole directory structure
* bin/mpy-fuse : mount a device into the filesystem using FUSE ...
* bin/mpy-watch : watch a directory for changes and send the diffs

[This package is also available through PyPI](https://pypi.python.org/pypi/mpy-utils/)

## Submitting Pull Requests

Before submitting a pull request, please install [black](https://github.com/ambv/black)
and reformat your code using the following command:

```
black *.py bin/* mpy_utils/*.py
```

This will hopefully prevent me from ever having to think about source code formatting again.
