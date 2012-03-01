#!/bin/sh
. .ENV
port selfupdate
port install cfitsio curl curl-ca-bundle py27-distribute python27 python_select readline swig swig-python
port select --set python python27
ln -sf /opt/local/bin/pip-2.7 /opt/local/bin/pip
pushd .
cd ccd
make 
make install
make clean
popd
cd libusb
./build.sh
popd
pip install pyfits
pip install numpy
#
# If packages already installed, run these commands
# instead:
#
# pip install --upgrade pyfits
# pip install --upgrade numpy
#
#
# now build the camera interface
#
pushd .
cd apogee
make
popd
#
#
echo setup the /Library/StartupDaemons and the /etc/services file
#

