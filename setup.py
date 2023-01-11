from setuptools import setup

setup(
    name="mpy-utils",
    version="0.1.13",
    description="MicroPython development utility programs",
    long_description="MicroPython development utility programs",
    url="https://github.com/nickzoic/mpy-utils/",
    author="Nick Moore",
    author_email="nick@zoic.org",
    license="MIT",
    packages=["mpy_utils"],
    scripts=["bin/mpy-fuse", "bin/mpy-upload", "bin/mpy-download", "bin/mpy-sync", "bin/mpy-watch", "bin/mpy-reset"],
    install_requires=["fusepy>=3", "pyserial>=3"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Embedded Systems",
    ],
)
