from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error
from .config import settings


def connect():
    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        autocommit=False,
    )

@contextmanager
def db_cursor(dictionary=False):
    conn = connect()
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
