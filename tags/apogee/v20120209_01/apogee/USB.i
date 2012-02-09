/* File : apogeeUSB.i */
%module apogeeUSB
%{     
#define SWIG_FILE_WITH_INIT
#include "ApnCamera.h" 
%} 

%typemap(in) Apn_BayerShift = int;
%typemap(out) Apn_BayerShift = int;
%typemap(in) Apn_CameraMode = int;
%typemap(out) Apn_CameraMode = int;
%typemap(in) Apn_CoolerStatus = int;
%typemap(out) Apn_CoolerStatus = int;
%typemap(in) Apn_CoolerStatus_AtSetPoint = int;
%typemap(out) Apn_CoolerStatus_AtSetPoint = int;
%typemap(in) Apn_CoolerStatus_RampingToSetPoint = int;
%typemap(out) Apn_CoolerStatus_RampingToSetPoint = int;
%typemap(in) Apn_FanMode = int;
%typemap(out) Apn_FanMode = int;
%typemap(in) Apn_Interface = int;
%typemap(out) Apn_Interface = int;
%typemap(in) Apn_LedMode = int;
%typemap(out) Apn_LedMode = int;
%typemap(in) Apn_LedState = int;
%typemap(out) Apn_LedState = int;
%typemap(in) Apn_NetworkMode = int;
%typemap(out) Apn_NetworkMode = int;
%typemap(in) Apn_Platform = int;
%typemap(out) Apn_Platform = int;
%typemap(in) Apn_Resolution = int;
%typemap(out) Apn_Resolution = int;
%typemap(in) Apn_SerialParity = int;
%typemap(out) Apn_SerialParity = int;
%typemap(in) Apn_Status = int;
%typemap(out) Apn_Status = int;
%typemap(in) Camera_CoolerMode = int;
%typemap(out) Camera_CoolerMode = int;
%typemap(in) Camera_CoolerStatus = int;
%typemap(out) Camera_CoolerStatus = int;
%typemap(in) Camera_CoolerStatus_AtSetPoint = int;
%typemap(out) Camera_CoolerStatus_AtSetPoint = int;
%typemap(in) Camera_CoolerStatus_RampingToSetPoint = int;
%typemap(out) Camera_CoolerStatus_RampingToSetPoint = int;
%typemap(in) Camera_Status = int;
%typemap(out) Camera_Status = int;

%include "numpy.i"
%init %{
import_array();
%}

%include "ApnCamera.i"

// wrap an Apogee method with one which understands that it is getting a num    py array.
%extend CApnCamera {
   void FillImageBuffer(unsigned short *INPLACE_ARRAY2, int DIM1, int DIM2)     {
    long ret;
    unsigned short w, h;
    unsigned long count;

    ret = $self->GetImageData(INPLACE_ARRAY2, w, h, count);
    if (w != DIM1 || h != DIM2) {
       abort();
    }   
   }
};

