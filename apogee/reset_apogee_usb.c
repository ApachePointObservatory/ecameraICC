/*
 * apogee_usb_reset.c - find the apogee camera USB port and reset it.
 *
 * Returns 0 if everything okay
 * 1 - if not found
 * 2 - if configuration failed
 * 3 - if claim failed
 * 4 - if reset failed
 *
 * If found and still fails, then USB device is in use by someone else.
 */

#include <assert.h>
/* #include <sys/io.h> */
#include <sys/time.h>                                                           
#include <sys/resource.h>
#include <sys/ioctl.h>
#include <string.h>
#include <sched.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>


#include "usb.h"

#define VND_ANCHOR_LOAD_INTERNAL		0xA0
#define VND_APOGEE_CMD_BASE			0xC0
#define VND_APOGEE_STATUS			( VND_APOGEE_CMD_BASE + 0x0 )
#define VND_APOGEE_CAMCON_REG			( VND_APOGEE_CMD_BASE + 0x2 )
#define VND_APOGEE_BUFCON_REG			( VND_APOGEE_CMD_BASE + 0x3 )
#define VND_APOGEE_SET_SERIAL			( VND_APOGEE_CMD_BASE + 0x4 )
#define VND_APOGEE_SERIAL			( VND_APOGEE_CMD_BASE + 0x5 )
#define VND_APOGEE_EEPROM			( VND_APOGEE_CMD_BASE + 0x6 )
#define VND_APOGEE_SOFT_RESET			( VND_APOGEE_CMD_BASE + 0x8 )
#define VND_APOGEE_GET_IMAGE			( VND_APOGEE_CMD_BASE + 0x9 )
#define VND_APOGEE_STOP_IMAGE			( VND_APOGEE_CMD_BASE + 0xA )

#define USB_ALTA_VENDOR_ID	0x125c
#define USB_ALTA_PRODUCT_ID	0x0010
#define USB_DIR_IN  USB_ENDPOINT_IN
#define USB_DIR_OUT USB_ENDPOINT_OUT
struct usb_dev_handle	*g_hSysDriver;
struct usb_dev_handle *hDevice;
int ApnUsbReadReg( unsigned short FpgaReg, unsigned short *FpgaData );
int ApnUsbWriteReg( unsigned short FpgaReg, unsigned short FpgaData );

int resetUSB(usb_dev_handle *devh) {
    int rc;
    int bpoint = 0;

    do {
        rc = usb_reset(devh);

        ++bpoint;

        if (bpoint > 100) {
            rc = 1;
        }
    } while (rc < 0);
    return rc;
}

int main(int argc,char **argv)
{
	char deviceName[128];
    int rc;
	struct usb_bus *bus;
	struct usb_device *dev;
        int Success;
        unsigned short FpgaReg;
        unsigned short FpgaData;
	char string[256];
        unsigned char buf[64];
        unsigned char *cbuf;

	usb_init();

	usb_find_busses();
	usb_find_devices();

	int found = 0;

	/* find ALTA device */
	for(bus = usb_busses; bus && !found; bus = bus->next) {
		for(dev = bus->devices; !found && dev; dev = dev->next) {
			if (dev->descriptor.idVendor == USB_ALTA_VENDOR_ID && 
			    dev->descriptor.idProduct == USB_ALTA_PRODUCT_ID) {
				hDevice = usb_open(dev);
				if (hDevice) {
				    found = 1;
				}
			}
		}
	}

	if (!found) 
    {
        printf("error: apogee camera not found, power cycle camera?\n");
        exit(1);
    }
	rc = usb_set_configuration(hDevice, 0x1);
    if (rc)
    {
        /* printf("error: usb set configuration failed, rc %d\n", rc); */
        printf("error: camera must be in use by another program %d\n", rc);
        exit(2);
    }
	rc = usb_claim_interface(hDevice, 0x0);
    if (rc)
    {
        /* printf("usb claim interface failed, rc %d\n", rc); */
        printf("error: camera must be in use by another program %d\n", rc);
        exit(3);
    }
    rc = resetUSB(hDevice);
    if (rc)
    {
        /* printf("usb reset failed, rc %d\n", rc); */
        printf("error: camera must be in use by another program %d\n", rc);
        exit(4);
    }

    exit(0);
}
