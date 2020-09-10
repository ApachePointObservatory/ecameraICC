/* This file contains the tcl interface routine to high level
   API for CCD frame processing
   Author : Dave Mills (The Random Factory
   Date   : 20 Dec 2000
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sys/shm.h>

#include <cfitsio/fitsio.h>

/* typedef unsigned short *PDATA;  */
typedef void *PDATA;  

#define MAX_CCD_BUFFERS  1000
#define MAX_BIAS_COLS 20
#define MAX_ROWS 32767
#define MAX_COLS 32767
#define RED_FITS   1
#define GREEN_FITS 2
#define BLUE_FITS  3
#define GEOM_BAYER 1
int     iamcolor;

int     ierror;
int     CCD_BUFCOUNT = 0;

typedef struct {
     unsigned short *pixels;
     int            size;
     short          xdim;
     short          ydim;
     short          zdim;
     short          xbin;
     short          ybin;
     short          type;
     char           name[64];
     int            shmid;
     size_t         shmsize;
     char           *shmem;
} CCD_FRAME;

CCD_FRAME CCD_Frame[MAX_CCD_BUFFERS];

int     CCD_cameranum =0;
float   exposure=0.0;



unsigned short *error;
int     bias_start, bias_end, bcols;
int     bias_rstart, bias_rend, brows;
int     geometry_change = 0;
int     last_imgrows = 1;
int     last_imgcols = 1;
int     last_hbin = 1;
int     last_vbin = 1;

PDATA CCD_locate_buffer(char *name, int idepth, short imgcols, short imgrows, short hbin, short vbin);
int   CCD_free_buffer();
int   CCD_locate_buffernum(char *name);

PDATA CCD_locate_buffer(char *name, int idepth, short imgcols, short imgrows, short hbin, short vbin)
{
     int nb; 
     PDATA bptr;
     int found;
     int i;

     found = -1;
     i = 0;
     bptr = NULL;
 
     while (found<0 && i<MAX_CCD_BUFFERS) {

       if (CCD_Frame[i].pixels != NULL) {
         if (strcmp(name,CCD_Frame[i].name) == 0) {
            bptr = CCD_Frame[i].pixels;
            found = i;
         } 
       }
       i++;
     }
       
     geometry_change = 0;
     if (imgcols != last_imgcols) {geometry_change=1;}
     if (imgrows != last_imgrows) {geometry_change=1;}
     if (hbin != last_hbin) {geometry_change=1;}
     if (vbin != last_vbin) {geometry_change=1;}
     if (geometry_change == 1) {
        found = -1;
        CCD_free_buffer(name);
        CCD_free_buffer("calibrated");
     }

     if (found < 0) {
       nb = (imgrows/hbin)*imgcols/vbin*idepth+4;
       i=0;
       while (CCD_Frame[i].pixels != 0 && i<MAX_CCD_BUFFERS) {i++;}
       bptr = ((PDATA) malloc(nb));
       CCD_Frame[i].pixels = bptr;
       strcpy(CCD_Frame[i].name,name);
       CCD_Frame[i].size = nb;
       CCD_Frame[i].xdim = imgcols/hbin;
       CCD_Frame[i].ydim = imgrows/vbin;
       CCD_Frame[i].xbin = hbin;
       CCD_Frame[i].ybin = vbin;
       CCD_Frame[i].zdim = idepth;
       CCD_Frame[i].shmid = 0;
       CCD_Frame[i].shmsize = 0;
       CCD_Frame[i].shmem = NULL;
       if (geometry_change == 1) {
          last_imgcols = imgcols;
          last_imgrows = imgrows;
          last_hbin = hbin;
          last_vbin = vbin;
       }
     }
     return(bptr);
}


int CCD_locate_buffernum(char *name)
{
     int found;
     int i;

     found = -1;
     i = 0;

     while (found<0 && i<MAX_CCD_BUFFERS) {

       if (CCD_Frame[i].pixels != NULL) {
         if (strcmp(name,CCD_Frame[i].name) == 0) {
            found = i;
         }
       }
       i++;
     }

     return(found);
}

int CCD_free_buffer(char *name)
{
  
     int found;
     int i;

     found = -1;
     i = 0;
 
     while (found<0 && i<MAX_CCD_BUFFERS) {

       if (CCD_Frame[i].pixels != NULL) {
         if (strcmp(name,CCD_Frame[i].name) == 0) {
            found = i;
         } 
       }
       i++;
     }
  
     if (found >= 0) {
        free(CCD_Frame[found].pixels);
        CCD_Frame[found].pixels = NULL;
        CCD_Frame[found].size = 0;
        strcpy(CCD_Frame[found].name,"NOT-IN-USE");
        if (CCD_Frame[found].shmem != NULL) {
           shmdt(CCD_Frame[found].shmem);
           CCD_Frame[found].shmem = NULL;
        }
     }
     return(0);
}


int printerror( int status)
{
    /*****************************************************/
    /* Print out cfitsio error messages and exit program */
    /*****************************************************/


    if (status)
    {
       fits_report_error(stderr, status); /* print error report */

       exit( status );    /* terminate the program, returning error status */
    }
    return 0;
}

