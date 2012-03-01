import numpy as np
import pyfits

h, w = 512, 512
filename='ones.fits'

image = np.ndarray((h, w), dtype='float')
image.fill(1.0)
print image

hdu = pyfits.PrimaryHDU(image)
hdr = hdu.header
hdu.writeto(filename)
