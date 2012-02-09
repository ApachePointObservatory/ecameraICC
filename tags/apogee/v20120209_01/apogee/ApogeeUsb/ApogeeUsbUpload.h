// ApogeeUsbUpload.h    
//
// Copyright (c) 2003 Apogee Instruments, Inc.
//
// Functions for allowing updates to the USB device.  Some code
// based off of Cypress development kit.  All accesses to the 
// hardware go through the common ApnUsbCreateRequest() function.
//

#if !defined(_APOGEEUSBUPLOAD_H__INCLUDED_)
#define _APOGEEUSBUPLOAD_H__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
#include "ApogeeUsb.h"


#define BUFCON_BASE_ADDRESS				0xD000

#define CPUCS_REG_FX2					0xE600

#define	ROM_SIZE					32768
#define	ROM_CHUNK_SIZE					4096
#define ROM_BANK_SIZE				3*2		// ALTA
// #define ROM_BANK_SIZE					2*2		// ASCENT

#define APN_USB_SN_EEPROM_ADDR			0x0400
#define APN_USB_SN_EEPROM_BANK			0
#define	APN_USB_SN_EEPROM_CHIP			5


/*
bool ApnUsbCreateRequest(		unsigned short		hDevice,
								unsigned char		Request,
								bool				InputRequest,
								unsigned short		Index,
								unsigned short		Value,
								unsigned long		Length,
								unsigned char		*pBuffer );
*/

bool ApnUsbReadBufcon(unsigned short		hDevice,unsigned short		RegNum, 
								unsigned char		*RegData );


bool ApnUsbWriteBufcon(unsigned short		hDevice,unsigned short		RegNum,
								unsigned char		RegData );


bool ApnUsbReadEeprom(unsigned short		hDevice,unsigned char		Bank,
								unsigned char		Chip,
								unsigned short		Address,
								unsigned long		Count,
								unsigned char		*pBuffer );


bool ApnUsbWriteEeprom(unsigned short		hDevice,unsigned char		Bank,
								unsigned char		Chip,
								unsigned short		Address,
								unsigned long		Count,
								unsigned char		*pBuffer );


bool ApnUsbReadEepromBuffer(unsigned short		hDevice,unsigned char		StartingBank,
								unsigned char		StartingChip,
								unsigned short		StartingAddress,
								unsigned long		Count,
								unsigned char		*pBuffer );


bool ApnUsbWriteEepromBuffer(unsigned short		hDevice,unsigned char		StartingBank,
								unsigned char		StartingChip,
								unsigned short		StartingAddress,
								unsigned long		Count,
								unsigned char		*pBuffer );


bool ApnUsbIdFlash(unsigned short		hDevice,unsigned long		*pIdCode );


bool ApnUsbEraseFlash(unsigned short		hDevice,unsigned short		StartBlock,
								unsigned short		BlockCount );


bool ApnUsbEraseFlashAll(unsigned short		hDevice);


bool ApnUsbReadFlash(unsigned short		hDevice,unsigned long		StartAddr,
								unsigned long		Count,
								unsigned char		*pBuffer );


bool ApnUsbWriteFlash(unsigned short		hDevice,unsigned long		StartAddr,
								unsigned long		Count,
								unsigned char		*pBuffer );


bool ApnUsbReadFlashBuffer(unsigned short		hDevice,unsigned long		StartAddr,
								unsigned long		Count,
								unsigned char		*pBuffer );


bool ApnUsbWriteFlashBuffer(unsigned short		hDevice,unsigned long		StartAddr,
								unsigned long		Count,
								unsigned char		*pBuffer );


bool ApnUsbEnableProgramMode(unsigned short		hDevice);


bool ApnUsbDisableProgramMode(unsigned short		hDevice);


bool ApnUsb8051Reset(unsigned short		hDevice,unsigned char		Value );


bool ApnUsbDownloadIntelHex(unsigned short		hDevice, PINTEL_HEX_RECORD	pFirmware );


bool ApnUsbDownloadFirmware(unsigned short		hDevice, PINTEL_HEX_RECORD	pFirmware );


bool ApnUsbWriteCustomSerialNumber( unsigned short		hDevice,char *SerialNumber, unsigned short	*SerialNumberLength );


#endif  // !defined(_APOGEEUSBUPLOAD_H__INCLUDED_)
