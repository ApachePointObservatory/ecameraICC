//////////////////////////////////////////////////////////////////////
//
// ApnCamera_USB.cpp: implementation of the CApnCamera_TEST class.
//
// Copyright (c) 2003-2006 Apogee Instruments, Inc.
//
//////////////////////////////////////////////////////////////////////

#include "stdafx.h"
#include "dbt.h"

#include "ApnCamera_TEST.h"

#include "ApogeeUsb.h"
#include "ApogeeUsbErr.h"

#include <initguid.h>
#include "..\Driver\Guid_usb.h"


//////////////////////////////////////////////////////////////////////
// Construction/Destruction
//////////////////////////////////////////////////////////////////////

CApnCamera_TEST::CApnCamera_TEST()
{
	m_CamIdA							= 0x0;
	m_CamIdB							= 0x0;
	m_Option							= 0x0;

	m_hSysDriver						= NULL;

	m_SysImgSizeBytes					= 0;

	m_pvtMsgWndCreated					= false;

	m_pvtConnectionOpen					= false;

	m_pvtExposeSequenceBulkDownload		= true;
	m_pvtExposeCI						= false;
	m_pvtExposeDualReadout				= false;

	// seed the random number generator
	srand( (unsigned)time( NULL ) );
}

CApnCamera_TEST::~CApnCamera_TEST()
{
	if ( m_pvtMsgWndCreated == true )
	{
		if ( DestroyWindow() != 0 )
		{
			// Message window was successfully destroyed
			m_pvtMsgWndCreated = false;
		}
	}

	CloseDriver();
}

bool CApnCamera_TEST::GetDeviceHandle( void *hCamera, char *CameraInfo )
{
	HANDLE *hDevice;

	hDevice = (HANDLE*)hCamera;

	*hDevice = m_hSysDriver;

	strcpy( CameraInfo, m_SysDeviceName );

	return true;
}

BEGIN_MESSAGE_MAP(CApnCamera_TEST, CWnd)
	ON_WM_CREATE()
	ON_WM_DEVICECHANGE()
END_MESSAGE_MAP()


/////////////////////////////////////////////////////////////////////////////
// CApnCamera_TEST message handlers

int CApnCamera_TEST::OnCreate(LPCREATESTRUCT lpCreateStruct) 
{
	if (CWnd::OnCreate(lpCreateStruct) == -1)
		return -1;
	
	// TODO: Add your specialized creation code here

    DEV_BROADCAST_DEVICEINTERFACE NotificationFilter;

    ZeroMemory( &NotificationFilter, sizeof(NotificationFilter) );

    NotificationFilter.dbcc_size		= sizeof(DEV_BROADCAST_DEVICEINTERFACE);
    NotificationFilter.dbcc_devicetype	= DBT_DEVTYP_DEVICEINTERFACE;
    NotificationFilter.dbcc_classguid	= GUID_USBWDM_DEVICE_INTERFACE_CLASS;

    RegisterDeviceNotification( m_hWnd, 
								&NotificationFilter,
								DEVICE_NOTIFY_WINDOW_HANDLE );

	return 0;
}

BOOL CApnCamera_TEST::OnDeviceChange(UINT nEventType, DWORD dwData)
{
	PDEV_BROADCAST_HDR pDB;
	
	pDB = (PDEV_BROADCAST_HDR)dwData;


	switch( nEventType )
	{
		case DBT_DEVICEARRIVAL:
			break;
		case DBT_DEVICEQUERYREMOVE:
			break;
		case DBT_DEVICEREMOVECOMPLETE:
			if ( pDB->dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE )
			{
				PDEV_BROADCAST_DEVICEINTERFACE pDBDI = (PDEV_BROADCAST_DEVICEINTERFACE)dwData;

				if ( pDBDI->dbcc_classguid == GUID_USBWDM_DEVICE_INTERFACE_CLASS )
				{
					if ( _tcscmp( _tcslwr(m_SysDeviceName), _tcslwr(pDBDI->dbcc_name) ) == 0 )
					{
						// the names match
						// ApnUsbClose( &m_hSysDriver );
					}
				}
			}
			break;
		case DBT_DEVNODES_CHANGED:
			break;
		default:
			break;
	}

	return CWnd::OnDeviceChange(nEventType, dwData);
}


bool CApnCamera_TEST::SimpleInitDriver( unsigned long	CamIdA, 
									   unsigned short	CamIdB, 
									   unsigned long	Option )
{
	m_CamIdA = CamIdA;
	m_CamIdB = CamIdB;
	m_Option = Option;


	m_pvtConnectionOpen	= true;

	m_pvtVendorId	= 0x0;
	m_pvtProductId	= 0x0099;
	m_pvtDeviceId	= 0x00AA;

	m_pvtMsgWndCreated	= false;

	AFX_MANAGE_STATE(AfxGetStaticModuleState( ));

	if ( CreateEx( WS_EX_TOPMOST, 
		 		   _T("STATIC"),
				   "AltaUsbMsgWnd",
				   0, 
				   0,
				   0,
				   1,
				   1,
				   NULL,
				   0 ) != 0 )
	{
		m_pvtMsgWndCreated = true;
	}

	return true;
}


bool CApnCamera_TEST::InitDriver( unsigned long	CamIdA, 
								 unsigned short CamIdB, 
								 unsigned long	Option )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::InitDriver() -> BEGIN" );

	
	m_CamIdA = CamIdA; 
	m_CamIdB = CamIdB;
	m_Option = Option;


	m_pvtConnectionOpen	= true;

	m_pvtVendorId		= 0x0;
	m_pvtProductId		= 0x0099;
	m_pvtDeviceId		= 0x00AA;

	m_SysImgSizeBytes	= 0;

	m_SysDriverVersion	= 9.9;

	m_pvtMsgWndCreated	= false;

	AFX_MANAGE_STATE(AfxGetStaticModuleState( ));

	if ( CreateEx( WS_EX_TOPMOST, 
		 		   _T("STATIC"),
				   "AltaUsbMsgWnd",
				   0, 
				   0,
				   0,
				   1,
				   1,
				   NULL,
				   0 ) != 0 )
	{
		m_pvtMsgWndCreated = true;
	}

	// Update the feature set structure
	if ( m_pvtDeviceId >= 16 )
	{
		m_pvtUseAdvancedStatus	= true;
	}
	else
	{
		m_pvtUseAdvancedStatus	= false;
	}

	m_pvtSequenceImagesDownloaded = 0;
	
	m_pvtMostRecentFrame	= 0;
	m_pvtReadyFrame			= 0;
	m_pvtCurrentFrame		= 0;

	// The loopback test was successful.  Proceed with initialization.
	if ( InitDefaults() != 0 )
		return false;

	// Done
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::InitDriver() -> END" );

	return true;
}


Apn_Interface CApnCamera_TEST::GetCameraInterface()
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::GetCameraInterface()" );

	
	return Apn_Interface_TEST;
}


long CApnCamera_TEST::GetCameraSerialNumber( char *CameraSerialNumber, long *BufferLength )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::GetCameraSerialNumber()" );


	char			pBuffer[256];
	unsigned short	Length;


	if ( *BufferLength < (APN_USB_SN_BYTE_COUNT + 1) )
	{
		if ( *BufferLength > 7 )
		{
			strcpy( CameraSerialNumber, "Unknown" );
			*BufferLength = strlen( CameraSerialNumber );
		}

		return CAPNCAMERA_ERR_SN;
	}

	strcpy( CameraSerialNumber, "TestObject" );
	*BufferLength = strlen( CameraSerialNumber );

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::GetSystemDriverVersion( char *SystemDriverVersion, long *BufferLength )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::GetSystemDriverVersion()" );


	if ( m_SysDriverVersion == 0.0 )
		sprintf( SystemDriverVersion, "Unknown" );
	else
		sprintf( SystemDriverVersion, "%.2f", m_SysDriverVersion );

	*BufferLength = strlen( SystemDriverVersion );

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::GetUsb8051FirmwareRev( char *FirmwareRev, long *BufferLength )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::GetUsb8051FirmwareRev()" );


	strcpy( FirmwareRev, "TestFw" );
	*BufferLength = strlen( FirmwareRev );

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::GetUsbProductId( unsigned short *pProductId )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::GetUsbProductId()" );


	*pProductId = m_pvtProductId;

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::GetUsbDeviceId( unsigned short *pDeviceId )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::GetUsbDeviceId()" );


	*pDeviceId = m_pvtDeviceId;

	return CAPNCAMERA_SUCCESS;
}


bool CApnCamera_TEST::CloseDriver()
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::CloseDriver()" );


	ApnUsbClose( &m_hSysDriver );

	return true;
}


long CApnCamera_TEST::GetImageData( unsigned short *pImageBuffer, 
								   unsigned short &Width,
								   unsigned short &Height,
								   unsigned long  &Count )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::GetImageData()" );


	unsigned short	Offset;
	unsigned short	*pTempBuffer;
	unsigned long	DownloadHeight;
	unsigned long	i, j;
	char			szOutputText[128];
	

	if ( m_pvtConnectionOpen == false )
		return CAPNCAMERA_ERR_CONNECT;

	if ( !ImageInProgress() )
		return CAPNCAMERA_ERR_IMAGE;

	// Make sure it is okay to get the image data
	// The app *should* have done this on its own, but we have to make sure
	if ( (m_pvtNumImages == 1) || (m_pvtExposeSequenceBulkDownload) )
	{
		while ( !ImageReady() )
		{
			Sleep( 50 );
			read_ImagingStatus();
		}
	}

	Width	= m_pvtExposeWidth;
	Height	= m_pvtExposeHeight;

	if ( m_pvtExposeCameraMode != Apn_CameraMode_Test )
	{
		if ( m_pvtExposeBitsPerPixel == 16 )
			Offset = 1;

		if ( m_pvtExposeBitsPerPixel == 12 )
			Offset = 10;

		Width -= Offset;	// Calculate the true image width
	}

	if ( m_pvtExposeSequenceBulkDownload )
		DownloadHeight = Height * m_pvtNumImages;
	else
		DownloadHeight = Height;

	pTempBuffer = new unsigned short[(Width+Offset) * DownloadHeight];
	
	TestGetImage( m_SysImgSizeBytes, pTempBuffer );

	unsigned long TermOne;
	unsigned long TermTwo;

	for ( i=0; i<DownloadHeight; i++ )
	{
		TermOne = i*Width;
		TermTwo = (i*(Width+Offset))+Offset;

		for ( j=0; j<Width; j++ )
		{
			// Below is the non-optimized formula for the data re-arrangement
			// pImageBuffer[(i*Width)+j] = pTempBuffer[(i*(Width+Offset))+j+Offset];
			pImageBuffer[TermOne+j] = pTempBuffer[TermTwo+j];
		}
	}

	if ( m_pvtExposeDualReadout == true )
	{
		// rearrange
	}

	delete [] pTempBuffer;

	if ( m_pvtExposeSequenceBulkDownload == true )
	{
		Count = read_ImageCount();
	}
	else
	{
		Count = 1;
	}

	if ( m_pvtExposeCameraMode == Apn_CameraMode_TDI )
	{
		m_pvtTdiLinesDownloaded++;

		AltaDebugPrint( szOutputText, "APOGEE.DLL - CApnCamera_TEST::GetImage() -> TdiLinesDownloaded = %d", m_pvtTdiLinesDownloaded );
		AltaDebugOutputString( szOutputText );

		if ( m_pvtTdiLinesDownloaded == read_TDIRows() )
		{
			SignalImagingDone();

			ResetSystem();
		}
	}
	else
	{
		if ( (m_pvtNumImages == 1) || (m_pvtExposeSequenceBulkDownload) )
		{
			AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::GetImage() -> Single Image Done" );

			SignalImagingDone();
		}

		if ( (m_pvtNumImages > 1) && (!m_pvtExposeSequenceBulkDownload) )
		{
			m_pvtSequenceImagesDownloaded++;

			AltaDebugPrint( szOutputText, "APOGEE.DLL - CApnCamera_TEST::GetImage() -> SequenceImagesDownloaded = %d", m_pvtSequenceImagesDownloaded );
			AltaDebugOutputString( szOutputText );

			if ( m_pvtSequenceImagesDownloaded == m_pvtNumImages )
				SignalImagingDone();
		}
	}

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::GetLineData( unsigned short *pLineBuffer,
								  unsigned short &Size )
{
	unsigned short	Offset;
	unsigned short	*pTempBuffer;
	unsigned short	Width;
	unsigned long	BytesPerLine;
	unsigned long	i;


	if ( m_pvtConnectionOpen == false )
		return CAPNCAMERA_ERR_CONNECT;

	// image must already be in progress
	if ( !ImageInProgress() )
		return CAPNCAMERA_ERR_IMAGE;

	// the SequenceBulkDownload var *must* be set to FALSE
	if ( m_pvtExposeSequenceBulkDownload )	
		return CAPNCAMERA_ERR_IMAGE;

	Width			= m_pvtExposeWidth;
	BytesPerLine	= Width * 2;

	if ( m_pvtExposeBitsPerPixel == 16 )
		Offset = 1;

	if ( m_pvtExposeBitsPerPixel == 12 )
		Offset = 10;

	Width -= Offset;	// Calculate the true image width

	pTempBuffer = new unsigned short[Width+Offset];
	
	if ( ApnUsbGetImage( &m_hSysDriver, BytesPerLine, pTempBuffer ) != APN_USB_SUCCESS )
	{
		ApnUsbClose( &m_hSysDriver );

		delete [] pTempBuffer;

		SignalImagingDone();

		m_pvtConnectionOpen = false;

		return CAPNCAMERA_ERR_IMAGE;
	}

	for ( i=0; i<Width; i++ )
	{
		pLineBuffer[i] = pTempBuffer[i+Offset];
	}

	delete [] pTempBuffer;

	if ( m_pvtTdiLinesDownloaded == read_TDIRows() )
		SignalImagingDone();
	
	Size = Width;

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::PreStartExpose( unsigned short BitsPerPixel )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::PreStartExpose() -> BEGIN" );


	if ( m_pvtConnectionOpen == false )
	{
		return CAPNCAMERA_ERR_CONNECT;
	}

	if ( (BitsPerPixel != 16) && (BitsPerPixel != 12) )
	{
		// Invalid bit depth request
		return CAPNCAMERA_ERR_START_EXP;
	}


	m_pvtExposeWidth				= GetExposurePixelsH();
	m_pvtExposeBitsPerPixel			= BitsPerPixel;
	m_pvtExposeHBinning				= read_RoiBinningH();
	m_pvtExposeSequenceBulkDownload	= read_SequenceBulkDownload();
	m_pvtExposeExternalShutter		= read_ExternalShutter();
	m_pvtExposeCameraMode			= read_CameraMode();
	m_pvtExposeCI					= read_ContinuousImaging();
	m_pvtExposeDualReadout			= read_DualReadout();

	if ( m_pvtExposeCameraMode != Apn_CameraMode_Test )
	{
		if ( m_pvtExposeBitsPerPixel == 16 )
			m_pvtExposeWidth += 1;

		if ( m_pvtExposeBitsPerPixel == 12 )
			m_pvtExposeWidth += 10;
	}

	if ( m_pvtExposeCameraMode == Apn_CameraMode_TDI )
	{
		m_pvtTdiLinesDownloaded = 0;
		m_pvtExposeHeight		= 1;
		m_pvtNumImages			= read_TDIRows();
	}
	else
	{
		m_pvtExposeHeight		= GetExposurePixelsV();
		m_pvtNumImages			= read_ImageCount();
	}

	if ( (m_pvtExposeCI) && (m_pvtExposeCameraMode == Apn_CameraMode_Normal) )
	{
		m_SysImgSizeBytes = m_pvtExposeWidth * m_pvtExposeHeight * 2;
	}
	else
	{
		if ( m_pvtExposeSequenceBulkDownload == true )
		{
			m_SysImgSizeBytes = m_pvtExposeWidth * m_pvtExposeHeight * m_pvtNumImages * 2;
		}
		else
		{
			// first check DID and .sys driver version

			// reset our vars that will be updated during future status calls
			m_pvtMostRecentFrame	= 0;
			m_pvtReadyFrame			= 0;
			m_pvtCurrentFrame		= 0;

			m_pvtSequenceImagesDownloaded = 0;

			m_SysImgSizeBytes = m_pvtExposeWidth * m_pvtExposeHeight * 2;
		}
	}

	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::PreStartExpose() -> END" );

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::PostStopExposure( bool DigitizeData )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::PostStopExposure() -> BEGIN" );


	PUSHORT			pRequestData;


	if ( m_pvtConnectionOpen == false )
		return CAPNCAMERA_ERR_CONNECT;


	switch( m_pvtExposeCameraMode )
	{
		case Apn_CameraMode_Normal:
			// If in continuous imaging mode, issue the stop
			if ( m_pvtExposeCI )
			{
				// ApnUsbStopCI( &m_hSysDriver, 1 );
			}

			// First, if we are not triggered in some manner, do a normal stop exposure routine
			// We check the condition "read_ImagingStatus() == Apn_Status_WaitingOnTrigger"
			// after this because we don't usually want to read ImagingStatus in the driver
			if ( !read_ExposureTriggerGroup() && !read_ExposureTriggerEach() && !read_ExposureExternalShutter() )
			{
				AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::PostStopExposure() -> Not using H/W trigger" );

				if ( !DigitizeData )
				{
					while ( !ImageReady() )
					{
						Sleep( 50 );
						read_ImagingStatus();
					}

					pRequestData = new USHORT[m_pvtExposeWidth*m_pvtExposeHeight];

					TestGetImage( m_SysImgSizeBytes, pRequestData );

					delete [] pRequestData;

					SignalImagingDone();
				}
			}
			else
			{
				AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::PostStopExposure() -> Using H/W trigger" );

				if ( read_ImagingStatus() == Apn_Status_WaitingOnTrigger )
				{
					AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::PostStopExposure() -> Detected Apn_Status_WaitingOnTrigger" );

					// ApnUsbStopExp( &m_hSysDriver, false );
					SignalImagingDone();
					ResetSystem();
				}
				else
				{
					AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::PostStopExposure() -> Did NOT detect Apn_Status_WaitingOnTrigger" );

					if ( !DigitizeData )
					{
						while ( !ImageReady() )
						{
							Sleep( 50 );
							read_ImagingStatus();
						}

						pRequestData = new USHORT[m_pvtExposeWidth*m_pvtExposeHeight];

						TestGetImage( m_SysImgSizeBytes, pRequestData );

						delete [] pRequestData;

						SignalImagingDone();
						
						if ( m_pvtExposeExternalShutter )
						{
							ResetSystem();
						}
					}
				}
			}
			break;
		case Apn_CameraMode_TDI:
			// Issue the Stop command
			// ApnUsbStopExp( &m_hSysDriver, DigitizeData );
			// Clean up after the stop

			// Restart the system to flush normally
			SignalImagingDone();
			ResetSystem();
			break;
		case Apn_CameraMode_ExternalTrigger:
			// Included for stopping "legacy" externally triggered exposures
			if ( !DigitizeData )
			{
				while ( !ImageReady() )
				{
					Sleep( 50 );
					read_ImagingStatus();
				}

				pRequestData = new USHORT[m_pvtExposeWidth*m_pvtExposeHeight];

				TestGetImage( m_SysImgSizeBytes, pRequestData );

				delete [] pRequestData;

				SignalImagingDone();
			}
			break;
		case Apn_CameraMode_Kinetics:
			// Issue the Stop command
			// ApnUsbStopExp( &m_hSysDriver, DigitizeData );
			// Clean up after the stop

			// Restart the system to flush normally
			SignalImagingDone();
			ResetSystem();
			break;
		default:
			break;
	}

	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::PostStopExposure() -> END" );

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::Read( unsigned short reg, unsigned short& val )
{
	if ( m_pvtConnectionOpen == false )
		return CAPNCAMERA_ERR_CONNECT;

	switch ( reg )
	{
	case FPGA_REG_CAMERA_ID:
		val = m_CamIdA;
		break;
	case FPGA_REG_FIRMWARE_REV:
		val = 50;
		break;
	default:
		break;
	}


	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::Write( unsigned short reg, unsigned short val )
{
	if ( m_pvtConnectionOpen == false )
		return CAPNCAMERA_ERR_CONNECT;

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::WriteMultiSRMD( unsigned short reg, unsigned short val[], unsigned short count )
{
	if ( m_pvtConnectionOpen == false )
		return CAPNCAMERA_ERR_CONNECT;

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::WriteMultiMRMD( unsigned short reg[], unsigned short val[], unsigned short count )
{
	if ( m_pvtConnectionOpen == false )
		return CAPNCAMERA_ERR_CONNECT;

	return CAPNCAMERA_SUCCESS;
}


long CApnCamera_TEST::QueryStatusRegs( unsigned short&	StatusReg,
									  unsigned short&	HeatsinkTempReg,
									  unsigned short&	CcdTempReg,
									  unsigned short&	CoolerDriveReg,
									  unsigned short&	VoltageReg,
									  unsigned short&	TdiCounter,
									  unsigned short&	SequenceCounter,
									  unsigned short&	MostRecentFrame,
									  unsigned short&	ReadyFrame,
									  unsigned short&	CurrentFrame )
{
	AltaDebugOutputString( "APOGEE.DLL - CApnCamera_TEST::QueryStatusRegs()" );


	bool DoneFlag;


	StatusReg		= 0x0;
	HeatsinkTempReg	= 0xAAAA + (rand() * 0.2 / RAND_MAX);
	CcdTempReg		= 0xCCCC + (rand() * 0.2 / RAND_MAX);
	CoolerDriveReg	= 0x0BBB + (rand() * 0.4 / RAND_MAX);;
	VoltageReg		= 9000 + (rand() * 0.5 / RAND_MAX);
	TdiCounter		= 0x0;
	SequenceCounter	= 0x0;
	MostRecentFrame	= 0x0;
	ReadyFrame		= 0x0;
	CurrentFrame	= 0x0;

	StatusReg |= FPGA_BIT_STATUS_IMAGE_DONE;

	if ( m_pvtConnectionOpen == false )
		return CAPNCAMERA_ERR_CONNECT;

	m_pvtMostRecentFrame	= MostRecentFrame;
	m_pvtReadyFrame			= ReadyFrame;
	m_pvtCurrentFrame		= CurrentFrame;

	return CAPNCAMERA_SUCCESS;
}


void CApnCamera_TEST::TestGetImage( unsigned long m_SysImgSizeBytes, unsigned short *pTempBuffer )
{
	unsigned long PixelCount;

	PixelCount = m_SysImgSizeBytes / 2;

	for ( unsigned long i=0; i<PixelCount; i++ )
	{
		pTempBuffer[i] = 2000 + ( (rand() * 500) / RAND_MAX );
	}

}
