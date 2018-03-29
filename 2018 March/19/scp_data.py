import os
import stat
import sys
import traceback

import paramiko


class SFTPConnection(object):
    def __init__(self, host, username, password, port=22):
        try:
            self.transport = paramiko.Transport(sock=(host, port))
            self.transport.connect(username=username, password=password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        except Exception, e:
            traceback.print_exc()
            sys.stderr.write("%s \n" % e)
            sys.exit(-1)

    def __del__(self):
        if self.transport:
            self.transport.close()

    def list_dir(self, dir_path):
        try:
            return self.sftp.listdir(dir_path)
        except IOError, e:
            traceback.print_exc()
            sys.stderr.write("%s \n" % e)
            sys.exit(-1)

    def traverse_directory(self, base_dir, deep=1):
        """Directory Traverse"""
        dir_stru = {}
        base_dir_name = os.path.basename(base_dir)
        dir_list = self.list_dir(base_dir)

        for dir_name in dir_list:
            dir_path = os.path.join(base_dir, dir_name)
            if stat.S_ISDIR(self.sftp.stat(dir_path).st_mode):
                if deep > 1:
                    dir_stru.setdefault(base_dir_name, []).append(self.traverse_directory(base_dir=dir_path,
                                                                                          deep=deep - 1))
                else:
                    dir_stru.setdefault(base_dir_name, []).append(dir_name)
            else:
                dir_stru.setdefault(base_dir_name, []).append(dir_name)

        if not dir_list:
            dir_stru.setdefault(base_dir_name, []).append("")
        return dir_stru

    def download_file(self, file_path_src, file_dir_des):
        file_path_des = os.path.join(file_dir_des, os.path.basename(file_path_src))
        if os.path.exists(file_path_des):
            sys.stderr.write("Download File[%s] have exist. Ignore it.\n" % file_path_des)
            return
        if not os.path.exists(file_dir_des):
            os.mkdir(file_dir_des)
        sys.stdout.write("File[%s] size is %s \n" % (file_path_src, self.sftp.stat(file_path_src).st_size))

        try:
            self.sftp.get(file_path_src, file_path_des)
        except IOError, e:
            traceback.print_exc()
            sys.stderr.write("%s \n" % e)
            sys.exit(-1)

        sys.stdout.write("Download file[%s] to [%s] done.\n" % (file_path_src, file_path_des))

    def download_directory(self, dir_path_src, dir_path_des):
        if not os.path.exists(dir_path_des):
            os.mkdir(dir_path_des)
        for sub_dir_name in self.list_dir(dir_path_src):
            sub_dir_path = os.path.join(dir_path_src, sub_dir_name)
            if stat.S_ISDIR(self.sftp.stat(sub_dir_path).st_mode):
                self.download_directory(sub_dir_path, os.path.join(dir_path_des, sub_dir_name))
            else:
                self.download_file(sub_dir_path, dir_path_des)
        sys.stdout.write("Download data from directory[%s] to [%s] done.\n" % (dir_path_src, dir_path_des))


def scp(hostname, sftp_username, sftp_password, source_data_path, des_data_path):
    try:
        sftp = SFTPConnection(host=hostname, username=sftp_username, password=sftp_password)
        sftp.download_directory(source_data_path, des_data_path)
        return True
    except IOError, e:
        traceback.print_exc()
        sys.stderr.write("%s" % e)
    return False


def main():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-H", "--host-name", help="host name", dest="sftp_hostname")
    parser.add_option("-U", "--username", help="user name", dest="sftp_username")
    parser.add_option("-P", "--password", help="sftp login password", dest="sftp_password")
    parser.add_option("-S", "--source-data-path", help="source data path in remote host", dest="source_data_path")
    parser.add_option("-O", "--output-destination-data-path", help="output path for scp data", dest="des_data_path")

    parameter_dict, args = parser.parse_args()
    sftp_hostname = parameter_dict.sftp_hostname
    sftp_username = parameter_dict.sftp_username
    sftp_password = parameter_dict.sftp_password
    source_data_path = parameter_dict.source_data_path
    des_data_path = parameter_dict.des_data_path
    # check
    if not sftp_password or not sftp_username or not sftp_hostname or not des_data_path or not source_data_path:
        parser.print_help()
        sys.exit(-1)
    # scp
    if not scp(hostname=sftp_hostname, sftp_password=sftp_password, sftp_username=sftp_username,
               source_data_path=source_data_path, des_data_path=des_data_path):
        sys.stderr.write("Error: SCP failed. \n")
        sys.exit(-1)


if __name__ == '__main__':
    main()
