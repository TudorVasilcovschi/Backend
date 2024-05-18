import os

import psycopg2
from psycopg2 import pool

class Database:
    __connection_pool = None

    @classmethod
    def initialize(cls, **kwargs):
        if not cls.__connection_pool:
            cls.__connection_pool = pool.SimpleConnectionPool(1, 10, **kwargs)

    @classmethod
    def get_connection(cls):
        return cls.__connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        cls.__connection_pool.putconn(connection)

    @classmethod
    def close_all_connections(cls):
        cls.__connection_pool.closeall()