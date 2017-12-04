def parse_df_responselines(self,responselines):
    '''
    :param responselines:
    the repsonselines of command 'df -m directory
    :return:
    parser the size of 'Available'
    '''
    if len(responselines) != 2:
        standout_print('get space size of remote remain is failed.Sorry ')
        return None

    # names = response_lines[0].strip().split()
    names = ['Filesystem', '1K-blocks', 'Used', 'Available', 'Use%', 'Mounted on']
    values = responselines[1].strip().split()

    response_dict = {}
    for i in range(len(names)):
        name = names[i]
        value = values[i]
        response_dict[name] = value

    if not response_dict or not response_dict.has_key('Available'):
        standout_print(' response of cmd  failed. please check')
        return None

    available_size = int(response_dict['Available'])

    return available_size


def localhost_remaining_spacesize(directory_path):
    '''
     unit size : MB
    :param directory_path:

    :return:
        free space of directory_path
    '''
    import platform
    import ctypes

    size = 0
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(directory_path), None, None,
                                                   ctypes.pointer(free_bytes))
        size = free_bytes.value  / 1024 / 1024
    else:

        try:
            # problem of  Permission denied:
            st = os.statvfs(directory_path)
            size = st.f_bavail * st.f_frsize  / 1024 / 1024

        except Exception,e:
            import commands
            a,b = commands.getstatusoutput('sudo df -m %s' %  directory_path)
            # a the Exit status; b the output
            if a == 0:
                size = parse_df_responselines(b.split('\n'))
            else:
                standout_print("Error: compute remain size of localhost failed. need check")
                return None

    size = '%.3f' % size

    return size
def standout_print(info):
    '''
    print information to standout
    :param info:
    :return:
    '''
    sys.stderr.write(info + "\n")

