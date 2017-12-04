
import psycopg2


def get_all_databasename():
    databasenames = []
    conn = get_connection("postgres")
    rows = excute_sql(conn,"select pg_database.datname from pg_database")
    for row in rows:
       print row[0]
    close_conn(conn)

def get_data_basedirectory(conn):
    rows = excute_sql(conn, "show data_directory;")
    for row in rows:
        print row[0]
    # close_conn(conn)

def get_all_tablespace(conn):
    rows = excute_sql(conn, "select spcname, pg_tablespace_location(oid) from pg_tablespace;")
    for row in rows:
        for i in range(len(row)):
            print row[i],
        print

def get_connection(databsename):
    conn = psycopg2.connect(database=databsename, user="postgres", password="postgres", host="hqd-ssdpostgis-04.mypna.com",
                     port="5432")
    return conn

def excute_sql(conn,sql):
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()

    return rows

def close_conn(conn):
    if conn != None:
        conn.close()

if __name__ == '__main__':
    conn = get_connection('postgres')
    get_data_basedirectory(conn)
    get_all_tablespace(conn)
    close_conn(conn)
