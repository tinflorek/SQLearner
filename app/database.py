import sqlite3
import os 

class NoResultSetError(Exception):
    pass

def build_sandbox(table_query, insert_query):

    sqlite_connection = sqlite3.connect(':memory:')
    cursor = sqlite_connection.cursor()

    try:
        for table in table_query:
            cursor.execute(table)

        for insert in insert_query:
            cursor.execute(insert)
    except sqlite3.Error as e:
        sqlite_connection.close()
        raise 
    except Exception as e:
        sqlite_connection.close()
        raise

    return sqlite_connection

def run_query(cursor, user_query):

    cursor.execute(user_query)

    if cursor.description is None:
        raise NoResultSetError("This is not a SELECT query — this is for reading data.")

    columns = [desc[0] for desc in cursor.description]

    return cursor.fetchall(), columns

def compare_results(user_results, correct_results, order_matters):
    if order_matters:
        return user_results == correct_results
    else:
        return sorted(user_results) == sorted(correct_results)

def print_table(rows, col_names):
    widths = [max(len(col), max((len(str(row[i])) for row in rows), default=0)) for i, col in enumerate(col_names)]
    header = " | ".join(f"{col:<{widths[i]}}" for i, col in enumerate(col_names))
    separator = "-+-".join("-" * w for w in widths)
    print(header)
    print(separator)
    for row in rows:
        print(" | ".join(f"{str(val):<{widths[i]}}" for i, val in enumerate(row)))

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

SQLITE_OK = 0
SQLITE_DENY = 1

BLOCKED_ACTIONS = {
    sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_UPDATE,
    sqlite3.SQLITE_INSERT,
    sqlite3.SQLITE_DROP_TABLE,
    sqlite3.SQLITE_CREATE_TABLE,
    sqlite3.SQLITE_ALTER_TABLE,
}

def authorizer(action, arg1, arg2, db_name, trigger):
    if action in BLOCKED_ACTIONS:
        return SQLITE_DENY
    return SQLITE_OK