import os
import sys
import json
import glob
import optparse


def merge(in_path, out_path):
    assert os.path.isdir(in_path)
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    json_files = glob.glob(os.path.join(in_path, '*'))
    stats_list = map(_load, json_files)
    #print stats_list

    merged_stats = _merge(stats_list)

    #print merged_stats

    for osm_type, stats in merged_stats.iteritems():
        out_json = os.path.join(out_path, osm_type.lower())

        with open(out_json, 'w') as ofs:
            ofs.write(json.dumps(stats))


def _load(json_file):
    osm_type = _retrieve_osm_type(json_file)
    with open(json_file) as fp:
        return osm_type, json.load(fp)


def _retrieve_osm_type(json_file):
    osm_types = ['Nodes', 'Ways', 'Relations']

    base_name = os.path.basename(json_file)
    for osm_type in osm_types:
        if base_name.upper().startswith(osm_type.upper()):
            return osm_type


def _merge(stats_list):
    merged_stats = {}

    for osm_type, stats_item in stats_list:
        stats = merged_stats.get(osm_type, {})

        for k, v in stats_item.iteritems():
            stats[k] = stats.get(k, 0) + v

        merged_stats[osm_type] = stats

    return merged_stats


def main():
    parser = optparse.OptionParser()

    parser.add_option('-i', '--in_path', help='input json path', dest='in_path')
    parser.add_option('-o', '--out_path', help='output json path', dest='out_path')

    options, args = parser.parse_args()
    if not options.in_path or not options.out_path:
        sys.stderr.write('Error: in json path or out json path is not specified\n')
        parser.print_help()
        sys.exit(-1)

    merge(options.in_path, options.out_path)

if __name__ == '__main__':
    main()
