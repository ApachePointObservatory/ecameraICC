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
from traceback import format_exc

from debugLog import DEBUG
import AltaUSB

BASE_DIRECTORY = '/export/images/forTron/echelle'
CONFIG = os.path.join(os.getenv('HOME'),'config/ecamera.ini')
END_OF_LINE = '\r\n'
OKAY = ' OK'

class ECamera:
    def __init__(self):
        self.image_name = 'gimg%04d.fits'
        self.image_directory = '/export/images/forTron/guider'
        self.image_wrap = 9999
        self.x0 = self.y0 = 0
        self.temperature = 0.0
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
        
        try:
            self.alta_usb = AltaUSB.AltaUSB()
        except:
            self.alta_usb = None
            DEBUG(format_exc())
        self.reply = ''
        self.read_config()
        self.image_number = 0
        try:
            self.image_number_init()
        except:
            DEBUG(format_exc())
            sys.stdout.write(format_exc() + END_OF_LINE)
            sys.stdout.flush()
            
        # software setup, now be sure hardware is set right
        if self.alta_usb:
            self.alta_usb.setCooler(self.temperature)

    def _init(self, unused):
        '''
        really should be an inline function.
        '''
        return OKAY + END_OF_LINE

    def image_number_init (self):
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
                    self.image_number_write()
                else:
                    self.last_image = 0
                    self.image_number = 0
                    DEBUG('image_number_init() search fails ...%s...' % \
                        (last_file), 0)
            else:
                self.last_image = 0
                self.image_number = 0

    def image_number_write(self):
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
            self.temperature = config.getfloat('alta', 'temperature')
            self.name = config.get('alta', 'name')
            self.image_directory = config.get('ecamera','image directory')
            self.image_directory = os.path.expandvars(self.image_directory)
            self.image_name = config.get('ecamera','image name')
        except:
            # This should not happen!  It is a broken configuration
            DEBUG(format_exc())
    
    def _image_info(self):
        if self.alta_usb:
            self.alta_usb.coolerStatus()
            message = '%d %d %d %d %d %d %f 1 %f' % \
                (self.binx, self.biny, self.x0, self.y0, self.sizex, 
                 self.sizey, self.integration, self.alta_usb.read_TempCCD())
        else:
            message = '0 0 0 0 0 0 0.0 0 0'
        message += ' image: binXY begXY sizeXY expTime camID temp' + END_OF_LINE
        return message

    def _iround(self, x):
        """
        iround(number) -> integer
        Round a number to the nearest integer
        """
        return int(round(x) - .5) + (x > 0)
    
    def _setup_image(self, line):
        '''
        The input window is specified in binned pixels.

        The documentation says that the region of interest, ROI, is
        defined by an unbinned offset, and then binned rows and columns.
        
        INI files settings: columns=530 imgcols=512 bic=4

        a. For a full frame image binned 1:1, the values of BIC_count, 
           Pixel_count and AIC_count are as follows; 

            BIC_count  = 4 (from ini file)
            Pixel_count = 512 (from ini file) 
            AIC_count = 530 - 512 - 4 = 14


        b. For a sub-frame image 50 pixels wide located at a column 
           offset= 100 ccd columns, binned 2:2:

            bic = 4 (from ini file) + 100 = 104 
            pixel_count = 50 / 2 = 25 
            aic count = 530 -104 - 50 = 376

        The offsets, x0, y0 are in unbinned pixels.  If no pixels are skipped, 
        then x0 and y0 are 0, so 0 based
        '''
        try:
            DEBUG('...%s...\n' % (line), 0)
            command, integration, binx, biny, ctrx, ctry, sizex, sizey = line.split()
            DEBUG('ctrx %s, sizex %s' % (ctrx, sizex))
            self.integration = float(integration)
            self.binx = int(binx)
            self.biny = int(biny)
            # assume ctr, size values are binned pixels
            ctrx = float(ctrx)*self.binx
            ctry = float(ctry)*self.biny
            self.sizex = self._iround(float(sizex)*self.binx)
            self.sizey = self._iround(float(sizey)*self.biny)
            # check for zero sized image.  happens with tcc gcam doread
            if self.sizex <= 0:
                self.sizex = ctrx * 2
            if self.sizey <= 0:
                self.sizey = ctry * 2
            # x0, y0 are unbinned pixels
            self.x0 = self._iround (ctrx - self.sizex / 2)
            if self.x0 < 0:
                # should adjust sizex too!
                self.x0 = 0
            self.y0 = self._iround (ctry - self.sizey / 2)
            if self.y0 < 0:
                # should adjust sizey too!
                self.y0 = 0
            DEBUG('ctrx %s, sizex/2 %s, x0 %s' % (ctrx, self.sizex/2, self.x0))
            # calculate if pixels availalble > size
            x1 = self.nx - self.x0
            if x1 < self.sizex:
                self.sizex = x1
            y1 = self.ny - self.y0
            if y1 < self.sizey:
                self.sizey = y1
            self.sizex = self._iround (self.sizex / self.binx)
            self.sizey = self._iround (self.sizey / self.biny)
            DEBUG('set binning to %s, %s\n' % (self.binx, self.biny), 0)
            self.alta_usb.setBinning(self.binx, self.biny)
            DEBUG('set window to %s, %s, %s, %s\n' % \
                (self.x0, self.y0, self.x0 + self.sizex, self.y0 + self.sizey), 0)
            time.sleep(1)
            self.alta_usb.setWindow(self.x0, self.y0, self.sizex, self.sizey)
            self.reply = self._image_info()
            self.reply = self.reply + OKAY + END_OF_LINE
        except:
            DEBUG(format_exc())
            self.reply = 'ERROR' + END_OF_LINE
            raise Exception('Camera Error')
    
    def _setup_expose_image(self, what, line, filename):
        '''
'expose exptime=1.0 bin=1,1 offset=79,120 size=189,189 filename=/export/images/ecam/UT120428/e0012.fits'

        The documentation says that the region of interest, ROI, is
        defined by an unbinned offset, and then binned rows and columns.
        
        INI files settings: columns=530 imgcols=512 bic=4

        a. For a full frame image binned 1:1, the values of BIC_count, 
           Pixel_count and AIC_count are as follows; 

            BIC_count  = 4 (from ini file)
            Pixel_count = 512 (from ini file) 
            AIC_count = 530 - 512 - 4 = 14


        b. For a sub-frame image 50 pixels wide located at a column 
           offset= 100 ccd columns, binned 2:2:

            bic = 4 (from ini file) + 100 = 104 
            pixel_count = 50 / 2 = 25 
            aic count = 530 -104 - 50 = 376

        The offsets, x0, y0 are in unbinned pixels.  If no pixels are skipped, 
        then x0 and y0 are 0, so 0 based
        '''
        try:
            DEBUG('...%s...\n' % (line), 0)
            bin = 1, 1
            offset = 0, 0
            size = 512, 512
            exptime = 0.0
            filename = self.image_number_write()
            #obj = re.search('expose (exptime=\d+\.\d+) (bin=\d+,\d+)\
            #(offset=\d+,\d+) (size=\d+,\d+) (filename=[a-zA-Z0-9_\.\/]+).*', line)
            obj = re.search(
'%s\W+(exptime=\d+\.\d+)\W+(bin=\d+,\d+)\W+(offset=\d+,\d+)\W+(size=\d+\.?\d*,\d+\.?\d*).*' % (what),
                line)
            if obj:
                for group in obj.groups():
                    exec(group)
            #DEBUG('exptime %s, bin %s, size %s, offset %s, filename %s' % \
            #    (str(exptime), str(bin), str(size), str(offset), str(filename)))
            DEBUG('_setup_expose_image: exptime %s, bin %s, size %s, offset %s' % \
                (str(exptime), str(bin), str(size), str(offset)))
            self.integration = exptime
            self.binx = bin[0]
            self.biny = bin[1]
            # assume ctr, size values are binned pixels
            self.sizex = self._iround(float(size[0])*self.binx)
            self.sizey = self._iround(float(size[1])*self.biny)
            # x0, y0 are unbinned pixels
            self.x0 = offset[0] * self.binx
            self.y0 = offset[1] * self.biny
            # calculate if pixels availalble > size
            x1 = self.nx - self.x0
            if x1 < self.sizex:
                self.sizex = x1
            y1 = self.ny - self.y0
            if y1 < self.sizey:
                self.sizey = y1
            self.sizex = self._iround (self.sizex / self.binx)
            self.sizey = self._iround (self.sizey / self.biny)
            DEBUG('_setup_expose_image: set binning to %s, %s\n' % (self.binx, self.biny), 0)
            self.alta_usb.setBinning(self.binx, self.biny)
            DEBUG('_setup_expose_image: set window to %s, %s, %s, %s\n' % \
              (self.x0, self.y0, self.x0 + self.sizex, self.y0 + self.sizey), 0)
            time.sleep(1)
            self.alta_usb.setWindow(self.x0, self.y0, self.sizex, self.sizey)
            self.reply = 'camFile=%s' % (filename) + END_OF_LINE
            self.reply = self.reply + OKAY + END_OF_LINE
        except:
            DEBUG(format_exc())
            self.reply = 'ERROR' + END_OF_LINE
            raise Exception('Camera Error')

    def doread(self, line):
        '''
        Exceptions
            Camera Error from _setup_image()
            NFS errors
        '''

        self.reply = ''

        if not self.alta_usb:
            self.reply = self._image_info()
            self.reply = self.reply + OKAY + END_OF_LINE
            return self.reply

        try:
            filename = self.image_number_write()
            self._setup_image(line)
            self.alta_usb.expose(self.integration, filename)
            self.last_image = self.image_number
            self.image_number = self.image_number + 1
            if self.image_number > self.image_wrap:
                self.image_number = 0
        except:
            # alta_usb.expose error?  wrong state?
            #
            # reset pixel processing engines
            self.alta_usb.ResetSystem()
            DEBUG(format_exc(), 0)
            raise Exception('Wrong State')
        DEBUG('image number now %s' % (self.image_number))
        return self.reply
    
    def setcam(self, line):
        '''
            user function
        '''
        ccd_temp = 0.0
        if self.alta_usb:
            self.alta_usb.coolerStatus()
            ccd_temp = self.alta_usb.read_TempCCD()
        self.reply = '1 "USB Apogee Camera" 512 512 16 %.2f %d '
        self.reply = self.reply % (ccd_temp, self.last_image)
        self.reply += "camera: ID# name sizeXY bits/pixel temp last FileNum"
        self.reply += END_OF_LINE
        self.reply += OKAY + END_OF_LINE

        return self.reply

    
    def showstatus(self, line):
        '''
            user function
showstatus
1 "PXL1024" 1024 1024 16 -20.89 318 "camera: ID# name sizeXY bits/pixel temp
lastFileNum"
1 1 0 0 0 0 nan 0 nan "image: binXY begXY sizeXY expTime camID temp"
8.00 1000 params: boxSize (FWHM units) maxFileNum

        '''
        ccd_temp = 0.0
        if self.alta_usb:
            self.alta_usb.coolerStatus()
            ccd_temp = self.alta_usb.read_TempCCD()
        self.reply = ''
        self.reply = '1 "USB Apogee Camera" 512 512 16 %.2f %d '
        self.reply = self.reply % (ccd_temp, self.last_image)
        self.reply += "camera: ID# name sizeXY bits/pixel temp last FileNum"
        self.reply += END_OF_LINE
        self.reply += self._image_info()
        self.reply += '0.00 %d params: boxSize (FWHM units) maxFileNum' % (self.image_wrap)
        self.reply += END_OF_LINE + OKAY + END_OF_LINE

        return self.reply

    def dodark(self, line):
        '''
        Exceptions
            Camera Error from _setup_image()
            NFS errors
        '''
        self.reply = ''

        if not self.alta_usb:
            self.reply = self._image_info()
            self.reply = self.reply + OKAY + END_OF_LINE
            return self.reply

        try:
            filename = self.image_number_write()
            self._setup_image(line)
            self.alta_usb.dark (self.integration, filename)
            self.last_image = self.image_number
            self.image_number = self.image_number + 1
            if self.image_number > self.image_wrap:
                self.image_number = 0
        except:
            DEBUG(format_exc(), 0)
            #if self.alta_usb:
            #    self.alta_usb = None
        return self.reply

    def status(self, line):
        if not self.alta_usb:
            return 'ERROR' + END_OF_LINE
        reply = ''
        self.cooler_status = self.alta_usb.coolerStatus()
        ccd_temp = self.alta_usb.read_TempCCD()
        reply += 'temp=%f' % (ccd_temp)
        reply += OKAY + END_OF_LINE
        return reply

    def expose(self, line):
        '''
        offset and size are in binned pixels

        Return ERROR or OK

expose exptime=1.0 bin=1,1 offset=79,120 size=189,189 \
filename=/export/images/ecam/UT120428/e0012.fits
        '''
        self.reply = ''

        if not self.alta_usb:
            # this should be an error
            self.reply = 'camFile=%s' % (self.image_number_write()) + END_OF_LINE
            return self.reply

        try:
            filename = self.image_number_write()
            self._setup_expose_image('expose', line, filename)
            DEBUG('ecamera expose: calling new_expose')
            self.alta_usb.new_expose(sys.stdout, self.integration, filename)
            # TBD: check that image was written!  then update
            self.last_image = self.image_number
            self.image_number = self.image_number + 1
            if self.image_number > self.image_wrap:
                self.image_number = 0
        except:
            #if self.alta_usb:
            #    self.alta_usb = None
            DEBUG(format_exc(), 0)
        DEBUG('ecamera expose: image number now %s' % (self.image_number))
        return self.reply

    def dark(self, line):
        '''
        Return ERROR or OK
        '''
        self.reply = ''

        if not self.alta_usb:
            # this should be an error
            self.reply = 'camFile=%s' % (self.image_number_write()) + END_OF_LINE
            return self.reply

        try:
            filename = self.image_number_write()
            self._setup_expose_image('dark', line, filename)
            self.alta_usb.new_expose(self.integration, filename)
            # TBD: check that image was written!  then update
            self.last_image = self.image_number
            self.image_number = self.image_number + 1
            if self.image_number > self.image_wrap:
                self.image_number = 0
        except:
            #if self.alta_usb:
            #    self.alta_usb = None
            DEBUG(format_exc(), 0)
        DEBUG('image number now %s' % (self.image_number))
        return self.reply

DEBUG('create ecamera!')

reply = os.popen('/Users/shack/bin/apogee_usb_reset').readline()
if reply.find('error') > -1:
    sys.stdout.write('ecamera error: %s, power cycle and restart nubs' % (reply))
ecamera = ECamera()

DEBUG('ecamera created')

commands = {
    # tcc camera interface
    'doread' :  ecamera.doread,
    'dodark':   ecamera.dodark,
    'init':     ecamera._init,
    'setcam':   ecamera.setcam,
    'showstatus': ecamera.showstatus,
    # newer camera interface
    'status':   ecamera.status,
    'expose':   ecamera.expose,
    'dark':     ecamera.dark
    }

def parse_line(parts):
    return

#sys.stdout.write ('doread 0.5 1 1 255.5 255.5 512 512\n')
#sys.stdout.flush()

#import datetime

def run():
    '''
    run for ever listening for standard in
    
    all commands are echoed, whatever reply output, and then
    an OK.
    '''
    
    while 1:
        input = sys.stdin.readline()
        if not input:
            DEBUG('read empty line\n', 0)
            break
        DEBUG(' input:...%s...' % (input), 0)
        
        buffer = input.strip()
        if not buffer:
            sys.stdout.write(OKAY + END_OF_LINE)
            sys.stdout.flush()
            DEBUG('output:' + OKAY, 0)
            continue
    
        if buffer in ['quit', 'QUIT']:
            break
    
        # echo the input
        sys.stdout.write('\n' + buffer + END_OF_LINE)
        sys.stdout.flush()
        DEBUG('output:'+buffer+END_OF_LINE, 0)
    
        command = buffer.split()[0]
        if command in commands:
            try:
                reply = commands[command](buffer)
                if reply:
                    sys.stdout.write(reply)
                DEBUG('output:'+reply.strip(), 0)
            except:
                # doread can through an exception on USB read
                sys.stdout.write('ERROR' + END_OF_LINE)
        else:
            sys.stdout.write(OKAY + END_OF_LINE)
            DEBUG('output:' + OKAY, 0)
        sys.stdout.flush()

try:
    DEBUG('starting ecamera, hello', 0)
    run()
    DEBUG('going away, bye', 0)
except:
    print format_exc()
