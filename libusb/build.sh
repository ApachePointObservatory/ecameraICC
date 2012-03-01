#!/bin/sh

DSTNAME=libusb
DSTVERSION=0.1.13

MACOSX_DEPLOYMENT_TARGET=$1

PATH=`sed -e 's!/opt/local/bin!!' \
	  -e 's!/opt/local/sbin!!' \
	  -e 's!^:*!!' -e 's!:*$!!' -e 's!::*!:!g' <<< $PATH`
export PATH=$PATH:/opt/local/bin:/opt/local/sbin

if   [ "$MACOSX_DEPLOYMENT_TARGET" = "10.6" ]; then
    SDKVERSION=10.6
    ARCHS="i386 x86_64"
elif [ "$MACOSX_DEPLOYMENT_TARGET" = "10.7" ]; then
    SDKVERSION=10.7
    ARCHS="i386 x86_64"
else
    MACOSX_DEPLOYMENT_TARGET=default
    echo "Warning: No valid Deployment Target specified."
    echo "         Possible targets are: 10.6 and 10.7"
    echo "         The software will be built for the MacOSX version and"
    echo "         architecture currently running."
    echo "         No SDK package will be built."
fi

[ -n "$SDKVERSION" ] && NEXT_ROOT=/Developer/SDKs/MacOSX${SDKVERSION}.sdk

if [ -n "$NEXT_ROOT" ] && [ ! -e "$NEXT_ROOT" ]; then
    echo "Error: SDK build requested, but SDK build not installed."
    exit 1
fi

SRCDIR=`pwd`
BUILD=/tmp/$DSTNAME.build
DSTROOT=/tmp/$DSTNAME.dst

[ -e $BUILD ]   && ( rm -rf $BUILD   || exit 1 )
[ -e $DSTROOT ] && ( rm -rf $DSTROOT || exit 1 )

for d in $DSTROOT-* ; do ( rm -rf $d || exit 1 ) ; done

mkdir $BUILD

(
    cd $BUILD
    tar -z -x -f $SRCDIR/$DSTNAME-2011-10-29-svn.tar.gz

    cd $DSTNAME-2011-10-29-svn

    patch -p1 < $SRCDIR/libusb-cxx.patch
    patch -p1 < $SRCDIR/libusb-64bit.patch
    patch -p1 < $SRCDIR/libusb-endian.patch
    patch -p1 < $SRCDIR/libusb-runloop.patch

    aclocal
    glibtoolize --force
    autoheader
    automake --add-missing --force
    autoconf

    if   [ "$MACOSX_DEPLOYMENT_TARGET" = "10.6" ]; then
	CC="/usr/bin/gcc-4.2 -isysroot $NEXT_ROOT"
	CXX="/usr/bin/g++-4.2 -isysroot $NEXT_ROOT"
	CPP="/usr/bin/cpp-4.2 -isysroot $NEXT_ROOT"
    elif [ "$MACOSX_DEPLOYMENT_TARGET" = "10.7" ]; then
	CC="/usr/bin/llvm-gcc-4.2 -isysroot $NEXT_ROOT"
	CXX="/usr/bin/llvm-g++-4.2 -isysroot $NEXT_ROOT"
	CPP="/usr/bin/llvm-cpp-4.2 -isysroot $NEXT_ROOT"
    fi

    LDFLAGS="-no-undefined"

    if [ -n "$SDKVERSION" ]; then
	export PATH=$NEXT_ROOT/usr/bin:$PATH
	export MACOSX_DEPLOYMENT_TARGET
	export NEXT_ROOT
    fi

    export LD_PREBIND_ALLOW_OVERLAP=1

    if [ -n "$ARCHS" ]; then
	for arch in $ARCHS ; do
	    CC=$CC CFLAGS="$CFLAGS -arch $arch" \
		CXX=$CXX CXXFLAGS="$CXXFLAGS -arch $arch" \
		CPP=$CPP CPPFLAGS="$CPPFLAGS -arch $arch" \
		LDFLAGS="$LDFLAGS -arch $arch" \
		./configure --build `./config.guess` --prefix=/opt/apogee
	    make
	    make install
	    make clean
	done
	mkdir $DSTROOT
	arch=`./config.guess | \
	    sed -e s/-.*// -e s/i.86/i386/ -e s/powerpc/ppc/`
	[ "$arch" = "ppc" -a ! -d $DSTROOT-ppc ] && arch=ppc7400
	[ ! -d $DSTROOT-$arch ] && arch=`sed "s/ .*//" <<< $ARCHS`
	for d in `(cd $DSTROOT-$arch ; find . -type d)` ; do
	    mkdir -p $DSTROOT/$d
	done
	for f in `(cd $DSTROOT-$arch ; find . -type f)` ; do
	    if [ `wc -w <<< $ARCHS` -gt 1 ] ; then
		file $DSTROOT-$arch/$f | grep -q -e 'Mach-O\|ar archive'
		if [ $? -eq 0 ] ; then
		    lipo -c -o $DSTROOT/$f $DSTROOT-*/$f
		else
		    cp -p $DSTROOT-$arch/$f $DSTROOT/$f
		fi
	    else
		cp -p $DSTROOT-$arch/$f $DSTROOT/$f
	    fi
	done
	for l in `(cd $DSTROOT-$arch ; find . -type l)` ; do
	    cp -pR $DSTROOT-$arch/$l $DSTROOT/$l
	done
	rm -rf $DSTROOT-*
    else
	CC=$CC CFLAGS="$CFLAGS" \
	    CXX=$CXX CXXFLAGS="$CXXFLAGS" \
	    CPP=$CPP CPPFLAGS="$CPPFLAGS" \
	    LDFLAGS="$LDFLAGS" \
	    ./configure --prefix=/opt/apogee
	make
	make install
    fi
)

rm -rf $BUILD
rm -rf $DSTROOT-*
