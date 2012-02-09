//////////////////////////////////////////////////////////////////////
//
// ApogeeUsbUpload.cpp    
//
// Copyright (c) 2003, 2004 Apogee Instruments, Inc.
//
// Functions for allowing updates to the USB device.  Some code
// based off of Cypress development kit.  All accesses to the 
// hardware go through the common ApnUsbCreateRequest() function.
//
//////////////////////////////////////////////////////////////////////

#include <assert.h>
#ifndef OSX
#ifndef OSXI
#include <sys/io.h>
#endif
#endif
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
#include <math.h>

#include "usb.h"
extern int usb_debug;

#include "stdafx.h"

/*#define HANDLE   unsigned long */
#define USHORT   unsigned short
#define PUCHAR   unsigned char *
#define APUSB_VERSION_MAJOR 1
#define APUSB_VERSION_MINOR 4

#ifndef APN_USB_TYPE
#define APN_USB_TYPE unsigned short
#endif


#define APOGEE_USB_DEVICE "/dev/usb/alta"
#define INVALID_HANDLE_VALUE  -1



#include "ApogeeUsb.h"
#include "ApogeeUsbErr.h"

#define MAX_INTEL_HEX_RECORD_LENGTH 16

typedef struct _INTEL_HEX_RECORD
{
	unsigned char	Length;
	unsigned short	Address;
	unsigned char	Type;
	unsigned char	Data[MAX_INTEL_HEX_RECORD_LENGTH];
} INTEL_HEX_RECORD, *PINTEL_HEX_RECORD;

extern usb_dev_handle *g_hSysDriver[APN_USB_MAXCAMERAS];
extern usb_dev_handle *g_hFilterDriver[APN_USB_MAXCAMERAS];


#include "ApogeeUsbUpload.h"

#include "ApnUsbSys.h"
//#include "ApogeeIoctl.h"

#define USB_ALTA_VENDOR_ID		0x125c
#define USB_ALTA_PRODUCT_ID		0x0010
#define USB_ASCENT_PRODUCT_ID		0x0020
#define USB_FILTERWHEEL_PRODUCT_ID	0x0100
#define USB_DIR_IN  USB_ENDPOINT_IN
#define USB_DIR_OUT USB_ENDPOINT_OUT
#define ULONG    unsigned int
#define BOOLEAN  unsigned int
#define USHORT   unsigned short
#define PUCHAR   unsigned char *
#define APUSB_VERSION_MAJOR 1
#define APUSB_VERSION_MINOR 4

#ifndef APN_USB_TYPE
#define APN_USB_TYPE unsigned short
#endif



/*
#ifdef _DEBUG
#define OutputAltaDebug( _X_ ) printf( _X_ )
#else
#define OutputAltaDebug( _X_ )
#endif
*/

/*
bool ApnUsbCreateRequest(	HANDLE			*hDevice,
							unsigned char	Request,
							bool			InputRequest,
							unsigned short	Index,
							unsigned short	Value,
							unsigned long	Length,
							unsigned char	*pBuffer )
{
	APN_USB_REQUEST	UsbRequest;
	BOOLEAN			Success;
	DWORD			BytesReceived;
	UCHAR			Direction;
	PUCHAR			pSendBuffer;
	ULONG			SendBufferLen;


	if ( InputRequest )
		Direction = REQUEST_IN;
	else
		Direction = REQUEST_OUT;

	UsbRequest.Request		= Request;
	UsbRequest.Direction	= Direction;
	UsbRequest.Index		= Index;
	UsbRequest.Value		= Value;

	if ( Direction == REQUEST_IN )
	{
		SendBufferLen	= sizeof(APN_USB_REQUEST);
		pSendBuffer		= new UCHAR[SendBufferLen];

		memcpy( pSendBuffer, 
				&UsbRequest, 
				sizeof(APN_USB_REQUEST) );
	}
	else
	{
		SendBufferLen	= sizeof(APN_USB_REQUEST) + Length;
		pSendBuffer		= new UCHAR[SendBufferLen];

		memcpy( pSendBuffer, 
				&UsbRequest, 
				sizeof(APN_USB_REQUEST) );

		memcpy( pSendBuffer + sizeof(APN_USB_REQUEST),
				pBuffer,
				Length );
	}

	Success = DeviceIoControl( *hDevice,
							   IOCTL_WDM_USB_REQUEST,
							   pSendBuffer,		// &UsbRequest,
							   SendBufferLen,	// sizeof(APN_USB_REQUEST),
							   pBuffer,
							   Length,
							   &BytesReceived,
							   NULL );

	delete [] pSendBuffer;

	if ( !Success )
		return false;
	
	return true;
}
*/

bool ApnUsbReadBufcon(unsigned short hDevice, unsigned short	RegNum, 
						unsigned char	*RegData )
{
	bool Success;


	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_BUFCON_REG,
								   true,
								   RegNum+BUFCON_BASE_ADDRESS,
								   0, 
								   16,
								   RegData );
	*/

   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_BUFCON_REG,
                                0, RegNum+BUFCON_BASE_ADDRESS, (char *)RegData, 16, 10000);

	return Success;
}


bool ApnUsbWriteBufcon(unsigned short hDevice, unsigned short	RegNum,
						unsigned char	RegData )
{
	bool			Success;
	unsigned char	TempData;

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_BUFCON_REG,
								   false,
								   RegNum+BUFCON_BASE_ADDRESS,
								   0, 
								   1,
								   &TempData );
	*/
   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_BUFCON_REG,
                                0, RegNum+BUFCON_BASE_ADDRESS, (char *)&TempData, 1, 10000);

	return Success;
}


bool ApnUsbReadEeprom(unsigned short hDevice, unsigned char	Bank,
						unsigned char	Chip,
						unsigned short	Address,
						unsigned long	Count,
						unsigned char	*pBuffer )
{
	bool			Success;
	unsigned short	Index;
	unsigned short	Value;

	Value	= (unsigned short)( (Bank<<8) | Chip );
	Index	= Address;

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_EEPROM,
								   true,
								   Index,
								   Value,
								   Count,
								   pBuffer );
	*/
   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_EEPROM,
                                Value, Index,(char *)pBuffer, Count, 10000);

	return Success;
}


bool ApnUsbWriteEeprom(unsigned short hDevice, unsigned char	Bank,
						unsigned char	Chip,
						unsigned short	Address,
						unsigned long	Count,
						unsigned char	*pBuffer )
{
	bool			Success;
	unsigned short	Index;
	unsigned short	Value;

	Value	= (unsigned short)( (Bank<<8) | Chip );
	Index	= Address;

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_EEPROM,
								   false,
								   Index,
								   Value,
								   Count,
								   pBuffer );
	*/
  	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_EEPROM,
                                Value, Index,(char *)pBuffer, Count, 10000);

	return Success;
}


bool ApnUsbReadEepromBuffer(unsigned short hDevice, unsigned char	StartingBank,
								unsigned char	StartingChip,
								unsigned short	StartingAddress,
								unsigned long	Count,
								unsigned char	*pBuffer )
{
	unsigned short	ChunkSize;
	unsigned short	RomAddress;
	unsigned char	BankNum;
	unsigned char	RomNum;
	unsigned char	*pRomBuffer;


	BankNum		= StartingBank;
	RomNum		= StartingChip;		// Select the I2C chip to start at
	RomAddress	= StartingAddress;
	pRomBuffer	= pBuffer;

	// If we're not starting on a ROM_CHUNK_SIZE boundary, then do a 1st
	// "catch-up" beat.
	if ( (RomAddress & (ROM_CHUNK_SIZE-1)) & ((Count+RomAddress) > ROM_CHUNK_SIZE) ) 
	{
		ChunkSize=ROM_CHUNK_SIZE-RomAddress;
		if ( !ApnUsbReadEeprom( hDevice, BankNum, RomNum, RomAddress, ChunkSize, pRomBuffer) ) 
		{
			// OutputAltaDebug( "ERROR: Failed 1st beat EEPROM read call." );
			return false;
		}

		Count -= ChunkSize;

		// Advance the write address, possibly to the next chip, or the next
		// bank of chips.
		pRomBuffer	+= ChunkSize;
		RomAddress	+= ChunkSize;
		
		if ( RomAddress >= ROM_SIZE )
		{
			RomAddress = 0;
			++RomNum;

			if ( RomNum == ROM_BANK_SIZE )
			{
				RomNum = 0;
				BankNum++;
			}
		}
	}

	// Mid-Beat. Once we've got to where the address is on a ROM_CHUNK_SIZE
	// boundary, do zero or more beats at the ROM_CHUNK_SIZE.

	while ( Count > ROM_CHUNK_SIZE )
	{
		ChunkSize = ROM_CHUNK_SIZE;
		
		if ( !ApnUsbReadEeprom( hDevice, BankNum, RomNum, RomAddress, ChunkSize, pRomBuffer) )
		{
			printf( "ERROR: Failed mid-beat EEPROM read call." );
			return false;
		}

		Count -= ChunkSize;

		// Advance the write address, possibly to the next chip, or the next
		// bank of chips.
		pRomBuffer	+= ChunkSize;
		RomAddress	+= ChunkSize;
		
		if ( RomAddress >= ROM_SIZE )
		{
			RomAddress = 0;		// After 1st beat, always start at address 0.
			RomNum++;			// Go to next ROM if needed
			
			if ( RomNum == ROM_BANK_SIZE )
			{
				RomNum = 0;
				++BankNum;
			}
		}
	}

	// At this point there's less than a ROM_CHUNK_SIZE remaining.
	// Do a final beat to close up.
	
	if ( Count )
	{
		if ( !ApnUsbReadEeprom( hDevice, BankNum, RomNum, RomAddress, Count, pRomBuffer) )
		{
			printf( "ERROR: Failed final EEPROM read call." );
			return false;
		}
	}

	return true;
}


bool ApnUsbWriteEepromBuffer(unsigned short hDevice, unsigned char	StartingBank,
								unsigned char	StartingChip,
								unsigned short	StartingAddress,
								unsigned long	Count,
								unsigned char	*pBuffer )
{
	unsigned short	ChunkSize;
	unsigned short	RomAddress;
	unsigned char	BankNum;
	unsigned char	RomNum;
	unsigned char	*pRomBuffer;


	BankNum		= StartingBank;
	RomNum		= StartingChip;		// Select the I2C chip to start at
	pRomBuffer	= pBuffer;
	RomAddress	= StartingAddress;

	// If we're not starting on a ROM_CHUNK_SIZE boundary, then do a 1st
	// "catch-up" beat.

	if ( (RomAddress & (ROM_CHUNK_SIZE-1)) & ((Count+RomAddress) > ROM_CHUNK_SIZE) ) 
	{
		printf( "catch up beat" );

		ChunkSize = ROM_CHUNK_SIZE - RomAddress;

		if ( !ApnUsbWriteEeprom( hDevice, BankNum, RomNum, RomAddress, ChunkSize, pRomBuffer) ) 
		{
			printf( "ERROR: Failed 1st beat EEPROM write call." );
			return(FALSE);
		}

		Count -= ChunkSize;
		
		// Advance the write address, possibly to the next chip, or the next
		// bank of chips.
		pRomBuffer	+= ChunkSize;
		RomAddress	+= ChunkSize;
		
		if (RomAddress >= ROM_SIZE) 
		{
			RomAddress = 0;
			++RomNum;
			if ( RomNum == ROM_BANK_SIZE ) 
			{
				RomNum = 0;
				BankNum++;
			}
		}
	}

	// Mid-Beat. Once we've got to where the address is on a ROM_CHUNK_SIZE
	// boundary, do zero or more beats at the ROM_CHUNK_SIZE.

	while ( Count > ROM_CHUNK_SIZE ) 
	{
		printf( "first beat" );

		ChunkSize = ROM_CHUNK_SIZE;
		
		if ( !ApnUsbWriteEeprom( hDevice, BankNum, RomNum, RomAddress, ChunkSize, pRomBuffer) ) 
		{
			printf( "ERROR:  Failed mid-beat EEPROM write call." );
			return false;
		}

		Count -= ChunkSize;
      
		// Advance the write address, possibly to the next chip, or the next
		// bank of chips.
		pRomBuffer += ChunkSize;
		RomAddress += ChunkSize;

		if ( RomAddress >= ROM_SIZE ) 
		{
			RomAddress = 0; // After 1st beat, always start at address 0.
			RomNum++;		// Go to next ROM if needed
	
			if ( RomNum == ROM_BANK_SIZE ) 
			{
				RomNum =0;
				++BankNum;
			}
		}
	}

	// At this point there's less than a ROM_CHUNK_SIZE remaining.
	// Do a final beat to close up.

	if ( Count ) 
	{
		if ( !ApnUsbWriteEeprom( hDevice, BankNum, RomNum, RomAddress, Count, pRomBuffer) ) 
		{
			printf( "ERROR:  Failed last EEPROM write call." );
			return false;
		}
	}	
	
	return true;
}


bool ApnUsbIdFlash(unsigned short hDevice, unsigned long	*pIdCode )
{
	bool Success; 
 
	printf( "In ApnUsbIdFlash" );

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_FLASHID,	// The request
								   true,				// Direction
								   0,					// wIndex
								   0,					// wValue
								   (USHORT)4,
								   (PUCHAR)pIdCode);	// Buffer for returned data
	*/
   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_FLASHID,
                                0, 0, (char *)pIdCode, 4, 10000);
	
	if (!Success) 
		printf( "WARNING: Failed ApnUsbIdFlash()." );
	
	return Success;
}


bool ApnUsbEraseFlash(unsigned short hDevice,  unsigned short	StartBlock,
					   unsigned short	BlockCount )
{
	bool Success;

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_DFERA,	// The request
								   false,				// Direction
								   StartBlock,			// wIndex
								   BlockCount,			// wValue
								   0,
								   NULL);				// Buffer for returned data
	*/

   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_DFERA,
                                BlockCount, StartBlock, (char *)NULL, 4, 10000);
	if (!Success) 
		printf( "WARNING: Failed ApnUsbEraseFlash().");
	
	return Success;
}


bool ApnUsbEraseFlashAll(unsigned short hDevice)
{
	bool Success;

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_DFERASE,	// The request
								   false,				// Direction
								   0,					// wIndex
								   0,					// wValue
								   0,
								   NULL);				// Buffer for returned data
	*/

   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_DFERASE,
                                0, 0, (char *)NULL, 0, 10000);
	if (!Success) 
		printf( "WARNING: Failed ApnUsbEraseFlashAll().");
	
	return Success;
}


bool ApnUsbReadFlash(unsigned short hDevice, unsigned long		StartAddr,
					  unsigned long		Count,
					  unsigned char		*pBuffer )
{
	bool			Success;
	unsigned short	wIndex;
	unsigned short	wValue;

	wIndex = (USHORT)(StartAddr >> 16);
	wValue = (USHORT)StartAddr;
	
	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_DFRW,	// The request
								   true,			// Direction
								   wIndex,			// wIndex
								   wValue,			// wValue
								   (USHORT)Count,
								   pBuffer);		// Buffer for returned data
	*/

   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_DFRW,
                                wValue, wIndex, (char *)pBuffer, Count, 10000);

	if (!Success)
		printf("WARNING:  Failed ApnUsbReadFlash()");

	return Success;
}


bool ApnUsbWriteFlash(unsigned short hDevice, unsigned long	StartAddr,
					   unsigned long	Count,
					   unsigned char	*pBuffer )
{
	bool			Success;
	unsigned short	wIndex;
	unsigned short	wValue;

	wIndex = (USHORT)(StartAddr >> 16);
	wValue = (USHORT)StartAddr;

	/*	
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_DFRW,	// The request
								   false,			// Direction
								   wIndex,			// wIndex
								   wValue,			// wValue
								   (USHORT)Count,
								   pBuffer);		// Buffer for returned data
	*/

   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_DFRW,
                                wValue, wIndex, (char *)pBuffer, Count, 10000);
	if (!Success)
		printf("WARNING:  Failed ApnUsbReadFlash()");

	return Success;
}


bool ApnUsbReadFlashBuffer(unsigned short hDevice, unsigned long	StartAddr,
							unsigned long	Count,
							unsigned char	*pBuffer )
{
	unsigned short	ChunkSize;
	unsigned long	Addr;
	unsigned short	StartBlock;
	unsigned char	*Ptr;
	unsigned short	ccnt;

	ccnt = 0;
	Addr = StartAddr;
	Ptr  = pBuffer;
	
	while (Count) 
	{
		if (Count < 4096) ChunkSize = Count;
		
		if ( !ApnUsbReadFlash( hDevice, Addr, ChunkSize, Ptr) ) 
		{
			printf( "ERROR:  ApnUsbReadFlashBuffer() Failure.  Error doing flash read." );
			return false;
		}

		Count	-= ChunkSize;
		Ptr		+= ChunkSize;
		Addr	+= ChunkSize;
	}

	return true;
}


bool ApnUsbWriteFlashBuffer(unsigned short hDevice, unsigned long	StartAddr,
							 unsigned long	Count,
							 unsigned char	*pBuffer )
{
	unsigned short	ChunkSize;
	unsigned long	Addr;
	unsigned short	StartBlock;
	unsigned char	*Ptr;

	Ptr		= pBuffer;
	Addr	= StartAddr;

	printf( "Ready to erase device" );

	if ( !ApnUsbEraseFlashAll(hDevice) ) 
	{
		printf( "ERROR:  Failed ApnUsbEraseFlashAll()." );
		return false;
	}
	else 
	{
		printf( "Ready to start buffer downlong" );

		while ( Count )
		{
			if (Count < 4096) ChunkSize = Count;
			
			if ( !ApnUsbWriteFlash(hDevice, Addr, ChunkSize, Ptr) )
			{
				printf( "ERROR:  Failed ApnUsbWriteFlash()." );
				return false;
			}

			Count	-= ChunkSize;
			Ptr		+= ChunkSize;
			Addr	+= ChunkSize;
		}
	}

	return true;
}


bool ApnUsbEnableProgramMode(unsigned short hDevice )
{
	bool			Success;
	unsigned char	val;

	printf("In ApnUsbEnableProgramMode" );

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_PROGMODE,
								   false,
								   0,
								   1,
								   0,
								   (PUCHAR)&val );
	*/

   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_PROGMODE,
                                1, 0, (char *)&val, 0, 10000);

	if ( !Success ) 
	{
		printf( "WARNING:  Failed ApnUsbEnableProgramMode()." );
		return false;
	}

	printf("Leaving ApnUsbEnableProgramMode" );

	return true;
}


bool ApnUsbDisableProgramMode(unsigned short hDevice )
{
	bool			Success;
	unsigned char	val;

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_APOGEE_PROGMODE,
								   false,
								   0,
								   0,
								   0,
								   (PUCHAR)&val );
	*/

   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_APOGEE_PROGMODE,
                                0, 0, (char *)&val, 0, 10000);

	if ( !Success ) 
	{
		printf( "WARNING:  Failed ApnUsbDisableProgramMode()." );
		return false;
	}

	return true;
}


bool ApnUsb8051Reset(unsigned short hDevice, unsigned char	Value )
{
	bool			Success;
	unsigned char	TempValue;
	
	TempValue = Value;

	/*
	Success = ApnUsbCreateRequest( hDevice,
								   VND_ANCHOR_LOAD_INTERNAL,
								   false,
								   0,
								   CPUCS_REG_FX2,
								   1,
								   &TempValue );
	*/

   	Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_ANCHOR_LOAD_INTERNAL,
                                CPUCS_REG_FX2, 0, (char *)&TempValue, 1, 10000);

	return Success;
}


bool ApnUsbDownloadIntelHex(unsigned short hDevice,PINTEL_HEX_RECORD pFirmware )
{
	bool				Success;
	PINTEL_HEX_RECORD	pRecord;
	
	pRecord = pFirmware;

	while ( pRecord->Type == 0 )
	{
		/*
		Success = ApnUsbCreateRequest( hDevice,
									   VND_ANCHOR_LOAD_INTERNAL,
									   false,
									   0,
									   pRecord->Address,
									   pRecord->Length,
									   pRecord->Data );
		*/
                printf("Downloading %x , %d\n",pRecord->Address,pRecord->Length);

   		Success = usb_control_msg((struct usb_dev_handle *)g_hSysDriver[hDevice], 
                                USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
                                VND_ANCHOR_LOAD_INTERNAL,
                                pRecord->Address, 0, (char *)pRecord->Data , pRecord->Length, 10000);

		if ( !Success )
			break;

		++pRecord;
	}

	return Success;
}


bool ApnUsbDownloadFirmware(unsigned short hDevice,PINTEL_HEX_RECORD pFirmware )
{
	if ( ApnUsb8051Reset( hDevice, 1) ) 
	{
		if ( ApnUsbDownloadIntelHex( hDevice, pFirmware ) )
			ApnUsb8051Reset( hDevice, 0 );
		else
			return false;
	} 
	else 
	{
		return false;
	}

	return true;
}


bool ApnUsbWriteCustomSerialNumber(unsigned short hDevice,char			*SerialNumber,
									unsigned short	*SerialNumberLength )
{
	bool				RetVal;
	unsigned char*		pBuffer;
	PUCHAR				pSendBuffer;
	ULONG				SendBufferLen;


	SendBufferLen	= sizeof( APN_USB_REQUEST ) + APN_USB_SN_BYTE_COUNT;
	pSendBuffer		= new UCHAR[SendBufferLen];
	
	pBuffer			= new unsigned char[APN_USB_SN_BYTE_COUNT];
	
	memset( pBuffer, '\0', APN_USB_SN_BYTE_COUNT );
	memcpy( pBuffer, SerialNumber, strlen(SerialNumber) );

	RetVal = ApnUsbWriteEepromBuffer( hDevice, 
									  APN_USB_SN_EEPROM_BANK,
									  APN_USB_SN_EEPROM_CHIP,
									  APN_USB_SN_EEPROM_ADDR,
									  APN_USB_SN_BYTE_COUNT,
									  pBuffer );

	delete [] pSendBuffer;
	delete [] pBuffer;

	if ( !RetVal )
	{
		*SerialNumberLength = 0;

		return false;
	}

	return true;
}

bool ApnRawReadCustomSerialNumber(unsigned short hDevice,unsigned char	*SerialNumber)
{
	bool			RetVal;	
	
	RetVal = ApnUsbReadEepromBuffer( hDevice, 
									  APN_USB_SN_EEPROM_BANK,
									  APN_USB_SN_EEPROM_CHIP,
									  APN_USB_SN_EEPROM_ADDR,
									  APN_USB_SN_BYTE_COUNT,
									  SerialNumber );

	if ( !RetVal )
	{

		return false;
	}

	return true;
}

