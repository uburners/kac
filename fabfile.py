from fabric import task
from fabric.group import SerialGroup, ThreadingGroup

import warnings
warnings.filterwarnings("ignore")

@task
def turngate(c):
    group = SerialGroup('root@25.63.197.128', 'root@25.63.236.172')
    for c in group:
        print(c)
        c.run('mount -o remount,rw /')
        c.local(f'scp -r turngate root@{c.host}:')
        c.run('mount -o remount,ro /')
        c.run('systemctl restart turngate')


@task
def upload_and_unpack(c):
    pass
    print(c)
    # if c.run('test -f /opt/mydata/myfile', warn=True).failed:
        # c.put('myfiles.tgz', '/opt/mydata')
        # c.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')
