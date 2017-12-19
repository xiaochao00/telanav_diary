import os
import sys
import psycopg2
import psycopg2.extras
from psycopg2 import Warning, Error
import time

class AddContentImporter(object):
    """
        class comment
    """
    CN_ADD_CONTENT = 'usr.cn_add_content'

    def __init__(self, db_args):
        self.add_dir = dir
        self.db_args = db_args
        self.conn = None
        self.cursor = None

        self.init()

    def init(self):
        try:
            self.conn = psycopg2.connect(self.db_args)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except Error,e:
            sys.stderr.write(e.__str__())
            sys.exit(-1)
        except Exception, e:
            sys.stderr.write(e.__str__())
            sys.exit(-1)

    def update(self, add_dir):
        if not os.path.exists(add_dir):
            return False

        self.__init_tables()

        conts = {}
        for f in os.listdir(add_dir):
            path = os.path.join(add_dir, f)
            for line in open(path):
                fields = line.strip().split(';')
                items = [i.split('=') for i in fields]

                feat_id = self._get_attribute('Feature_ID', items)
                typ = self._get_attribute('Content_Type', items)

                if not feat_id or not typ:
                    print 'No Feature_ID or no Type, [%s]' % line.strip()
                    continue

                elevated = self._get_attribute('Elevated_Road', items)
                overpass = self._get_attribute('Overpass', items)
                underpass = self._get_attribute('Underpass', items)

                attributes = conts.setdefault((feat_id, typ), ['N', 'N', 'N'])
                if elevated: attributes[0] = elevated
                if overpass: attributes[1] = overpass
                if underpass: attributes[2] = underpass

        TMP_FILE = '__tmp__'
        ofs = open(TMP_FILE, 'w')
        for key in conts:
            feat_id, typ = key
            elevated, overpass, underpass = conts[key]

            line = '%s\n' % ','.join((feat_id, typ, elevated, overpass, underpass))
            ofs.write(line)
        ofs.close()

        try:
            with open(TMP_FILE) as ifs:
                self.cursor.copy_from(ifs, AddContentImporter.CN_ADD_CONTENT, sep=',')

            # commit at once
            self.conn.commit()

        except Error,e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            sys.exit(-1)
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            sys.exit(-2)
        finally:
            if os.path.exists(TMP_FILE):
                os.remove(TMP_FILE)

        print 'Update Add content successfully!'

        return True

    def _get_attribute(self, key, items):
        for i in items:
            if i[0] == key:
                return i[1]
        return None


    def __init_tables(self):
        table = None

        sql = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' and tablename = '%s'" % AddContentImporter.CN_ADD_CONTENT
        self.cursor.execute(sql)
        for rec in self.cursor:
            table = rec[0]

        if table: return

        sql = """
                CREATE TABLE IF NOT EXISTS %s
                (
                    feature_id bigint,
                    type text,
                    elevated_road char,
                    overpass char,
                    underpass char
                )
        """ % AddContentImporter.CN_ADD_CONTENT

        try:
            self.cursor.execute(sql)
            # commit at once
            self.conn.commit()
        except Error,e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            sys.exit(-1)
        except Exception, e:
            self.conn.rollback()
            sys.stderr.write(e.__str__())
            sys.exit(-2)


def main():
    import optparse
    parser = optparse.OptionParser()

    parser.add_option('-C', '--add-content', help='add content dir', dest='add')
    parser.add_option('-H', '--host', help='hostname', dest='host')
    parser.add_option('-P', '--port', help='port', dest='port')
    parser.add_option('-U', '--user', help='user', dest='user')
    parser.add_option('-p', '--passwd', help='password', dest='passwd')
    parser.add_option('-D', '--dbname', help='dbname', dest='dbname')


    options, args = parser.parse_args()

    if not options.port: options.port = '5432'
    if not options.user: options.user = 'postgres'
    if not options.passwd: options.passwd = 'postgres'

    if not options.add or not os.path.isdir(options.add):
        print 'Error: addition content dir is not specified!'
        parser.print_help()
        return

    if not options.host:
        print 'Error: host is not specified!'
        parser.print_help()
        return

    if not options.dbname:
        print 'Error: dbname is not specified!'
        parser.print_help()
        return

    db_args = "host=%s port=%s user=%s password=%s dbname=%s" %(options.host, options.port, options.user, options.passwd, options.dbname)

    importer = AddContentImporter(db_args)
    importer.update(options.add)

if __name__ == '__main__':
    main()




