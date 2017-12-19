import os
import sys
import optparse
from util.import_csv import CsvImporter


class TollCostImporter(object):
    TG_MATCH_FIELDS = [
        'node_id',
        'highway_node_id',
        'tg_number',
        'is_entrance',
        'is_exit',
        'is_passing',
        'tg_class',
        'gate_count',
        'gate_flag',
    ]

    TG_MATCH_FIELD_TYPES = {
        'node_id': 'bigint',
        'highway_node_id': 'bigint',
        'tg_number': 'text',
        'is_entrance': 'int',
        'is_exit': 'int',
        'is_passing': 'int',
        'tg_class': 'int',
        'gate_count': 'int',
        'gate_flag': 'text',
    }

    def __init__(self, options, toll_cost_dir):
        self.importer = CsvImporter(options)
        self.toll_cost_dir = toll_cost_dir

    def import_toll_cost(self):
        toll_cost_files = self._get_toll_cost_files()
        headers = [TollCostImporter.TG_MATCH_FIELDS]
        field_types = [TollCostImporter.TG_MATCH_FIELD_TYPES]

        if len(toll_cost_files) != len(headers):
            raise Exception("Toll cost file count not equal to table count")

        return self.importer.import_csv(toll_cost_files, headers=headers, field_types=field_types)

    def _get_toll_cost_files(self):
        import glob

        toll_cost_files = glob.glob(os.path.join(self.toll_cost_dir, "TGMATCH.txt"))
        toll_cost_files.extend(glob.glob(os.path.join(self.toll_cost_dir, "TGMATCH.TXT")))

        toll_cost_files = [os.path.abspath(f) for f in toll_cost_files]
        return toll_cost_files


def validate(options):
    if not options.host:
        print 'Error: host not specified!'
        return False
    if not options.database:
        print 'Error: db name not specified!'
        return False
    if not options.tollcost:
        print 'Error: toll cost dir not exists!'
        return False

    return True


def main():
    parser = optparse.OptionParser()

    parser.add_option('-H', '--host', help='hostname', dest='host', default='localhost')
    parser.add_option('-P', '--port', help='port, default=5432', dest='port', default='5432')
    parser.add_option('-U', '--user', help='user, default=postgres', dest='user', default='postgres')
    parser.add_option('-p', '--passwd', help='password, optional', dest='passwd', default='postgres')
    parser.add_option('-D', '--dbname', help='database', dest='database')
    parser.add_option('-S', '--schema', help='schema', dest='schema', default='public')
    parser.add_option('-t', '--tollcost', help='toll cost dir', dest='tollcost')

    options, args = parser.parse_args()

    if not validate(options):
        parser.print_help()
        sys.exit(-1)

    importer = TollCostImporter(options, options.tollcost)
    importer.import_toll_cost()


if __name__ == '__main__':
    main()
