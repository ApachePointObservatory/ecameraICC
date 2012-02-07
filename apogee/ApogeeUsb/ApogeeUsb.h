#if !defined(_APOGEEUSB_H__INCLUDED_)
#define _APOGEEUSB_H__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000


#ifndef APN_USB_TYPE
#define APN_USB_TYPE unsigned short
#endif

#define APN_USB_MAXCAMERAS					255

// The following lists the driver versions for feature support
// within the .sys driver
#define APN_USB_DRIVER_VER_SEQUENCE_SUPPORT	2.0

// The following lists the PID of the USB interface board
// for supporting various features
#define APN_USB_PID_SEQUENCE_SUPPORT		


#define APN_USB_SERIAL_SETTINGS_BYTE_COUNT	5

#define APN_USB_SERIAL_SETTINGS_CTRL_INDEX	4

#define APN_USB_SERIAL_BIT_FLOW_CONTROL		0x01
#define APN_USB_SERIAL_BIT_PARITY_ENABLE	0x10
#define APN_USB_SERIAL_BIT_PARITY_ODD		0x20

// The following is for the custom USB serial number feature
#define APN_USB_SN_BYTE_COUNT			64

// Byte count for getting the revision of the 8051 firmware
#define APN_USB_8051_REV_BYTE_COUNT		3




#ifndef IN
#define IN
#endif

#ifndef OUT
#define OUT
#endif

#define DWORD long
#define UCHAR unsigned char

typedef struct usb_dev_handle HANDLE;

typedef struct _APN_USB_CAMINFO {
	bool			bCamera;
	unsigned short	CamNumber;
	unsigned short	CamModel;
	unsigned short	CamFirmware;
} APN_USB_CAMINFO;

#define ApnUsbParity_None 0
#define ApnUsbParity_Odd 1
#define ApnUsbParity_Even 2



APN_USB_TYPE ApnUsbOpen( unsigned short DevNumber, char *SysDeviceName );

APN_USB_TYPE ApnUsbOpenFilterWheel( unsigned short DevNumber, char *SysDeviceName );

APN_USB_TYPE ApnUsbClose( unsigned short hDevice );


APN_USB_TYPE ApnUsbDiscovery( unsigned short *UsbCamCount, 
							  APN_USB_CAMINFO UsbCamInfo[] );


APN_USB_TYPE ApnUsbReadReg( unsigned short hDevice ,
						    unsigned short FpgaReg, 
						    unsigned short *FpgaData );


APN_USB_TYPE ApnUsbWriteReg( unsigned short hDevice ,
							 unsigned short FpgaReg, 
							 unsigned short FpgaData );


APN_USB_TYPE ApnUsbWriteRegMulti( unsigned short hDevice ,
								  unsigned short FpgaReg,
								  unsigned short FpgaData[],
								  unsigned short RegCount );


APN_USB_TYPE ApnUsbWriteRegMultiMRMD( unsigned short hDevice ,
									  unsigned short FpgaReg[],
									  unsigned short FpgaData[],
									  unsigned short RegCount );


APN_USB_TYPE ApnUsbReadStatusRegs( unsigned short hDevice ,
								   bool				UseAdvStatus,
                                                                   bool                         *DoneFlag,
								   unsigned short	*StatusReg,
			 					   unsigned short	*HeatsinkTempReg,
								   unsigned short	*CcdTempReg,
								   unsigned short	*CoolerDriveReg,
								   unsigned short	*VoltageReg,
								   unsigned short	*TdiCounter,
								   unsigned short	*SequenceCounter,
								   unsigned short	*MostRecentFrame,
								   unsigned short	*ReadyFrame,
								   unsigned short	*CurrentFrame );


APN_USB_TYPE ApnUsbStartExp(unsigned short hDevice ,
							 unsigned short ImageCount,
							 unsigned short ImageWidth,
							 unsigned short ImageHeight );


APN_USB_TYPE ApnUsbStartCI(	unsigned short hDevice ,
							unsigned short	ImageWidth,
							unsigned short	ImageHeight );


APN_USB_TYPE ApnUsbStopExp(unsigned short hDevice ,
						    bool DigitizeData );


APN_USB_TYPE ApnUsbStopCI(	unsigned short hDevice ,
							unsigned short	PostStopCount );


APN_USB_TYPE ApnUsbGetImage( unsigned short hDevice ,
							 unsigned long ImgSizeBytes,
							 unsigned short *pMem ,unsigned long *transferbytes);


APN_USB_TYPE ApnUsbReset( unsigned short hDevice );


APN_USB_TYPE ApnUsbSerialReadSettings( unsigned short hDevice ,
									   unsigned short SerialId,
									   unsigned char  *Settings );


APN_USB_TYPE ApnUsbSerialWriteSettings( unsigned short hDevice ,
										unsigned short SerialId,
										unsigned char  *Settings );


APN_USB_TYPE ApnUsbSerialReadBaudRate( unsigned short hDevice ,
									   unsigned short SerialId,
									   unsigned long  *BaudRate );


APN_USB_TYPE ApnUsbSerialWriteBaudRate( unsigned short hDevice ,
									    unsigned short SerialId,
										unsigned long  BaudRate );


APN_USB_TYPE ApnUsbSerialReadFlowControl( unsigned short hDevice ,
										  unsigned short SerialId,
								 		  bool			 *FlowControl );


APN_USB_TYPE ApnUsbSerialWriteFlowControl( unsigned short hDevice ,
										   unsigned short SerialId,
								 		   bool			  FlowControl );


APN_USB_TYPE ApnUsbSerialReadParity( unsigned short hDevice ,
									 unsigned short	SerialId,
									 int	*Parity );


APN_USB_TYPE ApnUsbSerialWriteParity( unsigned short hDevice ,
									  unsigned short SerialId,
									  int   Parity );


APN_USB_TYPE ApnUsbSerialRead( unsigned short hDevice ,
							   unsigned short	SerialId,
							   char				*ReadBuffer,
							   unsigned short	*BufferCount );


APN_USB_TYPE ApnUsbSerialWrite( unsigned short hDevice ,
								unsigned short	SerialId,
							    char			*WriteBuffer,
								unsigned short	BufferCount );


APN_USB_TYPE ApnUsbReadVendorInfo( unsigned short hDevice ,
								   unsigned short *VendorId,
			 					   unsigned short *ProductId,
								   unsigned short *DeviceId );


APN_USB_TYPE ApnUsbSysDriverVersion( unsigned short hDevice ,
									 double *VersionNumber );


APN_USB_TYPE ApnUsbReadCustomSerialNumber( unsigned short hDevice ,
										   char				*SerialNumber,
										   unsigned short	*SerialNumberLength );
 
bool ApnRawReadCustomSerialNumber( unsigned short hDevice ,
										   unsigned  char				*SerialNumber);
 
APN_USB_TYPE ApnUsbRead8051FirmwareRevision( unsigned short hDevice ,char	*Revision );

APN_USB_TYPE ApnUsbRead8051FilterFirmwareRevision( unsigned short hDevice ,char	*Revision );

APN_USB_TYPE ApnUsbConfigureDataPort( unsigned short hDevice ,unsigned short	Assignment );


APN_USB_TYPE ApnUsbReadDataPort(unsigned short hDevice , unsigned short *DataValue );


APN_USB_TYPE ApnUsbWriteDataPort( unsigned short hDevice ,unsigned short	DataValue );


APN_USB_TYPE ApnUsbConfigureControlPort( unsigned short hDevice ,unsigned short	Assignment );


APN_USB_TYPE ApnUsbReadControlPort( unsigned short hDevice ,unsigned char	*ControlValue,
				    unsigned char	*OptionPinValue );



APN_USB_TYPE ApnUsbWriteControlPort( unsigned short hDevice ,unsigned char	ControlValue,
				     unsigned char	OptionPinValue );



#endif  // !defined(_APOGEEUSB_H__INCLUDED_)
