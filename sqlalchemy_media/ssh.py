import asyncio
import subprocess
import uuid
from os.path import dirname, join, basename
import logging


logger = logging.getLogger('ssh')
logger.addHandler(logging.NullHandler())

chunk_size = 1024


class SubprocessSSHClient(object):

    def __init__(self, host, ssh_executable='/usr/bin/ssh', scp_executable='/usr/bin/scp -3', max_tries=5, debug=False):
        self.host = host

        if debug:
            self.ssh_executable = '%s -v' % ssh_executable
            self.scp_executable = '%s -v' % scp_executable
        else:
            self.ssh_executable = ssh_executable
            self.scp_executable = scp_executable

        self.max_tries = max_tries

    @staticmethod
    def quote_filename_for_scp(filename):
        return filename.replace(' ', '\\ ').replace(')', '\\)').replace('(', '\\(')

    @staticmethod
    def quote_filename_for_ssh(filename):
        return '\\"%s\\"' % filename

    def execute_ssh_command(self, remote_command, stdin=None, retry_count=0):
        cmd_string = ' '.join([
            self.ssh_executable,
            self.host,
            '"%s"' % remote_command
        ])

        cmd = subprocess.Popen(
            cmd_string,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=stdin,
        )
        stdout, stderr = cmd.communicate()
        stdout, stderr = stdout.strip(), stderr.strip()

        if stderr:
            logger.error(stderr)

        if stdout:
            logger.debug(stdout)

        if cmd.returncode != 0:
            if retry_count <= self.max_tries:
                # retrying
                if stdin is not None and stdin.can_seek():
                    stdin.seek(0)
                return self.execute_ssh_command(remote_command, stdin=None, retry_count=retry_count + 1)
            else:
                raise SshClientError(cmd_string, cmd.returncode, stderr)

        return stdout

    def execute_scp_command(self, args, retry_count=0, **kw):
        cmd_string = ' '.join([
            self.scp_executable,
            args
        ])

        logger.debug("Executing: %s" % cmd_string)

        cmd = asyncio.create_subprocess_shell(
            cmd_string,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kw
        )
        stdout, stderr = cmd.communicate()
        stdout, stderr = stdout.strip(), stderr.strip()

        if stderr:
            logger.error(stderr)

        if stdout:
            logger.debug(stdout)

        if cmd.returncode != 0:
            if retry_count <= self.max_tries:
                # retrying
                return self.execute_scp_command(args, retry_count=retry_count+1, **kw)
            else:
                raise SshClientError(cmd_string, cmd.returncode, stderr)

        return stdout

    def store_file(self, src_file, dest_path):
        """
        feeding stdin
        See http://stackoverflow.com/a/37710228/680372
        :param src_file:
        :param dest_path:
        :return:
        """
        dir_name = dirname(dest_path)
        stdout, stderr = [], []

        def async_file_reader(f, buffer):
            for l in f:
                if l:
                    buffer.append(l.decode().strip())
                else:
                    break

        def async_file_writer(source_file, target_file):
            while True:
                input_chunk = source_file.read(chunk_size)
                if input_chunk:
                    target_file.write(input_chunk)
                else:
                    target_file.write_eof()
                    break
            target_file.drain()

        cmd_string = ' '.join([
            self.ssh_executable,
            self.host,
            '"mkdir -p %s && cat - > %s"' % (
                self.quote_filename_for_ssh(dir_name),
                self.quote_filename_for_ssh(dest_path)
            )
        ])

        logger.debug("Executing: %s" % cmd_string)

        cmd = asyncio.create_subprocess_shell(
            cmd_string,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        asyncio.gather(*[
            async_file_reader(cmd.stdout, stdout),
            async_file_reader(cmd.stderr, stderr),
            async_file_writer(src_file, cmd.stdin)
        ])

        status = cmd.wait()
        stdout, stderr = '\n'.join(stdout), '\n'.join(stderr)

        if stderr:
            logger.error(stderr)

        if stdout:
            logger.debug(stdout)

        if status != 0:
            raise SshClientError(cmd_string, cmd.returncode, stderr)

    def replicate(self, src_host, src_filename, dst_filename):
        dst_dirname = dirname(dst_filename)
        self.execute_ssh_command('mkdir -p %s' % self.quote_filename_for_ssh(dst_dirname))
        self.execute_scp_command("-r %(src_host)s:'%(src_filename)s' %(dst_host)s:'%(dst_filename)s'" % dict(
            src_host=src_host,
            src_filename=self.quote_filename_for_scp(src_filename),
            dst_host=self.host,
            dst_filename=self.quote_filename_for_scp(dst_filename)
        ))

    def move_file_to_trash(self, filename, destination_filename):
        destination_directory = dirname(destination_filename)
        destination_filename = join(destination_directory, '%s_%s' % (uuid.uuid1(), basename(filename)))
        self.execute_ssh_command('mkdir -p %s; mv %s %s' % (
            self.quote_filename_for_ssh(destination_directory),
            self.quote_filename_for_ssh(filename),
            self.quote_filename_for_ssh(destination_filename)
        ))

    def delete_file(self, filename):
        self.execute_ssh_command('rm %s' % self.quote_filename_for_ssh(filename))

    def get_idle_time(self):
        output = self.execute_ssh_command(
            "iostat -c | tail -n 2 | head -n 1 | awk '{ print $6 }'"
        )
        return float(output.strip())


class SshClientError(Exception):
    exit_status = None

    def __init__(self, cmd, status, msg):
        self.cmd = cmd
        self.exit_status = status
        super(SshClientError, self).__init__('SSH Error: [%s] %s\nExecuting Command: %s' % (
            status,
            msg,
            cmd
        ))
