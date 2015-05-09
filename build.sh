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
# copy configuration into $HOME/config
mkdir -f $HOME/config
cp ecamera/config/ecamera.ini $HOME/config
echo
echo make sure the $HOME/ecamera.ini is configured correctly
echo

#
# add the ecamera service
#
echo 'ecamera		30001/tcp   # echelle slitviewer camera' >> /etc/services

#
# copy the OS X daemon startup code and start it.  it will
# start on reboots
#
cp ../ecamera.plist /Library/LaunchDaemons
launchctl /Library/LaunnchDaemons/ecamera.plist start
#launchctl /Library/LaunnchDaemons/ecamera.plist stop

