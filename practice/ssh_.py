import base64
import getpass
import os
import socket
import sys
import traceback

import paramiko
from paramiko.py3compat import input


# setup logging
paramiko.util.log_to_file('demo_sftp.log')

# Paramiko client configuration
Port = 22

hostname = 'localhost'
username = 'vahid'

# get host key, if we know one
hostkeytype = None
hostkey = None
try:
    host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
except IOError:
    print('*** Unable to open host keys file')
    host_keys = {}

if hostname in host_keys:
    hostkeytype = host_keys[hostname].keys()[0]
    hostkey = host_keys[hostname][hostkeytype]
    print('Using host key of type %s' % hostkeytype)


# now, connect and use paramiko Transport to negotiate SSH2 across the connection
try:
    t = paramiko.Transport((hostname, Port))
    t.connect(hostkey)
    sftp = paramiko.SFTPClient.from_transport(t)

    # dirlist on remote host
    dirlist = sftp.listdir('.')
    print("Dirlist: %s" % dirlist)

    # copy this demo onto the server
    try:
        sftp.mkdir("demo_sftp_folder")
    except IOError:
        print('(assuming demo_sftp_folder/ already exists)')
    with sftp.open('demo_sftp_folder/README', 'w') as f:
        f.write('This was created by demo_sftp.py.\n')
    with open('demo_sftp.py', 'r') as f:
        data = f.read()
    sftp.open('demo_sftp_folder/demo_sftp.py', 'w').write(data)
    print('created demo_sftp_folder/ on the server')

    # copy the README back here
    with sftp.open('demo_sftp_folder/README', 'r') as f:
        data = f.read()
    with open('README_demo_sftp', 'w') as f:
        f.write(data)
    print('copied README back here')

    # BETTER: use the get() and put() methods
    sftp.put('demo_sftp.py', 'demo_sftp_folder/demo_sftp.py')
    sftp.get('demo_sftp_folder/README', 'README_demo_sftp')

    t.close()

except Exception as e:
    print('*** Caught exception: %s: %s' % (e.__class__, e))
    traceback.print_exc()
    try:
        t.close()
    except BaseException:
        pass
    sys.exit(1)
