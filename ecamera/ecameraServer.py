#!/opt/local/bin/python
'''
internet service that reads and writes from standard io

knows these commands:
    doread
    dodark
    init
    setcam
    showstatus
'''
import os
import re
import ConfigParser
import sys
import time
from traceback import format_exc, print_exc

import Pyro4
Pyro4.config.SOCK_REUSE=True
from EventService.Clients import Publisher

from debugLog import DEBUG
import AltaUSB

BASE_DIRECTORY = '/export/images/forTron/echelle'
CONFIG = os.path.join(os.getenv('HOME'),'config/ecamera.ini')

publisher = Publisher('PYRO::TRON-EventChannel@hub35m.apo.nmsu.edu:30000')

def exposureState(message, overall_time, remaining_time):
    global publisher
    # this will publish into the event stream
    # Ecamera.Hardware.ExposureState (0.0, 0.0)
    # tuple with overall and remainig time
    state = {'state':message,
             'overall_time':overall_time, 
             'remaining_time':remaining_time}
    try:
        publisher.publish('Ecamera.Hardware.ExposureState', state)
    except:
        print_exc()

class ECamera:
    def __init__(self):
        self.image_name = 'gimg%04d.fits'
        self.image_directory = '/export/images/forTron/guider'
        self.image_wrap = 9999
        self.x0 = self.y0 = 0
        self.setpoint = 0.0
        self.last_image = None
        self.integration = 0.0
        self.ny = self.nx = 512
        self.max_bin_x = 8
        self.max_bin_y = 512
        self.name = 'Alta U77'
        self.sizex = 512
        self.sizey = 512
        self.biny = 1
        self.binx = 1
        self.noise_units = 'electrons/sec/pixel'
        self.dark_current_units = 'electrons/sec/pixel'
        self.noise = 14
        self.dark_current = 0.8
        self.alta_usb = None

        self.connect()

        self.reply = ''
        self.read_config()
        self.image_number = 0
        try:
            self._image_number_init()
        except:
            DEBUG(format_exc())
            
        # software setup, now be sure hardware is set right
        if self.alta_usb:
            self.alta_usb.setCooler(self.setpoint)

    def __del__(self):
        self.disconnect()

    def connect(self):
        '''
            connect to camera
        '''
        if self.alta_usb:
            return

        self.exposure_state = 'done'
        try:
            self.alta_usb = AltaUSB.AltaUSB()
        except:
            self.alta_usb = None
            DEBUG(format_exc())

    def disconnect(self):
        '''
            disconnect from camera
        '''
        if not self.alta_usb:
            return

        self.exposure_state = 'done'
        if self.alta_usb:
            del self.alta_usb
            self.alta_usb = None

    def _image_number_init (self):
        '''
        setup image number

        throws exceptions if NFS file system has crashed
        '''
        filename = os.path.join(self.image_directory,'last.image')
        try:
            DEBUG('try to open this %s\n' % (filename), 0)
            last_file = file(filename, 'r').readline().strip()
            DEBUG('try to search for last_file %s\n' % (last_file))
            result = re.search('.*gimg(\d+).fits$', last_file)
            if result:
                self.last_image = int(result.group(1))
                self.image_number = int(result.group(1)) + 1
                if self.image_number > self.image_wrap:
                    self.image_number = 0
        except:
            file_search = 'ls -lt %s | head -n 1' % \
                (os.path.join(self.image_directory, 'gimg*.fits'))
            DEBUG('file search command: %s\n' %(file_search), 0)
            last_file = os.popen(file_search).readline().strip()
            DEBUG('found last file ...%s...' % (last_file), 0)
            if not last_file:
                # search the name for the number
                result = re.search('.*gimg(\d+).fits$', last_file)
                if result:
                    self.last_image = int(result.group(1))
                    self.image_number = int(result.group(1)) + 1
                    if self.image_number > self.image_wrap:
                        self.image_number = 0
                    self._image_number_write()
                else:
                    self.last_image = 0
                    self.image_number = 0
                    DEBUG('_image_number_init() search fails ...%s...' % \
                        (last_file), 0)
            else:
                self.last_image = 0
                self.image_number = 0

    def _image_number_write(self):
        '''
        write image_number to last.image

        Exceptions:
            NFS errors
        '''
        filename = os.path.join(self.image_directory, self.image_name)
        filename = filename % (self.image_number)
        last_image = os.path.join(self.image_directory, 'last.image')
        file(last_image, 'w').write(filename)
        if os.path.isfile(filename):
            os.unlink(filename)
        return filename
        

    def read_config(self):
        '''
        Configure instance variables from the configuration file
        '''
        config = ConfigParser.ConfigParser()
        config.read(CONFIG)
        DEBUG('read config done')
        try:
            self.nx = config.getint('alta', 'nx')
            self.ny = config.getint('alta', 'ny')
            self.noise = config.getfloat('alta', 'noise')
            self.dark_current = config.getfloat('alta', 'dark current')
            self.max_bin_x = config.getint('alta', 'max_bin_x')
            self.max_bin_y = config.getint('alta', 'max_bin_y')
            self.image_wrap = config.getint('ecamera','image wrap')
            self.noise_units = config.get('alta', 'noise units')
            self.dark_current_units = config.get('alta', 'dark current units')
            self.setpoint = config.getfloat('alta', 'setpoint')
            self.name = config.get('alta', 'name')
            self.image_directory = config.get('ecamera','image directory')
            self.image_directory = os.path.expandvars(self.image_directory)
            self.image_name = config.get('ecamera','image name')
        except:
            # This should not happen!  It is a broken configuration
            DEBUG(format_exc())
    
    def _iround(self, x):
        """
        iround(number) -> integer
        Round a number to the nearest integer
        """
        return int(round(x) - .5) + (x > 0)
    
    def status(self):
        '''
            returns CCD temperature, last image number, exposure state

        '''
        ccd_temp = 0.0
        if self.alta_usb:
            self.alta_usb.coolerStatus()
            ccd_temp = self.alta_usb.read_TempCCD()
        reply = {
            'ccd-temp':ccd_temp,
            'setpoint':self.setpoint,
            'last-image':self.last_image,
            'exposure-state':self.exposure_state,
            'binx':self.binx,
            'biny':self.biny,
            'x0':self.x0,
            'y0':self.y0,
            'sizex':self.sizex,
            'sizey':self.sizey,
            'nx':self.nx,
            'ny':self.ny,
        }
        return reply

    def _setBinning(self, bin=None):
        '''
        modifies binning, so _setWindow() needs to be called to
        update the window on the chip
        '''
        # range check binning
        if not bin:
            return

        binx, biny = bin

        if binx != self.binx or biny != self.biny:
            # calculate old window in real pixels
            sizex = self._iround(float(self.sizex * self.binx))
            sizex /= binx
            sizey = self._iround(float(self.sizey * self.biny))
            sizey /= biny
            self.binx = binx
            self.biny = biny

    def _setWindow(self, offset=None, size=None):
        '''
        must have binning set first.  this uses binning to set the window.

        offset and size are in binned pixels, so scale by bin to give real
        pixels.
        '''
        x0, y0 = None, None
        if offset:
            x0, y0 = offset

        # if x0, y0 are specified, then set the object's x0, y0
        # unbinned pixels
        if x0:
            self.x0 = x0 * self.binx

        if y0:
            self.y0 = y0 * self.biny

        sizex, sizey = None, None
        if offset:
            sizex, sizey = offset

        if sizex:
            # convert to real pixels, figure out final size on chip, scale back
            # to binned pixels
            sizex = self._iround(float(sizex*self.binx))
        else:
            sizex = self._iround(float(self.sizex) * self.binx)

        if sizey:
            # convert to real pixels, figure out final size on chip, scale back
            # to binned pixels
            sizey = self._iround(float(sizey*self.biny))
        else:
            sizey = self._iround(float(self.sizey) * self.biny)
    
        # calculate if pixels availalble > size
        x1 = self.nx - self.x0
        if x1 < sizex:
            sizex = x1
        y1 = self.ny - self.y0
        if y1 < self.sizey:
            sizey = y1

        # scale back to binned
        self.sizex = self._iround (sizex / self.binx)
        self.sizey = self._iround (sizey / self.biny)

        # don't change the settings while camera is exposing!
        DEBUG('_setup_expose_image: set binning to %s, %s\n' % \
          (self.binx, self.biny), 0)
        try:
            self.alta_usb.setBinning(self.binx, self.biny)
            time.sleep(1)
            DEBUG('_setup_expose_image: set window to %s, %s, %s, %s\n' % \
            (self.x0, self.y0, self.x0 + self.sizex, self.y0 + self.sizey), 0)
            self.alta_usb.setWindow(self.x0, self.y0, self.sizex, self.sizey)
        except:
            pass

    def stop(self):
        print 'stop server'

    def expose(self, exptime, shutter, bin=None, offset=None, size=None, filename=None):
        '''
        offset and size are in binned pixels

        Return ERROR or OK

expose exptime=1.0 bin=1,1 offset=79,120 size=189,189 \
filename=/export/images/ecam/UT120428/e0012.fits
        '''

        try:
            if not self.alta_usb:
                # throw an exception
                #raise 'alta usb not open'
                DEBUG('ecamera expose: Camera is not available, quit')
                exposureState('not available', 0.0, 0.0)
                return

            if not filename:
                filename = self._image_number_write()
                # write it to event channel?
            self.integration = exptime

            #
            # must set binning and then window.  window depends on binning!
            #
            self._setBinning(bin)
            self._setWindow(offset, size)

            # call new_expose() which knows how to callback

            DEBUG('ecamera expose: calling new_expose')
            self.alta_usb.new_expose(exposureState, self.integration, filename)
            #self.alta_usb.expose(self.integration, filename)
            # TBD: check that image was written!  then update
            self.last_image = self.image_number
            self.image_number = self.image_number + 1
            if self.image_number > self.image_wrap:
                self.image_number = 0
        except:
            #if self.alta_usb:
            #    self.alta_usb = None
            print_exc()
            DEBUG(format_exc())
        DEBUG('ecamera expose: image number now %s' % (self.image_number))
        return self.reply

DEBUG('create ecamera!')

reply = os.popen('/Users/shack/bin/apogee_usb_reset').readline()
if reply.find('error') > -1:
    print 'error resetting USB, correct error and try again'
    print 'execute shack@shack:bin/apogee_reset_usb to test if okay'
    sys.exit(1)

DEBUG('ecamera created')

ecamera=ECamera()

with Pyro4.core.Daemon(host="shack.apo.nmsu.edu", port=51000) as daemon:
    uri=daemon.register(ecamera,'Ecamera.Hardware')
    try:
        ns = Pyro4.locateNS()
        ns.register ('Ecamera.Hardware',uri)
    except:
        pass
    print 'server uri is ', uri
    print("Server ready.")
    daemon.requestLoop(loopCondition=lambda: True)
    print 'server quit'

ecamera.disconnect()
