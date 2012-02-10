'''
debugLog - 

levels:

    error = 0
    warning = 1
    info = 2
    debug = 3
'''
import logging

# do i need to protect against multiple imports?
logging.basicConfig(filename='/tmp/ecamera.log', level=logging.DEBUG)

DEBUG_ERROR = 0
DEBUG_WARN = 1
DEBUG_INFO = 2
DEBUG_DEBUG = 3
DEBUG_LEVEL = DEBUG_DEBUG         # allow all levels

def DEBUG(message, level=0):
    '''
    generic debug message
    '''
    if level > DEBUG_LEVEL:
        return
    #syslog.syslog(message.strip())
    logging.debug(message)
