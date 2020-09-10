#
# APOGEE makefile for linux
# $Id: Makefile.svr4,v 1.4 2004/02/15 07:34:43 rfactory Exp $
#
#/opt/apogee/lib/libcurl.a 


DEVHOME		= .
INSTALL_DIR	= /usr/local/apogee/lib



.KEEP_STATE:
CC =	g++
SWIG = /bin/swig

INCDIR		= $(DEVHOME)
ALTAINC		= -I./ApogeeUsb -I./FpgaRegs -DHAVE_STRERROR
CPPFLAGS	= -O2 -g -fPIC -DWall -DLINUX -DOSX -I../../include -I. \
    -I/usr/include/malloc -I/usr/include/python2.7 \
    -I/usr/lib64/python2.7/site-packages/numpy/core/include
PYSWIGFLAGS = -python -shadow -c++
LDFLAGS		= -L/usr/local/apogee/lib -shared -O2 -g
CONFIGTARGETS	= _apogeeUSB.so

all: $(CONFIGTARGETS)

CamData:
	$(CC) $(CPPFLAGS) -c ApnCamData.cpp
	$(CC) $(CPPFLAGS) -c ApnCamData_CCD7700D9.cpp
	$(CC) $(CPPFLAGS) -c ApnCamTable.cpp
	$(CC) $(CPPFLAGS) $(ALTAINC) -c ApnCamera_Linux.cpp

_apogeeUSB.so: CamData
	$(CC) $(CPPFLAGS) $(ALTAINC) -c ApnCamera.cpp
	$(CC) $(CPPFLAGS) $(ALTAINC) -c ApnCamera_USB.cpp
	$(CC) $(CPPFLAGS) $(ALTAINC) -c ApogeeUsb/ApogeeUsbLinux.cpp
	$(CC) $(CPPFLAGS) $(ALTAINC) -c ApogeeUsb/ApogeeUsbUpload.cpp
	$(SWIG) $(PYSWIGFLAGS) apogeeUSB.i
	$(CC) $(CPPFLAGS) $(ALTAINC) -c apogeeUSB_wrap.cxx
	$(CC) $(LDFLAGS) apogeeUSB_wrap.o ApnCamera.o ApnCamera_USB.o \
            ApogeeUsbLinux.o ApnCamData*.o ApnCamTable.o \
            ApogeeUsbUpload.o ApnCamera_Linux.o \
            -o _apogeeUSB.so -lccd -lusb -lcfitsio \
	    -shared -O2 -g


install: $(CONFIGTARGETS) FORCE
	cp $(CONFIGTARGETS) $(INSTALL_DIR)

clean:
	rm -f tags TAGS .make.state .nse_depinfo *.o *.dylib *.so *.a *.pyc \
    *wrap.c* test_altau test

tags:
	ctags $(LIBSOURCES)

FORCE:

test_usb:
	gcc -I/usr/local/include -o test test.c -L/usr/local/apogee/lib -lusb -shared -O2 -g

reset_apogee_usb: reset_apogee_usb.c
	gcc -I/usr/local/include -o reset_apogee_usb reset_apogee_usb.c -L/usr/local/apogee/lib -lusb

test_alta:
	g++ -I/usr/apogee/include  -I/usr/include/cfitsio test_alta.cpp \
	-IFpgaRegs -o test_altau \
	ApnCamera.o ApnCamera_Linux.o ApnCamera_USB.o  ApogeeUsbUpload.o \
	ApogeeUsbLinux.o ApnCamData*.o ApnCamTable.o \
	-L/usr/local/lib -L/usr/local/apogee/lib \
	-lccd  -lcfitsio -lusb
#	-ltcl8.3 -lccd  -lcfitsio -lusb
test_1:
	g++ -I/usr/apogee/include  \
    test_alta.cpp -IFpgaRegs -o test_altau \
    ApnCamera.o ApnCamera_Linux.o ApnCamera_USB.o  ApogeeUsbUpload.o \
    ApogeeUsbLinux.o ApnCamData*.o ApnCamTable.o -L/usr/local/apogee/lib \
    -L/usr/local/lib -lccd  -lusb -lcfitsio -shared -O2 -g
