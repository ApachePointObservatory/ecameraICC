#ifdef LINUX
#define MAX_INTEL_HEX_RECORD_LENGTH 16
#include <sys/types.h>
typedef struct _INTEL_HEX_RECORD
{
  unsigned char   Length;
  unsigned int    Address;
  unsigned char   Type;
  unsigned char   Data[MAX_INTEL_HEX_RECORD_LENGTH];
} INTEL_HEX_RECORD, *PINTEL_HEX_RECORD;
#endif


