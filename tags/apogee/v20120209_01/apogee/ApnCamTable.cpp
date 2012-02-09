//////////////////////////////////////////////////////////////////////
//
// ApnCamTable.cpp
//
// Copyright (c) 2003-2005 Apogee Instruments, Inc.
//
//////////////////////////////////////////////////////////////////////

#include <string.h>
#include <stdio.h>

#include "ApnCamTable.h"


#define ALTA_MODEL_PREFIX "Alta-"
#define ASCENT_MODEL_PREFIX "Ascent-"


void ApnCamModelLookup( unsigned short CamId, int FwRev, unsigned short Interface, char *szCamModel )
{
	char			szModelNumber[20];
	bool			Error;
	bool			IsAltaCamera;
	bool			IsAscentCamera;
	unsigned short	ModelIdentifier;



	IsAltaCamera	= ApnCamModelIsAlta( CamId, FwRev );
	IsAscentCamera	= ApnCamModelIsAscent( CamId, FwRev );

	if ( (IsAltaCamera && IsAscentCamera) || (!IsAltaCamera && !IsAscentCamera) )
	{
		strcpy( szCamModel, "Unknown" );
		return;
	}
	else
	{
		if ( IsAltaCamera )
		{
			strcpy( szCamModel, ALTA_MODEL_PREFIX );
			ModelIdentifier = CamId & APN_MASK_CAMERA_ID_ALTA;
		}
		else if ( IsAscentCamera )
		{
			strcpy( szCamModel, ASCENT_MODEL_PREFIX );
			ModelIdentifier = CamId & APN_MASK_CAMERA_ID_ASCENT;
		}
	}

	Error = false;

	switch( ModelIdentifier )
	{
	case APN_ALTA_KAF0401E_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF0401E_CAM_SZ );
		break;
	case APN_ALTA_KAF1602E_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF1602E_CAM_SZ );
		break;
	case APN_ALTA_KAF0261E_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF0261E_CAM_SZ );
		break;
	case APN_ALTA_KAF1301E_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF1301E_CAM_SZ );
		break;
	case APN_ALTA_KAF1001E_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF1001E_CAM_SZ );
		break;
	case APN_ALTA_KAF1001ENS_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF1001ENS_CAM_SZ );
		break;
	case APN_ALTA_KAF10011105_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF10011105_CAM_SZ );
		break;
	case APN_ALTA_KAF3200E_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF3200E_CAM_SZ );
		break;
	case APN_ALTA_KAF6303E_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF6303E_CAM_SZ );
		break;
	case APN_ALTA_KAF16801E_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF16801E_CAM_SZ );
		break;
	case APN_ALTA_KAF09000_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF09000_CAM_SZ );
		break;
	case APN_ALTA_KAF09000X_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF09000X_CAM_SZ );
		break;
	case APN_ALTA_KAF0401EB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF0401EB_CAM_SZ );
		break;
	case APN_ALTA_KAF1602EB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF1602EB_CAM_SZ );
		break;
	case APN_ALTA_KAF0261EB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF0261EB_CAM_SZ );
		break;
	case APN_ALTA_KAF1301EB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF1301EB_CAM_SZ );
		break;
	case APN_ALTA_KAF1001EB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF1001EB_CAM_SZ );
		break;
	case APN_ALTA_KAF6303EB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF6303EB_CAM_SZ );
		break;
	case APN_ALTA_KAF3200EB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF3200EB_CAM_SZ );
		break;
	case APN_ALTA_KAF16803_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF16803_CAM_SZ	);
		break;

	case APN_ALTA_TH7899_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_TH7899_CAM_SZ );
		break;
	case APN_ALTA_S101401107_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_S101401107_CAM_SZ );
		break;
	case APN_ALTA_S101401109_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_S101401109_CAM_SZ );
		break;
	case APN_ALTA_F3041_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_F3041_CAM_SZ );
		break;

	case APN_ALTA_KAF0401ENSD_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF0401ENSD_CAM_SZ );
		break;
	case APN_ALTA_KAF8300C_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF8300C_CAM_SZ );
		break;

	case APN_ALTA_CCD4710DD_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4710DD_CAM_SZ );
		break;
	case APN_ALTA_KAF8300_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF8300_CAM_SZ );
		break;

	case APN_ALTA_CCD4710_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4710_CAM_SZ );
		break;
	case APN_ALTA_CCD4710ALT_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4710ALT_CAM_SZ );
		break;
	case APN_ALTA_CCD4240_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4240_CAM_SZ );
		break;
	case APN_ALTA_CCD5710_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD5710_CAM_SZ );
		break;
	case APN_ALTA_CCD3011_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD3011_CAM_SZ );
		break;
	case APN_ALTA_CCD5520_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD5520_CAM_SZ );
		break;
	case APN_ALTA_CCD4720_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4720_CAM_SZ );
		break;
	case APN_ALTA_CCD7700_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD7700_CAM_SZ );
		break;

	case APN_ALTA_CCD4710B_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4710B_CAM_SZ );
		break;
	case APN_ALTA_CCD4240B_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4240B_CAM_SZ );
		break;
	case APN_ALTA_CCD5710B_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD5710B_CAM_SZ );
		break;
	case APN_ALTA_CCD3011B_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD3011B_CAM_SZ );
		break;
	case APN_ALTA_CCD5520B_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD5520B_CAM_SZ );
		break;
	case APN_ALTA_CCD4720B_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4720B_CAM_SZ );
		break;
	case APN_ALTA_CCD7700B_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD7700B_CAM_SZ );
		break;

	case APN_ALTA_KAI2001ML_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI2001ML_CAM_SZ );
		break;
	case APN_ALTA_KAI2020ML_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI2020ML_CAM_SZ );
		break;
	case APN_ALTA_KAI4020ML_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI4020ML_CAM_SZ );
		break;
	case APN_ALTA_KAI16000ML_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI16000ML_CAM_SZ );
		break;
	case APN_ALTA_KAI2001CL_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI2001CL_CAM_SZ );
		break;
	case APN_ALTA_KAI2020CL_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI2020CL_CAM_SZ );
		break;
	case APN_ALTA_KAI4020CL_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI4020CL_CAM_SZ );
		break;
	case APN_ALTA_KAI16000CL_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI16000CL_CAM_SZ );
		break;

	case APN_ALTA_KAI2020MLB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI2020MLB_CAM_SZ );
		break;
	case APN_ALTA_KAI4020MLB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI4020MLB_CAM_SZ );
		break;
	case APN_ALTA_KAI2020CLB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI2020CLB_CAM_SZ );
		break;
	case APN_ALTA_KAI4020CLB_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI4020CLB_CAM_SZ );
		break;

	case APN_ALTA_KAF09000D9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF09000D9_CAM_SZ );
		break;
	case APN_ALTA_KAF16801ED9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF16801ED9_CAM_SZ );
		break;
	case APN_ALTA_KAF16803D9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF16803D9_CAM_SZ );
		break;
	case APN_ALTA_F3041D9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_F3041D9_CAM_SZ );
		break;
	case APN_ALTA_KAI16000CLD9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI16000CLD9_CAM_SZ );
		break;
	case APN_ALTA_KAI16000MLD9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAI16000MLD9_CAM_SZ );
		break;
	case APN_ALTA_CCD4240D9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4240D9_CAM_SZ );
		break;
	case APN_ALTA_KAF1001EBD9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_KAF1001EBD9_CAM_SZ );
		break;
	case APN_ALTA_CCD4710D9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD4710D9_CAM_SZ );
		break;
	case APN_ALTA_CCD7700D9_CAM_ID:
		strcpy( szModelNumber, APN_ALTA_CCD7700D9_CAM_SZ );
		break;
    case APN_ALTA_KAF09000D7D9_CAM_ID:
        strcpy( szModelNumber, APN_ALTA_KAF09000D7D9_CAM_SZ );
		break;
    case APN_ALTA_KAF16801ED7D9_CAM_ID:
        strcpy( szModelNumber, APN_ALTA_KAF16801ED7D9_CAM_SZ );
		break;
    case APN_ALTA_KAF16803D7D9_CAM_ID:
        strcpy( szModelNumber, APN_ALTA_KAF16803D7D9_CAM_SZ );
		break;
    case APN_ALTA_KAF09000XD7D9_CAM_ID:
        strcpy( szModelNumber, APN_ALTA_KAF09000XD7D9_CAM_SZ );
		break;
    case APN_ALTA_KAF6302_CAM_ID:
        strcpy( szModelNumber, APN_ALTA_KAF6302_CAM_SZ );
		break;   
    case APN_ALTA_S101401108_CAM_ID:
        strcpy( szModelNumber, APN_ALTA_S101401108_CAM_SZ );
        break;

	// Ascent cameras
	case APN_ASCENT_KAF0402E_CAM_ID:
		strcpy( szModelNumber, APN_ASCENT_KAF0402E_CAM_SZ );
		break;
	case APN_ASCENT_KAF0402E2_CAM_ID:
		strcpy( szModelNumber, APN_ASCENT_KAF0402E2_CAM_SZ );
		break;
	case APN_ASCENT_KAF0402E3_CAM_ID:
		strcpy( szModelNumber, APN_ASCENT_KAF0402E3_CAM_SZ );
		break;
	case APN_ASCENT_KAF0402E4_CAM_ID:
		strcpy( szModelNumber, APN_ASCENT_KAF0402E4_CAM_SZ );
		break;

	case APN_ASCENT_KAI340_CAM_ID:
		strcpy( szModelNumber, APN_ASCENT_KAI340_CAM_SZ );
		break;
	case APN_ASCENT_KAI2000_CAM_ID:
		strcpy( szModelNumber, APN_ASCENT_KAI2000_CAM_SZ );
		break;
	case APN_ASCENT_KAI4000_CAM_ID:
		strcpy( szModelNumber, APN_ASCENT_KAI4000_CAM_SZ );
		break;
	case APN_ASCENT_KAI16000_CAM_ID:
		strcpy( szModelNumber, APN_ASCENT_KAI16000_CAM_SZ );
		break;

	default:
		Error = true;
		break;
	}

	if ( Error )
	{
		strcpy( szCamModel, "Unknown" );
	}
	else
	{
		if ( Interface == 0 )	// Network Interface
			strcat( szCamModel, "E" );

		if ( Interface == 1 )	// USB 2.0 Interface
		{
			if ( IsAltaCamera )
				strcat( szCamModel, "U" );
			else if ( IsAscentCamera )
				strcat( szCamModel, "A" );
		}

		strcat( szCamModel, szModelNumber );
	}

}


bool ApnCamModelIsAlta( unsigned short CamId, int FwRev )
{
	bool IsAltaPlatform;

	IsAltaPlatform = false;

	if ( FwRev < 100 )
		IsAltaPlatform = true;

	return ( IsAltaPlatform );
}


bool ApnCamModelIsAscent( unsigned short CamId, int FwRev )
{
	bool IsAscentPlatform;

	IsAscentPlatform = false;

	if ( FwRev < 100 )
		IsAscentPlatform = false;
	else if ( (CamId & APN_SIG_CAMERA_ID_ASCENT) == APN_SIG_CAMERA_ID_ASCENT )
 		IsAscentPlatform = true;

	return ( IsAscentPlatform );
}

