import sqlite3


def perform_sql_to_sqlite(db_name, query) -> bool:
    try:
        with sqlite3.connect(db_name) as conn:
            c = conn.cursor()
            c.execute(query)
        return True

    except (Exception, sqlite3.OperationalError) as e:
        print(e)  # TODO: to logging
        return False


class StorageRawKlines:
    def __init__(self, table_name: str):
        self.db_name = "raw_klines.db"
        self.table_name = table_name

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
            with sqlite3.connect(self.db_name) as conn:
                dataframe_to_append.to_sql(
                    name=self.table_name,
                    con=conn,
                    if_exists="append",
                    index=False,
                    index_label="Open_time",
                    method="multi",
                )

        except (Exception, sqlite3.OperationalError) as e:
            print(e)  # TODO: To logging

        finally:
            conn.close()

    def drop(self):
        query = "DROP TABLE IF EXISTS {};".format(self.table_name)
        perform_sql_to_sqlite(self.db_name, query)
