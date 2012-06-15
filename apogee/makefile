#
# APOGEE makefile for linux
# $Id: Makefile.svr4,v 1.4 2004/02/15 07:34:43 rfactory Exp $
#
#/opt/apogee/lib/libcurl.a 


DEVHOME		= .
INSTALL_DIR	= /opt/apogee/lib
TCLSRC = /opt/apogee/extern/tcl8.3.1/generic
TKSRC = /opt/apogee/extern/tk8.3.1/generic                                   



.KEEP_STATE:
CC =	g++
SWIG = /opt/local/bin/swig

INCDIR		= $(DEVHOME)
ALTAINC		= -I./ApogeeUsb -I./FpgaRegs -DHAVE_STRERROR
CPPFLAGS	= -O2 -g -fPIC -DWall -DLINUX -DOSX -I../../include -I. \
    -I/usr/include/malloc -I/opt/local/include \
    -I/opt/local/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 
PYSWIGFLAGS = -python -shadow -c++
LDFLAGS		= -dynamiclib -lpython2.7 -L/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib -L/opt/local/lib -L/opt/apogee/lib
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
            -o _apogeeUSB.so -lccd -lusb \
            -framework CoreFoundation -framework IOKit


install: $(CONFIGTARGETS) FORCE
	cp $(CONFIGTARGETS) $(INSTALL_DIR)

clean:
	rm -f tags TAGS .make.state .nse_depinfo *.o *.dylib *.so *.a *.pyc \
    *wrap.c* test_altau test

tags:
	ctags $(LIBSOURCES)

FORCE:

test_usb:
	gcc -I/opt/local/include -o test test.c -L/opt/apogee/lib -lusb -framework CoreFoundation -framework IOKit

reset_apogee_usb: reset_apogee_usb.c
	gcc -I/opt/local/include -o reset_apogee_usb reset_apogee_usb.c -L/opt/apogee/lib -lusb -framework CoreFoundation -framework IOKit

test_alta:
	g++ -I/opt/apogee/include  test_alta.cpp -IFpgaRegs -o test_altau \
	ApnCamera.o ApnCamera_Linux.o ApnCamera_USB.o  ApogeeUsbUpload.o \
	ApogeeUsbLinux.o ApnCamData*.o ApnCamTable.o \
	-L/opt/local/lib -L/opt/apogee/lib \
	-ltcl8.3 -lccd  -lcfitsio -lusb \
	-framework CoreFoundation -framework Tcl -framework IOKit

test_1:
	g++ -I/opt/apogee/include  -I/opt/local/include \
    test_alta.cpp -IFpgaRegs -o test_altau \
    ApnCamera.o ApnCamera_Linux.o ApnCamera_USB.o  ApogeeUsbUpload.o \
    ApogeeUsbLinux.o ApnCamData*.o ApnCamTable.o -L/opt/apogee/lib \
    -L/opt/local/lib -lccd  -lusb -lcfitsio -framework CoreFoundation -framework IOKit
