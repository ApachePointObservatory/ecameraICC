'''
control a remote power switch to reboot the camera

generally there would be a power switch class with instances 
of different kinds of power switches. all a user wants to see 
is on, off, status
'''
import os
import re

def power_status():
    '''
    power status
    '''
    abc = os.popen('/usr/bin/curl -s \
http://admin:foenix@power1-35m/Set.cmd?CMD=GetPower'
                ).readline()
    x = re.search('.*P60=(\d),P61=(\d),P62=(\d),P63=(\d).*', abc)
    if len(x.groups()) != 4:
        print 'not 4 ports'
        return False
    if x.groups()[3] == '1':
        return True
    print x.groups()
    return False

def power_on(port=0, name=None):
    '''
    power on port number or name
    '''
    if not port and not name:
        os.popen('/usr/bin/curl -s \
http://admin:foenix@power1-35m/Set.cmd?\
CMD=SetPower+P60=0+P61=0+P62=0+P63=1\n'
            )
    else:
        print 'port and name not implemented'

def power_off(port=0, name=None):
    '''
    power off
    '''
    if not port and not name:
        os.popen('/usr/bin/curl -s \
http://admin:foenix@power1-35m/Set.cmd?\
CMD=SetPower+P60=0+P61=0+P62=0+P63=0\n'
            )
    else:
        print 'port and name not implemented'

if __name__ == '__main__':
    print 'ecamera [on, off, status]'
