from main import run_etl

def test_etl_pipeline():
    result = run_etl()
    status, excel_path, html_path = run_etl()

    assert status is True
    assert excel_path.endswith(".xlsx")
    assert html_path.endswith(".html")


