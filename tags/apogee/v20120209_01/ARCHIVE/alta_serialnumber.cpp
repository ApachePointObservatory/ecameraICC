/*  Program : test_alta.cpp
 *  Version : 2.0
 *  Author  : Dave Mills
 *  Copyright : The Random Factory 2004-2008
 *  License : GPL
 *
 */


#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <time.h>
#include "tcl.h"
#include "ApnCamera.h"
#include "ApogeeUsb/ApogeeUsb.h"
extern INTEL_HEX_RECORD alta2firmware;
CApnCamera *alta;


/* Main executable starts here -----------------------------------------------*/

int main (int argc, char **argv) 
{

	int status;
        char serialnumber[APN_USB_SN_BYTE_COUNT];
        long int snlen = APN_USB_SN_BYTE_COUNT+1;
        char *psn = &serialnumber[0];

        strcpy(serialnumber,argv[1]);

/*	Create the camera object , this will reserve memory */
	alta = (CApnCamera *)new CApnCamera();

	alta->InitDriver(1,0,0);

/*	Do a system reset to ensure known state, flushing enabled etc */
	alta->ResetSystem();

        if (strncmp(serialnumber,"read",4) == 0) {
           alta->GetCameraSerialNumber( psn,&snlen);
           printf("Serial number is %s\n",serialnumber);
        } else {
   	   alta->DownloadFirmware( &alta2firmware );
  	   alta->SetCameraSerialNumber( serialnumber, &snlen );
           printf("Power camera OFF now to complete serial number programming\n");
        }

        exit(0);
}


