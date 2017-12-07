import sys
import socket
import paramiko
from get_common_utils import print_standout, print_error


class RemoteModel:
    """  remote options model
    execute remote command
    """

    def __init__(self, hostname, username, password, port=22):
        self.hostname = hostname
        self.port = port

        self.username = username
        self.password = password

        self.s = None
        self.session = None
        self.init_conn()

        self.channel_timeout = 10

    def init_conn(self):
        """
            make a connection with the remote machine
        :return:
        """
        try:
            paramiko.util.log_to_file("paramiko_log.log")
            self.s = paramiko.SSHClient()
            self.s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.s.connect(hostname=self.hostname, port=self.port, username=self.username, password=self.password)

            print_standout("Success connect the remote machine [host=%s]" % self.hostname)

        except Exception, e:
            print_error(str(e))
            print_error("Connect failed.in host[%s] user[%s] or pwd[%s] maybe wrong." % (self.hostname, self.username, self.password))
            sys.exit(-1)

    def close(self):
        """
        close
        if close can not use this connection
        :return:
        """
        if self.s:
            self.s.close()

    def execute_command(self, command):
        """
        :param command:
            execute cmd
        :return:
            the response lines
        """
        print_standout("Execute command [%s]" % command)
        stdin, stdout, stderr = self.s.exec_command(command, get_pty=True)
        stdin.write(self.password)
        stdin.write("\n")
        stdin.flush()
        try:
            stdout.channel.settimeout(self.channel_timeout)
            response_lines = stdout.readlines()
            stderr.channel.settimeout(self.channel_timeout)
            error_info = stderr.read()

            if error_info and error_info.strip():
                print_error(' remote command error info : %s' % stderr.read())
                print_error(error_info)
                return None

            # info_arr = response_info.split('\n')
            print_standout("Info: response lines are below")
            print_standout(response_lines)
            return response_lines
        except socket.timeout(), e:
            print_error("socket time out error. maybe the password[%s] and username[%s] of remote machine[%s] is not suitable." % (self.password, self.username, self.hostname))
            sys.exit(-1)


if __name__ == '__main__':
    host = "hqd-ssdpostgis-05.mypna.com"
    hostname = "shd-dpc6x64ssd-02.china.telenav.com"
    command = "sudo df /data/pgsql94/data 1>&2"
    rm = RemoteModel(host=hostname)
    lines = rm.execute_command(command)
