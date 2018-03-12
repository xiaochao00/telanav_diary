import os
import sys
from multiprocessing import pool


def upload_file(local_file_path, remote_dir_path, remote_host):
    """

    :param local_file_path:
    :param remote_dir_path:
    :param remote_host: user@host
    :return:
    """
    full_path_remote = "%s%s" % (remote_host, remote_dir_path)
    scp_cmd = "scp  %s %s" % (local_file_path, full_path_remote)
    if os.system(scp_cmd):
        sys.stdout.write("scp file success from[%s] to [%s].\n" % (local_file_path, full_path_remote))
        return True
    return False


def upload_dir(local_dir_path, remote_dir_path, remote_host):
    """

    :param local_dir_path:
    :param remote_dir_path:
    :param remote_host: user@host
    :return:
    """
    local_file_list = []
    remote_dir_list = []
    for root, dirs, filename_list in os.walk(local_dir_path):
        for filename in filename_list:
            full_path_file = os.path.join(root, filename)
            # create directory structure
            new_dir = full_path_file.replace(local_dir_path, "").strip(os.altsep)
            if not new_dir:
                local_file_list.append(full_path_file)
                remote_dir_list.append(remote_dir_path)
                continue

            new_remote_dir = os.path.join(remote_dir_path, new_dir)
            ssh_cmd = "ssh %s 'mkdir -p %s'" % (remote_host, new_remote_dir)
            sys.stdout.write("%s\n" % ssh_cmd)
            if os.system(ssh_cmd):
                sys.stdout.write("create remote path [%s] in .\n" % new_remote_dir)
            else:
                sys.stdout.write("Remote path[%s] have already created. Ignore it.\n" % new_remote_dir)
            local_file_list.append(full_path_file)
            remote_dir_list.append(new_remote_dir)
    # sort make big file as first
    local_remote_list = zip(local_file_list, remote_dir_list)
    local_remote_list.sort(key=lambda f: os.path.getsize(f[0]))
    local_remote_list.reverse()
    print local_remote_list
    #
    multi_pool = pool.Pool(8)
    result_list = []
    for local_path, remote_path in local_remote_list:
        res = multi_pool.apply_async(upload_file, (local_path, remote_path, remote_host))
        result_list.append(res)
    multi_pool.close()
    multi_pool.join()
    for res in result_list:
        status = res.get()
        if not status:
            sys.stderr.write("scp failed.\n")
            sys.exit(-1)
    sys.stdout.write("Upload data finish. From [%s] to [%s%s].\n" % (local_dir_path, remote_host, remote_dir_path))


if __name__ == '__main__':
    local_dir_path = "/home/mapuser/shichao/data_download/SEA/__rdf"
    remote_dir_path = "/home/mapuser/2_NAVTEQ/1_RDF/test/test_multi_scp"
    remote_host = "mapuser@172.16.102.140"
    upload_dir(local_dir_path=local_dir_path, remote_dir_path=remote_dir_path, remote_host=remote_host)
