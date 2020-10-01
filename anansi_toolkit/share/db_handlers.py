import sqlite3

# TODO: Cuidar do parâmetro 'attributes'


class SQLite3:

    __slots__ = [
        "_db_name",
        "_table_name",
        "_primary_key",
        "_order_key",
        "table_exists"
    ]

    def __init__(self, db_name: str,
                 table_name: str,
                 primary_key: str = None,
                 order_key: str = None):
        self._db_name = db_name
        self._table_name = table_name
        self._primary_key = primary_key
        self._order_key = order_key if order_key != None else primary_key
        self.table_exists = False

    def _perform_sql(self, query):

        try:
            with sqlite3.connect(self._db_name) as conn:
                c = conn.cursor()
                c.execute(query)
            _status = True

        except (Exception, sqlite3.OperationalError) as e:
            print(e)
            _status = False

        finally:
            c.close()
            conn.close()

        return _status

    def create_table(self):
        query = "CREATE TABLE IF NOT EXISTS {} {};".format(
            self._table_name, self.attributes)

        self.table_exists = self._perform_sql(query)

    def rename_table_to(self, new_table_name: str):
        query = "ALTER TABLE {} RENAME TO {};".format(
            self._table_name, new_table_name)

        renamed = self._perform_sql(query)
        if renamed:
            self._table_name = new_table_name

    def drop_table(self):
        query = "DROP TABLE IF EXISTS {};".format(self._table_name)
        self._perform_sql(query)

    def append_dataframe(self, dataframe_to_append):
        self._save_in_slices(dataframe_to_append)

    def _save_in_slices(self, dataframe_in, step=500):
        _end = len(dataframe_in)

        for i in range(0, _end, step):
            _from, _until = i, i + step

            if _until > _end:
                _until = _end
            self._append_dataframe(dataframe_in[_from:_until])

    def _append_dataframe(self, dataframe_to_append):

        try:
            with sqlite3.connect(self._db_name) as conn:
                dataframe_to_append.to_sql(
                    name=self._table_name,
                    con=conn,
                    if_exists="append",
                    index=False,
                    index_label=self._primary_key,
                    method="multi")

        except (Exception, sqlite3.OperationalError) as e:
            print(e)

        finally:
            conn.close()

    def _proceed_search(self, query="") -> list:
        _query = "SELECT * FROM {} {};".format(self._table_name, query)
        search_result = []
        try:
            with sqlite3.connect(self._db_name) as conn:
                c = conn.cursor()
                c.execute(_query)
                search_result = c.fetchall()

        except (Exception, sqlite3.OperationalError) as e:
            print(e)

        finally:
            c.close()
            conn.close()

        return search_result

    def _get_all(self):
        return self._proceed_search()

    def _oldest(self, number_of_entries=1) -> list:
        query = "ORDER BY {} ASC LIMIT {}".format(
            self._order_key, str(number_of_entries))

        return self._proceed_search(query)

    def _newest(self, number_of_entries=1) -> list:
        query = "ORDER BY {} DESC LIMIT {}".format(
            self._order_key, str(number_of_entries))

        return self._proceed_search(query)

    def _where(self, clause: str, number_of_entries=1) -> list:
        query = "WHERE {} LIMIT {}".format(
            clause, str(number_of_entries))

        return self._proceed_search(query)


class StorageKlines(SQLite3):
    _attributes = (
        "Open_time INTEGER primary key",
        "Open REAL, High REAL",
        "Low REAL",
        "Close REAL",
        "Volume REAL",
    )

    def __init__(self, table_name: str):
        self.attributes = "({})".format(", ".join(self._attributes))
        super(StorageKlines, self).__init__(
            db_name="klines.db", table_name=table_name, primary_key="Open_time"
        )


class Storage(SQLite3):
    def __init__(self, db_name: str, table_name: str, primary_key: str):
        super(Storage, self).__init__(
            db_name=db_name,
            table_name=table_name,
            primary_key=primary_key)
