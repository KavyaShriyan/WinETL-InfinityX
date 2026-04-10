from src.extract import extract_data


class DummyCursor:
    def execute(self, query):
        pass

    def fetchall(self):
        return [
            (1, "A", 1000),
            (2, "B", 2000)
        ]

    @property
    def description(self):
        return [
            ("id",),
            ("name",),
            ("salary",)
        ]


def test_extract_data():
    cursor = DummyCursor()
    table_name = "dummy_table"

    columns, data = extract_data(cursor, table_name)

    assert columns == ["id", "name", "salary"]
    assert len(data) == 2
