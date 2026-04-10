import pytest
import pandas as pd

@pytest.fixture
def sample_dataframe():
    data = {
        "id": [1, 2, 3],
        "name": ["A", "B", "C"],
        "salary": [1000, 2000, 3000]
    }
    return pd.DataFrame(data)
