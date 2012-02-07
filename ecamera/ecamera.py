#!/opt/local/bin/python
'''
internet service that reads and writes from standard io

knows these commands:
    doread
    dodark
    init
    setcam
'''
import os
import re
import ConfigParser
import sys
import time
from traceback import format_exc
import syslog
import logging

import AltaUSB

logging.basicConfig(filename='/tmp/ecamera.log',level=logging.DEBUG)

def DEBUG(message, level=0):
    #syslog.syslog(message.strip())
    logging.debug(message)
    return
    if message[-1] != '\n':
        message += '\n'
    sys.stdout.write('ecamera: ' + message)
    sys.stdout.flush()

BASE_DIRECTORY = '/export/images/forTron/echelle'
CONFIG = os.path.join(os.getenv('HOME'),'config/ecamera.ini')
END_OF_LINE = '\r\n'

class ECamera:
    def __init__(self):
        try:
            self.alta_usb = AltaUSB.AltaUSB()
        except:
            self.alta_usb = None
            DEBUG(format_exc())
        self.reply = ''
        DEBUG('here1')
        self.read_config()
        DEBUG('here2')
        self.image_number = 0
        DEBUG('here3')
        self.image_number_init()
        DEBUG('here4')

    def _init(self, unused):
        if self.alta_usb:
            self.alta_usb.CloseDriver()
            del self.alta_usb

        #
        # power cycle
        #
        try:
            DEBUG('here1')
            self.alta_usb = AltaUSB.AltaUSB()
            DEBUG('here2')
        except:
            self.alta_usb = None
        DEBUG('here3')
        return ' OK' + END_OF_LINE

    def image_number_init (self):
        '''
        setup image number
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
                    DEBUG('image_number_init() search fails ...%s...' % (last_file),\
                        0)
            else:
                self.last_image = 0
                self.image_number = 0

    def image_number_write(self):
        '''
        write image_number to last.image
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
            self.name = config.get('alta', 'name')
            self.image_directory = config.get('ecamera','image directory')
            self.image_directory = os.path.expandvars(self.image_directory)
            self.image_name = config.get('ecamera','image name')
        except:
            DEBUG(format_exc())
    
    def _image_info(self):
        if self.alta_usb:
            self.alta_usb.coolerStatus()
            message = '%d %d %d %d %d %d %f 1 %f' % \
                (self.binx, self.biny, self.x0, self.y0, self.sizex, self.sizey, \
                self.integration, self.alta_usb.read_TempCCD())
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
            self.integration = float(integration)
            self.binx = int(binx)
            self.biny = int(biny)
            # assume ctr, size values are binned pixels
            self.ctrx = float(ctrx)*self.binx
            self.ctry = float(ctry)*self.biny
            self.sizex = self._iround(float(sizex)*self.binx)
            self.sizey = self._iround(float(sizey)*self.biny)
            # x0, y0 are unbinned pixels
            self.x0 = self._iround (self.ctrx - self.sizex / 2)
            if self.x0 < 0:
                self.x0 = 0
            self.y0 = self._iround (self.ctry - self.sizey / 2)
            if self.y0 < 0:
                self.y0 = 0
            DEBUG('ctrx %s, sizex/2 %s, x0 %s' % (self.ctrx, self.sizex/2, self.x0))
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
            self.reply = self.reply + ' OK' + END_OF_LINE
        except:
            DEBUG(format_exc());
            self.reply = 'ERROR' + END_OF_LINE
            raise Exception('Camera Error')

    def doread(self, line):

        self.reply = ''

        if not self.alta_usb:
            self.reply = self._image_info() + END_OF_LINE
            self.reply += 'image: binXY begXY sizeXY expTime camID temp' + END_OF_LINE
            self.reply = self.reply + ' OK' + END_OF_LINE
            return self.reply

        filename = self.image_number_write()
        try:
            self._setup_image(line)
            self.alta_usb.expose(self.integration, filename)
            self.last_image = self.image_number
            self.image_number = self.image_number + 1
            if self.image_number > self.image_wrap:
                self.image_number = 0
        except:
            if self.alta_usb:
                self.alta_usb.CloseDriver()
                self.alta_usb = None
            DEBUG(format_exc(), 0);
        DEBUG('image number now %s' % (self.image_number))
        return self.reply
    
    def setcam(self, line):
        ccd_temp = 0.0
        if self.alta_usb:
            self.alta_usb.coolerStatus()
            ccd_temp = self.alta_usb.read_TempCCD()
        self.reply = ''
        self.reply = '1 "USB Apogee Camera" 512 512 16 %.2f %d '
        self.reply = self.reply % (ccd_temp, self.last_image)
        self.reply += "camera: ID# name sizeXY bits/pixel temp last FileNum"
        self.reply += END_OF_LINE
        self.reply += ' OK' + END_OF_LINE

        return self.reply

    def dodark(self, line):
        self.reply = ''

        if not self.alta_usb:
            self.reply = self._image_info() + END_OF_LINE
            self.reply += 'image: binXY begXY sizeXY expTime camID temp' + END_OF_LINE
            self.reply = self.reply + ' OK' + END_OF_LINE
            return self.reply

        filename = self.image_number_write()
        try:
            self._setup_image(line)
            self.alta_usb.dark (self.integration, filename)
            self.last_image = image_number
            self.image_number = self.image_number + 1
            if self.image_number > self.image_wrap:
                self.image_number = 0
        except:
            DEBUG(format_exc(), 0);
            if self.alta_usb:
                self.alta_usb.CloseDriver()
                self.alta_usb = None
        return self.reply

DEBUG('create ecamera!')

ecamera = ECamera()

DEBUG('ecamera created')

commands = {
    'doread' :  ecamera.doread,
    'dodark':   ecamera.dodark,
    'init':     ecamera._init,
    'setcam':   ecamera.setcam
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
            logging.debug('read empty line\n')
            break
        logging.debug(' input:...%s...' % (input))
        
        buffer = input.strip()
        if not buffer:
            sys.stdout.write(' OK'+END_OF_LINE)
            sys.stdout.flush()
            logging.debug('output:'+' OK')
            continue
    
        if buffer in ['q', 'Q']:
            break
    
        # echo the input
        sys.stdout.write('\n' + buffer + END_OF_LINE)
        sys.stdout.flush()
        logging.debug('output:'+buffer+END_OF_LINE)
    
        command = buffer.split()[0]
        if command in commands:
            reply = commands[command](buffer)
            sys.stdout.write(reply)
            logging.debug('output:'+reply.strip())
        else:
            sys.stdout.write(' OK'+END_OF_LINE)
            logging.debug('output:'+' OK')
        sys.stdout.flush()

try:
    logging.debug('starting ecamera, hello')
    run()
    logging.debug('going away, bye')
except:
    print format_exc()
