from src.transform import transform_data


def test_transform_data():

    columns = ["id", "name", "salary"]
    data = [
        (1, "A", 1000),
        (2, "B", 2000)
    ]

    transformed_data = transform_data(columns, data)

    assert transformed_data is not None
    assert len(transformed_data) == 2
