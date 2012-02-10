'''
Interface to Apogee USB Camera

NOTE: The chip appears to be rotated 90 degrees.  Hence, the flip = True flag
'''
__all__ = ['AltaUSB']

import numpy as np
import pyfits
import time
import os
import logging
from traceback import format_exc

from apogeeUSB import CApnCamera

logging.basicConfig(filename='/tmp/ecamera.log',level=logging.DEBUG)

def DEBUG(message, level=0):
    logging.debug(time.asctime(time.gmtime(time.time()))+message)
    return

class AltaUSB(CApnCamera):
    '''
    Instantiate this class and get an object that should be connected to the
    camera.  For now, a power cycle is sometimes needed.
    '''

    def __init__(self):
        ''' 
        Connect to a camera, initialize it. 
        '''

        CApnCamera.__init__(self)

        self.flip = True       # make image line up
        self.ok = False         # init driver opened
        self.connected = False  # usb is connected
        self.present = False    # InitData() succeeded 

        # this definition is lifted from USB CCD sources - bad failure, common
        self.Apn_Status_ConnectionError = 6

        DEBUG('calling doInit(1)')
        self.doInit(init=1)
        self.bin_x, self.bin_y = 1, 1
        self.x0, self.y0 = 0, 0
        DEBUG('AltaUSB __init__ done')

    def __del__(self):
        DEBUG('AltaUSB __del__ close driver')
        self.CloseDriver()
        time.sleep(1.0)
        
    def __checkSelf(self):
        ''' Single point to call before communicating with the camera. '''
        
        if not self.connected:
            raise RuntimeError("Alta camera device not available")
        if not self.present:
            raise RuntimeError("Alta camera failed to init defaults")
        if not self.ok:
            raise RuntimeError("Alta camera init failed")
        
    def doOpen(self):
        ''' (Re-)open a connection to the camera. '''
        raise RuntimeError("Cannot reconnect to an already open Alta.")
    
    def doInit(self, init=0):
        ''' (Re-)initialize and already open connection. '''

        # APN_ALTA_CCD7700HS_CAM_ID is 27
        if not init:
            self.CloseDriver()

        DEBUG('doInit: init driver')
        self.ok = self.InitDriver(1, 0, 0)
        DEBUG('okay is %s\n' % (self.ok))
        DEBUG('doInit: reset system')
        self.ResetSystem()

        self.connected = False
        self.present = False

        state = self.read_ImagingStatus()
        DEBUG('doInit: ok %d, image status %d\n' % (self.ok, state))

        result = self.InitDefaults()
        DEBUG('doInit, init defaults result %s\n' % (result))

        self.present = True

        state = self.read_ImagingStatus()
        if state != self.Apn_Status_ConnectionError:
            self.connected = True

        self.__checkSelf()

        # Turn off LEDs
        self.write_LedMode(0)

        DEBUG('return from doInit')
        return self.ok
    
    def coolerStatus(self):
        ''' Return a cooler status keywords. '''

        self.__checkSelf()

        status = self.read_CoolerStatus()
        setpoint = self.read_CoolerSetPoint()
        drive = self.read_CoolerDrive()
        ccdTemp = self.read_TempCCD()
        heatsinkTemp = self.read_TempHeatsink()
        fan = self.read_FanMode()
        
        #return "cooler=%0.1f,%0.1f,%0.1f,%0.1f,%d,%d" % (setpoint,
        return \
"setpoint %0.1f, ccd %0.1f,heatsink %0.1f, drive %0.1f,fan %d,status %d" \
            % (setpoint, ccdTemp, heatsinkTemp, drive, fan, status)

    def setCooler(self, setPoint):
        ''' Set the cooler setpoint.

        Args:
           setPoint - degC to use as the TEC setpoint. If None, turn off cooler.

        Returns:
           the cooler status keyword.
        '''

        self.__checkSelf()

        if setPoint == None:
            self.write_CoolerEnable(0)
            return

        self.write_CoolerSetPoint(setPoint)
        self.write_CoolerEnable(1)

        return self.coolerStatus()

    def setFan(self, level):
        ''' Set the fan power.

        Args:
           level - 0=Off, 1=low, 2=medium, 3=high.
        '''

        self.__checkSelf()

        if type(level) != type(1) or level < 0 or level > 3:
            raise RuntimeError("setFan level must be an integer 0..3")

        self.write_FanMode(level)

    def setBinning (self, x, y=None):
        ''' Set the readout binning.

        Args:
            x = binning factor along rows.
            y ? binning factor along columns. If not passed in, same as x.
        '''

        DEBUG('in binning, check\n')

        self.__checkSelf()

        if x > 5:
            x = 5

        if y == None:
            y = x

        if y > 5:
            y = 5

        if y < 1:
            y = 1

        if x < 1:
            x = 1
        #complain
        
        try:
            self.write_RoiBinningV(y)       # NOTE: Order is important!!
        except:
            DEBUG(format_exc())

        try:
            self.write_RoiBinningH(x)       # This call resets FPGA if changed
        except:
            print format_exc()

        self.bin_x = x
        self.bin_y = y

    def _iround(self, x):
        '''
        iround(number) -> integer        Round a number to the nearest integer
        '''
        return int(round(x) - .5) + (x > 0)

    def setWindow(self, x0, y0, sizex, sizey):
        '''
        Set the readout window
    
        x0, y0 are unbinned offset starting from 0, 0.
        sizex, sizey are binned
        '''

        self.__checkSelf()

        if y0 < 0:
            DEBUG('y0 too small %d', y0)
            y0 = 0
        if y0 > 512:
            DEBUG('y0 too large %d', y0)
            y0 = 512
        if x0 < 0:
            DEBUG('x0 too small %d', x0)
            x0 = 0
        if x0 > 512:
            DEBUG('x0 too large %d', x0)
            x0 = 512

        if (x0 + sizex * self.bin_x) > 512:
            DEBUG('sizex too large x0 %d, size %d, bin %d' %\
                (x0, sizex,self.bin_x))
            sizex = (512 - x0) / self.bin_x

        if (y0 + sizey * self.bin_y) > 512:
            DEBUG('sizey too large y0 %d, size %d, bin %d' %\
                (y0, sizey ,self.bin_y))
            sizey = (512 - y0) / self.bin_y

        self.x0 = self._iround(x0 / self.bin_x)
        self.y0 = self._iround(y0 / self.bin_y)

        if self.flip:
            self.m_pvtRoiStartX = 512 - (y0 + sizey * self.bin_y)
            self.m_pvtRoiStartY = x0
            self.m_pvtRoiPixelsH = sizey
            self.m_pvtRoiPixelsV = sizex
        else:
            self.m_pvtRoiStartX = x0
            self.m_pvtRoiStartY = y0
            self.m_pvtRoiPixelsH = sizex
            self.m_pvtRoiPixelsV = sizey
        
    def expose(self, itime, filename=None):
        return self._expose(itime, True, filename)
    def dark(self, itime, filename=None):
        return self._expose(itime, False, filename)
    def bias(self, filename=None):
        return self._expose(0.0, False, filename)
        
    def _expose(self, itime, openShutter, filename):
        ''' Take an exposure.

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
        '''

        self.__checkSelf()

        state = self.read_ImagingStatus()
        DEBUG('_expose: image status %d\n' % (state))

        # Is the camera alive and flushing?
        for i in range(2):
            state = self.read_ImagingStatus()
            if state == 4:
                break
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
        DEBUG("state=%d readoutTime=%0.2f" % (state, t1-t0))

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
        ''' Return the current image. '''
 
        # I _think_ this is the right way to get the window size...
        h = self.GetExposurePixelsV()
        w = self.GetExposurePixelsH()
 
        DEBUG("create image w %d, h %d" % (w, h))
        image = np.ndarray((w, h), dtype='uint16')
        DEBUG("fill image buffer")
        self.FillImageBuffer(image)
        DEBUG("return image")
 
        image = image.reshape(h, w)
        if self.flip:
            image = np.rot90(image)
        return image


    def getTS(self, t_now=None, format="%Y/%m/%d %H:%M:%S", zone="Z"):
        ''' Return a proper ISO timestamp for t, or now if t==None. '''
        
        if t_now == None:
            t_now = time.time()
            
        if zone == None:
            zone = ''
            
        time_string = time.strftime(format, time.gmtime(t_now))
        utdate, uttime = time_string.split()
        return uttime, utdate

                                                        
    def WriteFITS(self, d):
        ''' Write an image to a FITS file.

        Args:
            data      - the image data, as a string.
            w, h      - the image height and width.
            filename  - the filename to write to.
        '''

        filename = d['filename']

        hdu = pyfits.PrimaryHDU(d['data'])
        hdr = hdu.header

        uttime, utdate = self.getTS(d['startTime'])
        hdr.update('BSCALE', 1.0)
        hdr.update('BZERO', 32768.0)
        hdr.update('BEGX', self.x0+1)
        hdr.update('BEGY', self.y0+1) # +1
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
