#!/opt/local/bin/python
'''
internet service that reads and writes from standard io

knows these commands:
	doread
	dodark
	init
	setcam
	showstatus
	status
	expose
	dark
'''
import os
import re
import ConfigParser
import sys
import time
from traceback import format_exc

from debugLog_fli import DEBUG

import AltaUSB

import pyfli as fli
import numpy as np
from pyfits import PrimaryHDU

import math
BASE_DIRECTORY = '/export/images/forTron/echelle'
#BASE_DIRECTORY = '/home/arc'
#CONFIG = os.path.join(os.getenv('HOME'),'config/ecamera.ini')
CONFIG = '/home/arc/config/ecamera_fli.ini'
#CONFIG = '/home/arc/config/ecamera.ini'
END_OF_LINE = '\r\n'
OKAY = ' OK'

#
# Camera is in wrong state
#
class WrongState(Exception):
	pass

class ECamera:
	def __init__(self):
		self.image_name = 'gimg%04d.fits'
		self.image_directory = '/export/images/forTron/guider'
#		self.image_directory = '/home/arc'
		self.image_wrap = 9999
		self.x0 = self.y0 = 0
		self.temperature = 0.0
		self.last_image = None
		self.integration = 0.0

		self.ny = self.nx = 512
		self.max_bin_x = 8
		self.max_bin_y = 512
		self.name = ''
		self.sizex = 512
		self.sizey = 512
		self.biny = 1
		self.binx = 1
		self.noise_units = 'electrons/sec/pixel'
		self.dark_current_units = 'electrons/sec/pixel'
		self.noise = 1
		self.dark_current = 1

		self.read_config()
		try:
			if 'alta' == self.camera :
				self.alta_usb = AltaUSB.AltaUSB()
			elif 'fli' == self.camera :
				self.fli_usb = fli.FLIOpen ('/dev/fliusb0', 'usb', 'camera')
			else :
				DEBUG('config: no or illegal camera defined')
		except:
			if 'alta' == self.camera :
				self.alta_usb = None
			elif 'fli' == self.camera :
				self.fli_usb = None
			else :
				DEBUG('camera setup failed')
			DEBUG(format_exc())
		self.reply = ''
		self.image_number = 0
		try:
			self.image_number_init()
		except:
			DEBUG(format_exc())
			sys.stdout.write(format_exc() + END_OF_LINE)
			sys.stdout.flush()

		# software setup, now be sure hardware is set right
		if 'alta' == self.camera and self.alta_usb:
			self.alta_usb.setCooler(self.temperature)
			DEBUG('camera set to alta')
		elif 'fli' == self.camera and None != self.fli_usb:
			fli.setTemperature (self.fli_usb, self.temperature)
			DEBUG('camera set to fli')
		else :
			DEBUG('camera temperature: no camera defined')

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
			self.image_directory = config.get('ecamera','image directory')
			self.image_directory = os.path.expandvars(self.image_directory)
			self.image_wrap = config.getint('ecamera','image wrap')
			self.image_name = config.get('ecamera','image name')
			self.camera = config.get('ecamera', 'camera')
			DEBUG('camera = %s' % self.camera)

			self.nx = config.getint(self.camera, 'nx')
			self.ny = config.getint(self.camera, 'ny')
			self.noise = config.getfloat(self.camera, 'noise')
			self.dark_current = config.getfloat(self.camera, 'dark current')
			self.max_bin_x = config.getint(self.camera, 'max_bin_x')
			self.max_bin_y = config.getint(self.camera, 'max_bin_y')
			self.noise_units = config.get(self.camera, 'noise units')
			self.dark_current_units = config.get(self.camera, 'dark current units')
			self.temperature = config.getfloat(self.camera, 'temperature')
			self.name = config.get(self.camera, 'name')
		except:
			# This should not happen! It is a broken configuration
			DEBUG(format_exc())

	def _image_info(self):
		if 'alta' == self.camera and self.alta_usb:
			self.alta_usb.coolerStatus()
			message = '%d %d %d %d %d %d %f 1 %f' % \
				(self.binx, self.biny, self.x0, self.y0, self.sizex,
				self.sizey, self.integration, self.alta_usb.read_TempCCD())
		elif 'fli' == self.camera and None != self.fli_usb:
			message = '%d %d %d %d %d %d %f 1 %f' % \
				(self.binx, self.biny, self.x0, self.y0, self.sizex,
				self.sizey, self.integration, fli.getTemperature (self.fli_usb))
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

	#utility functions
	# Keep in mind the rotation and translation is not cummutative, order or transformation matters!
	# Rotate point (x,y) an angle a about the origin and then translates by h,k to (x',y')
	def homogeneous_rot_trans(self,vector, translate, angle):	
		# Want to translate array about h, k and rotate by angle in degrees
		h, k = translate
		theta = np.radians(angle)	
		# Homogeneous coordinate translation rotation matrix. Rotation is clockwise
		R = np.matrix([[np.cos(theta), -np.sin(theta),  h],[np.sin(theta),  np.cos(theta),  k], [0,              0,              1]])
		return np.dot(R, vector)


	#rotate point (x',y') an angle a about the origin and then translates by -h,-k back to (x,y)
	def homogeneousT_rot_trans(self,vector, translate, angle):
		# Want to translate array about h, k and rotate by angle in degrees
		h, k = translate
		theta = np.radians(angle)
		# Homogeneous coordinate translation rotation matrix. Rotation is clockwise
		Rt = np.matrix([[ np.cos(theta), np.sin(theta),  -h * np.cos(theta) - k * np.sin(theta)], [-np.sin(theta), np.cos(theta),   h * np.sin(theta) - k * np.cos(theta)], [0,              0,               1]])
		return np.dot(Rt, vector)
	

	# Translate point (x,y) by h,k to (x',y') then rotate an angle a about the origin
	def homogeneous_trans_rot(self,vector, translate, angle):
		# Want to translate array about h, k and rotate by angle in degrees
		h, k = translate
		theta = np.radians(angle)		
		# Homogeneous coordinate translation rotation matrix. Rotation is clockwise
		R = np.matrix([[np.cos(theta), -np.sin(theta),  h * np.cos(theta) - k * np.sin(theta)],[np.sin(theta),  np.cos(theta),  h * np.sin(theta) + k * np.cos(theta)],[0,              0,              1]])
		return np.dot(R, vector)


	# Translate point (x',y') by -h,-k back to (x,y) then rotate and angle a about the origin
	def homogeneousT_trans_rot(self,vector, translate, angle):
		# Want to translate array about h, k and rotate by angle in degrees
		h, k = translate
		theta = np.radians(angle)
		# Homogeneous coordinate translation rotation matrix. Rotation is clockwise
		Rt = np.matrix([[ np.cos(theta), np.sin(theta),  -h],[-np.sin(theta), np.cos(theta),  -k],[0,              0,               1]])
		return np.dot(Rt, vector)



	def _setup_image(self, line):
		'''
		The input window is specified in binned pixels.

		The documentation says that the region of interest, ROI, is
		defined by an unbinned offset, and then binned rows and columns.

		INI files settings: columns=530 imgcols=512 bic=4

		a. For a full frame image binned 1:1, the values of BIC_count,
			Pixel_count and AIC_count are as follows;

			BIC_count = 4 (from ini file)
			Pixel_count = 512 (from ini file)
			AIC_count = 530 - 512 - 4 = 14


		b. For a sub-frame image 50 pixels wide located at a column
			offset= 100 ccd columns, binned 2:2:

			bic = 4 (from ini file) + 100 = 104
			pixel_count = 50 / 2 = 25
			aic count = 530 -104 - 50 = 376

		The offsets, x0, y0 are in unbinned pixels. If no pixels are skipped,
		then x0 and y0 are 0, so 0 based
		'''
		try:
			DEBUG('_setup_image: ...%s...\n' % (line), 0)
			command, integration, binx, biny, ctrx, ctry, sizex, sizey = line.split()
			DEBUG('_setup_image: ctrx %s, sizex %s:ctry %s, sizey %s' % (ctrx, sizex, ctry, sizey))
			self.integration = float(integration)
			self.binx = int(binx)
			self.biny = int(biny)
		



			#another shane test
			#ctrx=256
			#crty=256
			flipY = ctrx
			flipX = ctry

			ctrx=flipY
			ctry=flipX
			# assume ctr, size values are binned pixels
			ctrx = float(ctrx)*self.binx
			ctry = float(ctry)*self.biny


			self.sizex = self._iround(float(sizex)*self.binx)
			self.sizey = self._iround(float(sizey)*self.biny)


			# check for zero sized image. happens with tcc gcam doread
			if self.sizex <= 0:
				self.sizex = ctrx * 2
			if self.sizey <= 0:
				self.sizey = ctry * 2





			#not sure what this is doing
			# x0, y0 are unbinned pixels
			self.x0 = self._iround (ctrx - self.sizex / 2)
			if self.x0 < 0:
				# should adjust sizex too!
				self.x0 = 0
			self.y0 = self._iround (ctry - self.sizey / 2)
			if self.y0 < 0:
				# should adjust sizey too!
				self.y0 = 0


			#testing remove later
			# calculate if pixels availalble > size
			x1 = self.nx - self.x0
			if x1 < self.sizex:
				self.sizex = x1
			y1 = self.ny - self.y0
			if y1 < self.sizey:
				self.sizey = y1
			self.sizex = self._iround (self.sizex / self.binx)
			self.sizey = self._iround (self.sizey / self.biny)
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.setBinning(self.binx, self.biny)
			elif 'fli' == self.camera and None != self.fli_usb:
				# fli.setHBin (self.fli_usb, self.binx)
				# fli.setVBin (self.fli_usb, self.biny)
				# Image is rotated 270 degrees
				fli.setHBin (self.fli_usb, self.biny)
				fli.setVBin (self.fli_usb, self.binx)
			else :
				DEBUG('_setup_image: set binning: no camera defined')
			time.sleep(1)
			DEBUG('_setup_image: set window to %s, %s, %s, %s\n' % \
				(self.x0, self.y0, self.x0 + self.sizex, self.y0 + self.sizey))
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.setWindow(self.x0, self.y0, self.sizex, self.sizey)
			elif 'fli' == self.camera and None != self.fli_usb:
				#added b y shane to fix the rotation ecamera PR.  Did a lot of work to rotate the frame, saved that to ecamera.bill.st.py.
				#this now shows just the frame itself.  it does march, and I am not sure why working on that 7-8-2019
				DEBUG("Sending this to the fli.setImageArea y0: %s, x0: %s, sizey+y0: %s, sizex+x0:%s" % (self.y0, self.x0, self.sizey+self.y0, self.sizex+self.x0),0)
				#this is needed so because the fli camera origin is bottom right I think and it calculates funny with our values from our subframe window. hence
				#all the oddity


				DEBUG("BINNING: %s, %s" % (self.binx, self.biny), 0)
				binValue = 512/self.binx
				
				offset=(binValue-(self.x0+self.sizex))
				#fli.setImageArea(self.fli_usb, self.y0, binValue-(self.x0+self.sizex), self.y0+self.sizey, self.sizex+offset)
				fli.setImageArea(self.fli_usb, self.y0, binValue-(self.x0+self.sizex), self.y0+self.sizey, self.sizex+offset)
	
				DEBUG("Final image area: y0: %s, binValue-(x0+sizex): %s, y0+sizey: %s, sizex+offset: %s" % (self.y0, binValue-(self.x0+self.sizex), self.y0+self.sizey, self.sizex+offset))


				#flipping around below fails with values of:
				#x0: 0, y0: 106, sizey+y0: 439, sizex+x0: 512
				#2019-07-23 17:29:48 TU02.shane 55 ecam w debug="camera shape does not agree with dark, cam=(512, 303) dark=(406, 303)"
				#fli.setImageArea(self.fli_usb, self.x0, self.y0, self.x0+self.sizex, self.y0+self.sizey)
			else :
				DEBUG('_setup_image: set window: no camera defined')
			self.reply = self._image_info() + OKAY + END_OF_LINE
		except WrongState:
			DEBUG('_setup_image: WrongState: camera timed out - reset it')
			# the camera timed out somehow - reset it
			if 'alta' == self.camera and self.alta_usb:
				del self.alta_usb
				self.alta_usb = AltaUSB.AltaUSB()
				# give a little bit of time to let camera get ready?
				time.sleep(2)
				if self.alta_usb:
					self.alta_usb.setCooler(self.temperature)
			elif 'fli' == self.camera and None != self.fli_usb:
				fli.FLIClose (self.fli_usb)
				del self.fli_usb
				# give a little bit of time to let camera get ready?
				time.sleep(2)
				self.fli_usb = fli.FLIOpen ('/dev/fliusb0', 'usb', 'camera')
				fli.setTemperature (self.fli_usb, self.temperature)
			else :
				DEBUG('_setup_image: restart camera: no camera defined')
			self.reply = 'RESTART CAMERA' + OKAY + END_OF_LINE
		except:
			DEBUG('_setup_image:\n%s' % format_exc())
			self.reply = 'ERROR' + OKAY + END_OF_LINE
			raise Exception('Camera Error')

	def _setup_expose_image(self, what, line, filename):
		'''
'expose exptime=1.0 bin=1,1 offset=79,120 size=189,189 filename=/export/images/ecam/UT120428/e0012.fits'

		The documentation says that the region of interest, ROI, is
		defined by an unbinned offset, and then binned rows and columns.

		INI files settings: columns=530 imgcols=512 bic=4

		. For a full frame image binned 1:1, the values of BIC_count,
			Pixel_count and AIC_count are as follows;

			BIC_count = 4 (from ini file)
			Pixel_count = 512 (from ini file)
			AIC_count = 530 - 512 - 4 = 14


		b. For a sub-frame image 50 pixels wide located at a column
			offset= 100 ccd columns, binned 2:2:

			bic = 4 (from ini file) + 100 = 104
			pixel_count = 50 / 2 = 25
			aic count = 530 -104 - 50 = 376

		The offsets, x0, y0 are in unbinned pixels. If no pixels are skipped,
		then x0 and y0 are 0, so 0 based
		'''
		try:
			DEBUG('_setup_expose_image: ...%s...\n' % (line), 0)
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
			#DEBUG('_setup_expose_image: exptime %s, bin %s, size %s, offset %s, filename %s' % \
			#	(str(exptime), str(bin), str(size), str(offset), str(filename)))
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
			DEBUG('ST size y' % (self.sizey),0)
			DEBUG('_setup_expose_image: set binning to %s, %s\n' % (self.binx, self.biny), 0)
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.setBinning(self.binx, self.biny)
			elif 'fli' == self.camera and None != self.fli_usb:
				# The camera is rotated 270 degrees but binning should remain unchanged - wfk
				# fli.setHBin (self.fli_usb, self.binx)
				# fli.setVBin (self.fli_usb, self.biny)
				fli.setHBin (self.fli_usb, self.biny)
				fli.setVBin (self.fli_usb, self.binx)
			else :
				DEBUG('_setup_expose_image: set binning: no camera defined')
			DEBUG('_setup_expose_image: set window to %s, %s, %s, %s\n' % \
				(self.x0, self.y0, self.x0 + self.sizex, self.y0 + self.sizey), 0)
			time.sleep(1)
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.setWindow(self.x0, self.y0, self.sizex, self.sizey)
			elif 'fli' == self.camera and None != self.fli_usb:
				# fli.setImageArea (self.fli_usb, self.x0, self.y0, self.sizex, self.sizey)
				# The camera is rotated 270 degrees - wfk
				#fli.setImageArea (self.fli_usb, self.x0, (512 - (self.y0 + self.sizey * self.biny)), self.sizey, self.sizex)

				#shanes fix

				#additional shane has to check to see what is the bin size here...print that out when doing this test shot

				binValue = 512/self.binx


				offset=(binValue-(self.x0+self.sizex))

				fli.setImageArea(self.fli_usb, self.y0, binValue-(self.x0+self.sizex), self.sizey+self.y0, self.sizex+offset)

			else :
				DEBUG('_setup_expose_image: set window: no camera defined')
			self.reply = 'camFile=%s' % (filename) + END_OF_LINE
			self.reply = self.reply + OKAY + END_OF_LINE
		except:
			DEBUG('_setup_expose_image:\n%s' % format_exc())
			self.reply = 'ERROR' + OKAY + END_OF_LINE
			raise Exception('Camera Error')

	def _fli_expose (self, type, exp_time, filename) :
		''' Take one exposure with the FLI camera
			type - 'dark' or 'normal'
			exp_time - exposure time in seconds
			filename - name of the FITS file
		'''
		fli.setFrameType (self.fli_usb, type)
		fli.setNFlushes (self.fli_usb, 1)
		fli.setExposureTime (self.fli_usb, int (1000.0 * exp_time))
#		DEBUG('_fli_expose: exposure setup')
#		DEBUG('_fli_expose: Visible area: %s' % str(fli.getVisibleArea (self.fli_usb)))
#		DEBUG('_fli_expose: Readout dimensions: %s' % str(fli.getReadoutDimensions (self.fli_usb)))

		start_time = time.time()
		fli.exposeFrame (self.fli_usb)
#		DEBUG('_fli_expose: exposure started')

		while 0 != fli.getExposureStatus (self.fli_usb) :
#			DEBUG('_fli_expose: waiting for exposure to finish (getExposureStatus() == 0)')
			time.sleep (1)

		data = fli.grabFrame (self.fli_usb)
		# Image is rotated 270 degrees from Apogee camera, rot90 x 3 - WFK

		data = np.rot90(data, 3)



#		DEBUG('_fli_expose: exposure frame grabbed')

#	Populate FITS header and write file

		hdu = PrimaryHDU (data)
		hdr = hdu.header
		hdr['BSCALE'] = (1.0)
		hdr['BZERO'] = (32768.0)
		hdr['BEGX'] = (self.x0+1)
		hdr['BEGY'] = (self.y0+1) # +1
		hdr['FULLX'] = (512)
		hdr['FULLY'] = (512)
		hdr['BINX'] = (self.binx)
		hdr['BINY'] = (self.biny)
		hdr['EXPTIME'] = (exp_time)
		hdr['CAMNAME'] = ('USB FLI Camera', 'Camera used for this image')
		hdr['CAMID'] = (2)
		hdr['CAMTEMP'] = (fli.getTemperature (self.fli_usb), 'degrees C')
		hdr['DATE-OBS'] = (time.strftime ('%Y-%m-%d %H:%M:%SZ', time.gmtime (start_time)), 'TAI Date-Time CCD was read')

		hdu.writeto (filename)
		del data, hdu, hdr
#		DEBUG('_fli_expose: exposure written to file')

	def _doread (self, line):
		'''
		wrap doread with attempts to reset the system and if that fails
		execute an init
		'''
		count = 2
		while count > 0:
			try:
				return self.doread(line)
				break
			except WrongState:
				DEBUG(format_exc(), 0)
			time.sleep(1.0)
		count -= 1
		DEBUG('_doread: calling usb doInit()')
		if 'alta' == self.camera and self.alta_usb:
			self.alta_usb.doInit()

		# try 1 more time
		return self.doread(line)

	def doread(self, line):
		'''
		Exceptions
			Camera Error from _setup_image()
			NFS errors
		'''

		self.reply = ''

		if 'alta' == self.camera and self.alta_usb:
			if not self.alta_usb:
				self.reply = self._image_info()
				self.reply = self.reply + OKAY + END_OF_LINE
				return self.reply

		try:
			filename = self.image_number_write()
			self._setup_image(line)
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.expose(self.integration, filename)
			elif 'fli' == self.camera and None != self.fli_usb:
				self._fli_expose ('normal', self.integration, filename)
			else :
				DEBUG('_doread: no camera defined')
			self.last_image = self.image_number
			self.image_number = self.image_number + 1
			if self.image_number > self.image_wrap:
				self.image_number = 0
		except:
			# alta_usb.expose error? wrong state?
			#
			# reset pixel processing engines
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.ResetSystem()
			DEBUG(format_exc(), 0)
			raise WrongState()
		DEBUG('_doread: image number now %s' % (self.image_number))
		return self.reply

	def setcam(self, line):
		'''
			user function
		'''
		ccd_temp = 0.0
		if 'alta' == self.camera and self.alta_usb:
			if self.alta_usb:
				self.alta_usb.coolerStatus()
				ccd_temp = self.alta_usb.read_TempCCD()
			self.reply = '1 "USB Apogee Camera" 512 512 16 %.2f %d '
			self.reply = self.reply % (ccd_temp, self.last_image)
		elif 'fli' == self.camera and None != self.fli_usb:
			ccd_temp =fli.getTemperature (self.fli_usb)
			self.reply = '1 "USB FLI Camera" 512 512 16 %.2f %d '
			self.reply = self.reply % (ccd_temp, self.last_image)
		else :
			self.reply = '0 "no camera defined" '
			DEBUG('setcam: no camera defined')
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
		self.reply = ''
		if 'alta' == self.camera and self.alta_usb:
			if self.alta_usb:
				self.alta_usb.coolerStatus()
				ccd_temp = self.alta_usb.read_TempCCD()
			self.reply = '1 "USB Apogee Camera" 512 512 16 %.2f %d '
			self.reply = self.reply % (ccd_temp, self.last_image)
		elif 'fli' == self.camera and None != self.fli_usb:
			ccd_temp =fli.getTemperature (self.fli_usb)
			self.reply = '1 "USB FLI Camera" 512 512 16 %.2f %d '
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

		if 'alta' == self.camera and self.alta_usb:
			if not self.alta_usb:
				self.reply = self._image_info()
				self.reply = self.reply + OKAY + END_OF_LINE
				return self.reply

		try:
			filename = self.image_number_write()
			self._setup_image(line)
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.dark (self.integration, filename)
			elif 'fli' == self.camera and None != self.fli_usb:
				self._fli_expose ('dark', self.integration, filename)
			else :
				DEBUG('dodark: no camera defined')
			self.last_image = self.image_number
			self.image_number = self.image_number + 1
			if self.image_number > self.image_wrap:
				self.image_number = 0
		except:
			DEBUG(format_exc(), 0)
			#if self.alta_usb:
			#	self.alta_usb = None
		return self.reply

	def status(self, line):
		if 'alta' == self.camera and self.alta_usb:
			if not self.alta_usb:
				return 'ERROR' + OKAY + END_OF_LINE
		elif 'fli' == self.camera and None == self.fli_usb:
			return 'ERROR' + OKAY + END_OF_LINE
		reply = ''
		if 'alta' == self.camera and self.alta_usb:
			self.cooler_status = self.alta_usb.coolerStatus()
			ccd_temp = self.alta_usb.read_TempCCD()
		elif 'fli' == self.camera and None != self.fli_usb:
			ccd_temp =fli.getTemperature (self.fli_usb)
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

		if 'alta' == self.camera and self.alta_usb:
			if not self.alta_usb:
				# this should be an error
				self.reply = 'camFile=%s' % (self.image_number_write()) + END_OF_LINE
				return self.reply

		try:
			filename = self.image_number_write()
			self._setup_expose_image('expose', line, filename)
			DEBUG('ecamera expose: calling new_expose')
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.new_expose(sys.stdout, self.integration, filename)
			elif 'fli' == self.camera and None != self.fli_usb:
				self._fli_expose ('normal', self.integration, filename)
			else :
				DEBUG('expose: no camera defined')
			# TBD: check that image was written! then update
			self.last_image = self.image_number
			self.image_number = self.image_number + 1
			if self.image_number > self.image_wrap:
				self.image_number = 0
		except:
			#if self.alta_usb:
			#	self.alta_usb = None
			DEBUG('ecamera expose:\n'+format_exc(), 0)
		DEBUG('ecamera expose: image number now %s' % (self.image_number))
		return self.reply

	def dark(self, line):
		'''
		Return ERROR or OK
		'''
		self.reply = ''

		if 'alta' == self.camera and self.alta_usb:
			if not self.alta_usb:
				# this should be an error
				self.reply = 'camFile=%s' % (self.image_number_write()) + END_OF_LINE
				return self.reply

		try:
			filename = self.image_number_write()
			self._setup_expose_image('dark', line, filename)
			if 'alta' == self.camera and self.alta_usb:
				self.alta_usb.new_expose(self.integration, filename)
			elif 'fli' == self.camera and None != self.fli_usb:
				self._fli_expose ('dark', self.integration, filename)
			else :
				DEBUG('dark: no camera defined')
			# TBD: check that image was written! then update
			self.last_image = self.image_number
			self.image_number = self.image_number + 1
			if self.image_number > self.image_wrap:
				self.image_number = 0
		except:
			#if self.alta_usb:
			#	self.alta_usb = None
			DEBUG(format_exc(), 0)
		DEBUG('image number now %s' % (self.image_number))
		return self.reply

#
# Start ECamera software
#
DEBUG('create ecamera!')

#reply = os.popen('sudo /usr/local/bin/reset_apogee_usb').readline()
# set permissions
#if reply.find('error') > -1:
#	sys.stdout.write('ecamera error: %s, power cycle and restart nubs' % (reply))
ecamera = ECamera()

DEBUG('ecamera created')

commands = {
	# tcc camera interface
	'doread' :	ecamera._doread,
	'dodark':	ecamera.dodark,
	'init':		ecamera._init,
	'setcam':	ecamera.setcam,
	'showstatus': ecamera.showstatus,
	# newer camera interface
	'status':	ecamera.status,
	'expose':	ecamera.expose,
	'dark':		ecamera.dark,
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
				# doread can throw an exception on USB read
				sys.stdout.write('ERROR' + OKAY + END_OF_LINE)
				DEBUG(format_exc(), 0)
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
