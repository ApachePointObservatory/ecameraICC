
def get_power():
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

def power_on():
    os.popen('/usr/bin/curl -s \
http://admin:foenix@power1-35m/Set.cmd?\
CMD=SetPower+P60=0+P61=0+P62=0+P63=1\n'
            )

def power_off():
    os.popen('/usr/bin/curl -s \
http://admin:foenix@power1-35m/Set.cmd?\
CMD=SetPower+P60=0+P61=0+P62=0+P63=0\n'
            )
