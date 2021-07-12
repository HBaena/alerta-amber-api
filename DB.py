import json
from psycopg2 import pool
import logging
from os import getcwd, path

logging.basicConfig(filename='db.log', level=logging.DEBUG)


class PoolConection:
    def __init__(self,config_filename):
        raise NotImplementedError

    def get_connection(self):
        raise NotImplementedError

    def release_connection(self):
        raise NotImplementedError


class PosgresPoolConnection(PoolConection):

    def __init__(self, config_filename):
        with open(config_filename, "r") as file:
            db_args = json.loads(file.read())
            pool_size = db_args.pop("pool_size")
        self.pool = pool.ThreadedConnectionPool(
            minconn=pool_size,
            maxconn=pool_size,
            **db_args
        )


    def get_connection(self):
        return self.pool.getconn()


    def release_connection(self, connection):
        try:
            self.pool.putconn(connection)
            return True
        except Exception as e:
            logging.debug(str(e))
            return False


    def  __del__(self):
        try:
            self.pool.closeall()
            return True
        except Exception as e:
            logging.debug(str(e))
            return False
