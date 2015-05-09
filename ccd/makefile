#
# APOGEE makefile for linux
# $Id: Makefile.svr4,v 1.4 1995/06/15 07:34:43 gillies Exp $
#
BASE = ccd
LNAME = lib$(BASE)
MACHINE = linux
M = linux
# Version and minor version
V = 1
MV = 0


DEVHOME		= .
LIBDIR		= $(DEVHOME)
STATICLIBRARY	= $(LIBDIR)/$(LNAME)_$(M).a
SHAREDLIB	= $(LIBDIR)/$(LNAME)_$(M).dylib.$(V).$(MV)	# ignored
SHAREDLIBLN	= $(LIBDIR)/$(LNAME)_$(M).dylib
INSTALL_DIR	= /opt/apogee
TCLSRC = /opt/apogee/extern/tcl8.3.1/generic
TKSRC = /opt/apogee/extern/tk8.3.1/generic                                   

.PRECIOUS:	$(STATICLIBRARY) $(LIBDIR)/$(LNAME)_$(M).so.$(V).$(MV) $(LIBDIR)/$(LNAME)_$(M).sa.$(V).$(MV)

# Test program
TPROG = apwish.$(M)
TSRC =  tkMain.c myAppInit.c 
TOBJ =	$(TSRC:%.c=%.o)


# -R$(DEVHOME):$(GWCHOME)/lib -lsocket -lnsl
# If you don't have TkPixmap tk leave out Xpm
XPMLIBS = -lXpm 
LDLIBS +=  -ltk8.3 $(XPMLIBS) -ltcl8.3 -lX11 -lm 

.KEEP_STATE:
CC =	gcc
INCDIR		= $(DEVHOME)
PRIVATEINCDIR	= $(DEVHOME)
GUIINC          = /opt/apogee/include

#CFLAGS 		+= -O -g -D_POSIX_C_SOURCE 
CFLAGS 		+= -pipe -O2 -g -D$(MACHINE)  -DLINUX -Wall  -I$(TCLSRC) -I$(TKSRC)     


CPPFLAGS	= -I/opt/local/include -I$(INCDIR) -I$(GUIINC) -DVER=\"$(V).$(MV)\"

INCLUDES =	

PRIVATE_INCLUDES =	

LIBSOURCES =    ccd_library.c

LIBDATA =	

CSOURCE_ALL = $(LIBSOURCES) $(LIBDATA)

STATICLIBDIR=Static
SHAREDLIBDIR=Shared

#CONFIGPIC		= -fPIC
CONFIGPIC		=
CONFIGSHAREDLIBLD	= g++ -dynamiclib -L/opt/local/lib -lcfitsio -o $(LNAME)_$(M).dylib.$(V).$(MV) $?
#CONFIGSHAREDLIBLD	= g++ -dynamiclib libccd.dylib $?

CONFIGTARGETS		= $(SHAREDLIB)

CFLAGS		+= -DSVR4
NSLLIB		= -lnsl

all: Static Shared $(LIBDIR) $(CONFIGTARGETS) $(STATICLIBRARY) $(SHAREDLIBLN)
#all: Shared $(LIBDIR) $(CONFIGTARGETS) $(SHAREDLIBLN)
#all: Static $(LIBDIR) $(CONFIGTARGETS) $(STATICLIBRARY) 
test: $(TPROG)

$(STATICLIBRARY):	$(CSOURCE_ALL:%.c=Static/%.o)
	ar rv $@ $?

$(STATICLIBDIR)/%.o: %.c $(PRIVATE_INCLUDES) $(INCLUDES)
	$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

$(SHAREDLIB):	$(CSOURCE_ALL:%.c=Shared/%.o)
	$(CONFIGSHAREDLIBLD)

$(SHAREDLIBDATA): $(LIBDATA:%.c=Shared/%.o)
	ar ruv $(SHAREDLIBDATA) $?
	-ranlib $(SHAREDLIBDATA)

$(SHAREDLIBDIR)/%.o: %.c $(PRIVATE_INCLUDES) $(INCLUDES)
	$(CC) $(CFLAGS) $(CONFIGPIC) $(CPPFLAGS) -c $< -o $@

$(SHAREDLIBLN):
	rm -f $(SHAREDLIBLN)
	ln -s $(SHAREDLIB) $(SHAREDLIBLN)

xdr:	edm.x
	rpcgen -C edm.x

$(TPROG): $(TSRC) $(TOBJ) $(STATICLIBRARY)
	$(LINK.c) -o $@ $(TOBJ)  libapogee_linux.a /-l$(BASE)_$(M) $(LDLIBS)

sunos:
	@-rm makefile
	ln -s Makefile.sunos makefile

solaris:
	@-rm makefile
	ln -s Makefile.solaris makefile

linux:
	@-rm makefile
	ln -s Makefile.linux makefile

Shared:
	-mkdir Shared

Static:
	-mkdir Static

$(LIBDIR):
	-mkdir $(LIBDIR)


install: $(STATICLIBRARY) $(SHAREDLIB) FORCE
	-mkdir $(INSTALL_DIR)/lib
	cp $(STATICLIBRARY) $(INSTALL_DIR)/lib
	cp $(SHAREDLIB) $(INSTALL_DIR)/lib
	rm -f $(INSTALL_DIR)/lib/$(LNAME)_$(M).so
	ln -s $(INSTALL_DIR)/lib/$(LNAME)_$(M).dylib.$(V).$(MV) $(INSTALL_DIR)/lib/$(LNAME)_$(M).so
	rm -f $(INSTALL_DIR)/lib/$(LNAME).so
	ln -s $(INSTALL_DIR)/lib/$(LNAME)_$(M).dylib.$(V).$(MV) $(INSTALL_DIR)/lib/$(LNAME).so

clean:
	rm -rf Shared Static
	rm -f tags TAGS .make.state .nse_depinfo $(TOBJ)
	rm -f libccd* *.o

tags:
	ctags $(LIBSOURCES)

FORCE:

