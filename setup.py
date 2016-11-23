from setuptools import setup

setup(
  name='mpy-utils',
  version='0.1',
  description='MicroPython development utility programs',
  url='http://github.com/nickzoic/mpy-utils/',
  author='Nick Moore',
  author_email='nick@zoic.org',
  license="MIT",
  packages=["mpy_utils"],
  scripts=["bin/mpy-fuse"],
  install_requires=[
    'fusepy>=2',
    'pyserial>=3',
  ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3 :: Only',
    'Topic :: Software Development :: Embedded Systems',
  ],
)
