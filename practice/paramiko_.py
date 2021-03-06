from sqlalchemy_media.ssh import SSHClient

if __name__ == '__main__':
    ssh = SSHClient()
    ssh.load_config_file()
    ssh.connect('carrene-new')
    stdin, stdout, stderr = ssh.exec_command('ls')
    print(stdout.read().decode())

    try:
        f = ssh.sftp.file('a.txt', mode='w')
        f.write(b'TEST text')
        f.close()

    finally:
        ssh.sftp.close()
