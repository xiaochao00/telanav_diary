# -*- coding: utf8 -*-
import itertools
import os
from collections import OrderedDict


def process_dir(src_dir, des_dir):
    files = [os.path.join(src_dir, f) for f in os.listdir(src_dir)]
    files = [f for f in files if os.path.isfile(f)]

    for file_name in files:
        process_file(file_name, des_dir)


def process_file(file_name, des_dir):
    with open(file_name) as ifs:
        line = ifs.readline()
        main_type = None
        if len(line.split('|')) == 4 or len(line.split('|')) == 6:
            main_type = os.path.splitext(os.path.basename(file_name))[0]
        process_file_imp(file_name, des_dir, main_type)


def process_file_imp(src, des, type=None):
    """
    :param src:
    :param des:
    :return:
    """
    des_records = {}

    i = 0
    for line in open(src):
        i += 1
        if i == 1: continue

        if not line.strip(): continue

        fields = process_line(type, line)
        main_type, ad_code, province, sub_type, counts = fields
        for count_index, count in enumerate(counts):
            new_main_type = main_type if not count_index else main_type + "_%s" % count_index
            des_records.setdefault(new_main_type, dict()).setdefault((ad_code, province), dict())[sub_type] = count

    for main_type, provinces in des_records.iteritems():
        sub_types = []
        for _, type_count in provinces.iteritems():
            sub_types.extend(type_count.keys())

        sub_types = sorted(list(set(list(sub_types))))

        records = [';'.join(['ad_code', 'province'] + sub_types)]
        for admin, type_count in sorted(provinces.iteritems()):
            ad_code, province_name = admin
            ad_code = ad_code[:2]

            counts = map(str, [type_count.setdefault(sub_type, 0) for sub_type in sub_types])

            record = ';'.join([ad_code, province_name] + counts)
            records.append(record)

        des_file = os.path.join(des, main_type)
        with open(des_file, 'w') as ofs:
            ofs.write('\n'.join(records))


def process_line(type, line):
    if type:
        return process_line_b(type, line)
    else:
        return process_line_a(type, line)


def process_line_a(type, line):
    """
    main_type;ad_code;province_name;sub_type;count
    :return:
    """
    print line
    columns = map(lambda x: x.strip(), line.split(';'))
    main_type, ad_code, province_name, sub_type, counts = columns[0], columns[1], columns[2], columns[3], columns[4:]
    return [ad_code, province_name, sub_type, counts]


def process_line_b(type, line):
    """
    ad_code|province_name|sub_type|count
    :return:
    """
    print line
    columns = map(lambda x: x.strip(), line.split('|'))
    ad_code, province_name, sub_type, counts = columns[0], columns[1], columns[2], columns[3:]
    return [type, ad_code, province_name, sub_type, counts]


def main():
    import sys
    import optparse

    parser = optparse.OptionParser()
    parser.add_option('-i', '--src', help='src dir', dest='src')
    parser.add_option('-o', '--des', help='des dir', dest='des')

    options, args = parser.parse_args()
    if not options.src or not os.path.isdir(options.src):
        sys.stderr.write("Error: src dir not exists!")
        parser.print_help()
        sys.exit(-1)
    if not options.des or not os.path.isdir(options.des):
        sys.stderr.write("Error: des dir not exists!")
        parser.print_help()
        sys.exit(-1)

    src_dir = options.src
    des_dir = options.des
    process_dir(src_dir, des_dir)


if __name__ == '__main__':
    main()

#
# f_path = "traffic_signals_result.txt"
#
# with open(f_path, "r") as f:
#     province_rc_count_dict = OrderedDict({})
#     for line in f:
#         if not line.strip():
#             continue
#         p, rc, count = line.strip().split("|")
#
#         province_rc_count_dict.setdefault(p, OrderedDict({})).setdefault(rc, count)
