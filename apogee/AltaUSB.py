__all__ = ['AltaUSB']

from apogeeUSB import CApnCamera

import numarray
import numpy as np
import pyfits
import pixel16

import math
import re
import socket
import time
import urllib
import sys
import os

import logging

logging.basicConfig(filename='/tmp/ecamera.log',level=logging.DEBUG)

from traceback import print_exc, format_exc

def DEBUG(message, level=0):
    logging.debug(message)
    return
    if message[-1] != '\n':
        message += '\n'
    sys.stdout.write(message)
    sys.stdout.flush()

class AltaUSB(CApnCamera):
    # Parse the response to the Read and Write register calls.
    #
    readRegRE = re.compile('^FPGA\[(\d+)\]=(0x[0-9A-F]+)\s*$')

    def __init__(self):
        """ Connect to an Alta-E at the given IP address and start to initialize it. """
        CApnCamera.__init__(self)

        self.ok = False         # init driver opened
        self.connected = False  # usb is connected
        self.present = False    # InitData() succeeded 
        self.Apn_Status_ConnectionError = 6
        DEBUG('calling doInit()')
        self.doInit()
        self.bin_x, self.bin_y = 1, 1
        self.x0, self.y0 = 0, 0
        DEBUG('AltaUSB __init__ done')

    def __del__(self):
        self.CloseDriver()
        
    def __checkSelf(self):
        """ Single point to call before communicating with the camera. """
        
        if not self.connected:
            raise RuntimeError("Alta camera device not available")
        if not self.present:
            raise RuntimeError("Alta camera failed to init defaults")
        if not self.ok:
            raise RuntimeError("Alta camera init failed")
        
    def doOpen(self):
        """ (Re-)open a connection to the camera. """
        raise RuntimeError("Cannot reconnect to an already open Alta.")
    
    def doInit(self):
        """ (Re-)initialize and already open connection. """

        # APN_ALTA_CCD7700HS_CAM_ID is 27

        DEBUG('init driver')
        self.ok = self.InitDriver(1, 0, 0)
        DEBUG('okay is %s\n' % (self.ok))
        self.ResetSystem()

        self.connected = False
        self.present = False

        state = self.read_ImagingStatus()
        DEBUG('_expose: ok %d, image status %d\n' % (self.ok, state))

        result = self.InitDefaults()
        DEBUG('_expose, init defaults result %s\n' % (result))


        self.present = True

        state = self.read_ImagingStatus()
        if state != self.Apn_Status_ConnectionError:
            self.connected = True

        self.__checkSelf()

        # Turn off LEDs
        self.write_LedMode(0)

        DEBUG('return from doInit')
        return self.ok
    
    def readReg(self, reg):
        """ Read a single register. """

        self.__checkSelf()
        raise UnimplementedError("readReg")


    def readRegs(self, regs):
        """ Read a single register. """

        self.__checkSelf()
        raise UnimplementedError("readRegs")


    def writeReg(self, reg, value):
        """ Write a single register. """

        self.__checkSelf()

        raise UnimplementedError("writeReg")

    def writeRegs(self, regs, values):
        """ Write a single register. """

        self.__checkSelf()

        if len(regs) != len(values):
            raise ValueError("number of registers and values passed to writeRegs must match.")
        
        raise UnimplementedError("writeReg")

    def coolerStatus(self):
        """ Return a cooler status keywords. """

        self.__checkSelf()

        status = self.read_CoolerStatus()
        setpoint = self.read_CoolerSetPoint()
        drive = self.read_CoolerDrive()
        ccdTemp = self.read_TempCCD()
        heatsinkTemp = self.read_TempHeatsink()
        fan = self.read_FanMode()
        
        #return "cooler=%0.1f,%0.1f,%0.1f,%0.1f,%d,%d" % (setpoint,
        return "setpoint %0.1f, ccd %0.1f,heatsink %0.1f, drive %0.1f,fan %d,status %d" % (setpoint,
                                                         ccdTemp, heatsinkTemp,
                                                         drive, fan, status)
    def setCooler(self, setPoint):
        """ Set the cooler setpoint.

        Args:
           setPoint - degC to use as the TEC setpoint. If None, turn off cooler.

        Returns:
           the cooler status keyword.
        """

        self.__checkSelf()

        if setPoint == None:
            self.write_CoolerEnable(0)
            return

        self.write_CoolerSetPoint(setPoint)
        self.write_CoolerEnable(1)

        return self.coolerStatus()

    def setFan(self, level):
        """ Set the fan power.

        Args:
           level - 0=Off, 1=low, 2=medium, 3=high.
        """

        self.__checkSelf()

        if type(level) != type(1) or level < 0 or level > 3:
            raise RuntimeError("setFan level must be an integer 0..3")

        self.write_FanMode(level)

    def setBinning(self, x, y=None):
        """ Set the readout binning.

        Args:
            x = binning factor along rows.
            y ? binning factor along columns. If not passed in, same as x.
        """

        DEBUG('in binning, check\n');

        self.__checkSelf()

        if y == None:
            y = x
        
        DEBUG('x %s, y %s\n' % (x, y));
        try:
            self.write_RoiBinningV(y)       # NOTE: Order is important!!
        except:
            DEBUG(format_exc())
        #time.sleep(0.2)
        DEBUG('y set, now set x\n')
        #time.sleep(0.2)
        try:
            self.write_RoiBinningH(x)       # This call resets the FPGA if changed
        except:
            print format_exc()
        DEBUG('in binning, done\n');
        self.bin_x = x
        self.bin_y = y

    def _iround(self, x):
        """
        iround(number) -> integer        Round a number to the nearest integer
        """
        return int(round(x) - .5) + (x > 0)

    def setWindow(self, x0, y0, sizex, sizey):
        '''
        Set the readout window
    
        x0, y0 are unbinned offset starting from 0, 0.
        sizex, sizey are binned
        '''

        self.__checkSelf()

        self.x0 = self._iround(x0 / self.bin_x)
        self.y0 = self._iround(y0 / self.bin_y)

        DEBUG('set PixlesH %d' % (sizey))
        self.write_RoiPixelsH(sizey)
        DEBUG('set PixlesV %d' % (sizex))
        self.write_RoiPixelsV(sizex)
        self.write_RoiStartX(x0)
        self.write_RoiStartY(y0)
        
    def expose(self, itime, filename=None):
        return self._expose(itime, True, filename)
    def dark(self, itime, filename=None):
        return self._expose(itime, False, filename)
    def bias(self, filename=None):
        return self._expose(0.0, False, filename)
        
    def _expose(self, itime, openShutter, filename):
        """ Take an exposure.

        Args:
            itime        - seconds
            openShutter  - True to open the shutter.
            filename     - a full pathname. If None, the image is returned

        Returns:
            dict         - size:     (width, height)
                           type:     FITS IMAGETYP
                           iTime:    integration time
                           filename: the given filename, or None
                           data:     the image data as a string, or None if saved to a file.
        """

        self.__checkSelf()

        state = self.read_ImagingStatus()
        DEBUG('_expose: image status %d\n' % (state))

        # Is the camera alive and flushing?
        for i in range(2):
            state = self.read_ImagingStatus()
            if state == 4:
                break;
            # print "starting state=%d, RESETTING" % (state)
            self.ResetSystem()

        if state != 4 or state < 0: 
            raise RuntimeError("bad imaging state=%d" % (state))

        d = {}

        # Block while we expose. But sleep if we have to wait a long time.
        # And what is the flush time of this device?
        start = time.time()
        DEBUG('self.Expose\n')
        DEBUG('itime %s, open shutter %s\n' % (itime, openShutter))
        self.Expose(itime, openShutter)
        DEBUG('self.Expose done\n')
        if itime > 0.25:
            time.sleep(itime - 0.2)

        # We are close to the end of the exposure. Start polling the camera
        i = 50
        while i > 0:
            i -= 1
            now = time.time()
            state = self.read_ImagingStatus()
            if state < 0: 
                raise RuntimeError("bad state=%d" % (state))
            if state == 3:
                break
            DEBUG("state=%d time=%0.2f waiting to read" % \
                (state, now - (start + itime)))
            time.sleep(0.1)

        if i == 0:
            raise RuntimeError("bad state=%d" % (state))

        if openShutter:
            fitsType = 'obj'
        elif itime == 0:
            fitsType = 'zero'
        else:
            fitsType = 'dark'

        # I _think_ this is the right way to get the window size...
        #h = self.m_pvtExposurePixelsV
        #w = self.m_pvtExposurePixelsH

        t0 = time.time()
        DEBUG("fetch image")
        image = self.fetchImage()
        DEBUG("fetch done")
        t1 = time.time()

        state = self.read_ImagingStatus()
        DEBUG("state=%d readoutTime=%0.2f" % (state,t1-t0))

        DEBUG("dir of d=%s" % (dir(d)))
        d['iTime'] = itime
        d['type'] = fitsType
        d['startTime'] = start
        d['data'] = image
        d['filename'] = filename

        DEBUG("filename is ...%s..." % (filename))
        if filename:
            try:
                DEBUG("write fits")
                self.WriteFITS(d)
            except:
                DEBUG(format_exc())

        return d

 
    def fetchImage(self):
        """ Return the current image. """
 
        # I _think_ this is the right way to get the window size...
        h = self.GetExposurePixelsV()
        w = self.GetExposurePixelsH()
 
        DEBUG("create image h %d, w %d" % (h, w))
        image = np.ndarray((w,h), dtype='uint16')
        DEBUG("fill image buffer")
        self.FillImageBuffer(image)
        DEBUG("return image")
 
        return image


    def PyRead(self):
        """ Read the current image using the python-level hooks. """
    
        h = self.m_pvtRoiPixelsV
        w = self.m_pvtRoiPixelsH

        x = urllib.urlopen('http://%s/UE/image.bin' % (self.hostname))
        data = x.read()
        data = pixel16.undoAlta(data, h, w)

        self.m_pvtImageInProgress = 0
        self.SignalHaveRead()

        return data

    def getTS(self, t=None, format="%Y/%m/%d %H:%M:%S", zone="Z"):
        """ Return a proper ISO timestamp for t, or now if t==None. """
        
        if t == None:
            t = time.time()
            
        if zone == None:
            zone = ''
            
        time_string = time.strftime(format, time.gmtime(t))
        utdate, uttime = time_string.split()
        return uttime, utdate

                                                        
    def WriteFITS(self, d):
        """ Write an image to a FITS file.

        Args:
            data      - the image data, as a string.
            w, h      - the image height and width.
            filename  - the filename to write to.
        """

        filename = d['filename']

        hdu = pyfits.PrimaryHDU(d['data'])
        hdr = hdu.header

        uttime, utdate = self.getTS(d['startTime'])
        hdr.update('BSCALE', 1.0)
        hdr.update('BZERO', 32768.0)
        hdr.update('BEGX', self.x0+1)
        hdr.update('BEGY', self.y0+1)
        hdr.update('FULLX', 512)
        hdr.update('FULLY', 512)
        hdr.update('BINX', self.bin_x)
        hdr.update('BINY', self.bin_y)
        hdr.update('EXPTIME',  d['iTime'])
        hdr.update('CAMNAME', 'USB Apogee Camera', 'Camera used for this image')
        hdr.update('CAMID', 1)
        hdr.update('CAMTEMP', self.read_TempCCD(), 'degrees C')
        hdr.update('UTTIME', uttime, 'UT Time CCD was read')
        hdr.update('UTDATE', utdate, 'UT Date CCD was read')

        # pyfits now does the right thing with uint16
        hdu.writeto(filename)

        del hdu
        del hdr

        os.chmod(filename, 0666)

if __name__ == "__main__":
    alta = AltaUSB()
    print alta.coolerStatus()
    alta.setCooler(15.0)
    print alta.coolerStatus()
