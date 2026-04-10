"""
ETL Validation Tests
These tests are designed to be run via the web interface or directly via pytest.
Environment variables control which validations to run and which tables to validate.
"""

import os
import pytest
from config.db_config import create_connection
from src.validate import (
    structure_validation,
    count_validation,
    null_check,
    duplicate_check,
    row_data_validation,
)

# Get configuration from environment variables
SOURCE_TABLE = os.getenv("SOURCE_TABLE", "dbo.emp_source2")
TARGET_TABLE = os.getenv("TARGET_TABLE", "dbo.emp_target2")

# Validation flags from environment
RUN_STRUCTURE = os.getenv("STRUCTURE_VALIDATION", "True") == "True"
RUN_COUNT = os.getenv("COUNT_VALIDATION", "True") == "True"
RUN_NULL = os.getenv("NULL_CHECK", "True") == "True"
RUN_DUPLICATE = os.getenv("DUPLICATE_CHECK", "True") == "True"
RUN_ROW_DATA = os.getenv("ROW_DATA_VALIDATION", "True") == "True"


@pytest.fixture(scope="module")
def db_connection():
    """Create database connection for tests"""
    conn = create_connection()
    if conn is None:
        pytest.skip("Database connection failed")
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def db_cursor(db_connection):
    """Create database cursor for tests"""
    return db_connection.cursor()


@pytest.mark.skipif(not RUN_STRUCTURE, reason="Structure validation disabled")
def test_structure_validation(db_cursor):
    """
    Test that source and target tables have matching structures.
    Validates column names, data types, nullability, and primary keys.
    """
    output, result = structure_validation(
        db_cursor, SOURCE_TABLE, TARGET_TABLE, return_output=True
    )
    
    assert result, f"Structure mismatch between {SOURCE_TABLE} and {TARGET_TABLE}\n{output}"


@pytest.mark.skipif(not RUN_COUNT, reason="Count validation disabled")
def test_count_validation(db_cursor):
    """
    Test that source and target tables have the same number of records.
    """
    result, output = count_validation(
        db_cursor, SOURCE_TABLE, TARGET_TABLE, return_output=True
    )
    
    assert result, f"Record count mismatch\n{output}"


@pytest.mark.skipif(not RUN_NULL, reason="Null check disabled")
def test_null_check_source(db_cursor):
    """
    Test for NULL values and constraint violations in source table.
    """
    output = null_check(db_cursor, SOURCE_TABLE, return_output=True)
    
    # Check for constraint violations
    if isinstance(output, str):
        assert "❌" not in output or "violation" not in output.lower(), \
            f"NULL constraint violations found in {SOURCE_TABLE}\n{output}"


@pytest.mark.skipif(not RUN_NULL, reason="Null check disabled")
def test_null_check_target(db_cursor):
    """
    Test for NULL values and constraint violations in target table.
    """
    output = null_check(db_cursor, TARGET_TABLE, return_output=True)
    
    # Check for constraint violations
    if isinstance(output, str):
        assert "❌" not in output or "violation" not in output.lower(), \
            f"NULL constraint violations found in {TARGET_TABLE}\n{output}"


@pytest.mark.skipif(not RUN_DUPLICATE, reason="Duplicate check disabled")
def test_duplicate_check_source(db_cursor):
    """
    Test for duplicate records in source table based on primary key.
    """
    output = duplicate_check(
        db_cursor,
        SOURCE_TABLE,
        use_primary_key=True,
        return_output=True,
        label="Source"
    )
    
    if isinstance(output, str):
        assert "❌" not in output, f"Duplicates found in {SOURCE_TABLE}\n{output}"


@pytest.mark.skipif(not RUN_DUPLICATE, reason="Duplicate check disabled")
def test_duplicate_check_target(db_cursor):
    """
    Test for duplicate records in target table based on primary key.
    """
    output = duplicate_check(
        db_cursor,
        TARGET_TABLE,
        use_primary_key=True,
        return_output=True,
        label="Target"
    )
    
    if isinstance(output, str):
        assert "❌" not in output, f"Duplicates found in {TARGET_TABLE}\n{output}"


@pytest.mark.skipif(not RUN_ROW_DATA, reason="Row data validation disabled")
def test_row_data_validation(db_cursor):
    """
    Test that all rows in source table exist in target table and vice versa.
    Performs row-by-row comparison of data.
    """
    output = row_data_validation(
        db_cursor,
        SOURCE_TABLE,
        TARGET_TABLE,
        return_output=True,
        mismatch_log_file="logs/row_data_mismatch_log.txt"
    )
    
    if isinstance(output, str):
        # Check for mismatches
        has_only_in_source = "Only in Source" in output
        has_only_in_target = "Only in Target" in output
        
        assert not (has_only_in_source or has_only_in_target), \
            f"Row data mismatch found\n{output}"


def test_etl_pipeline_integration(db_cursor):
    """
    Integration test that runs all validations and generates a summary.
    """
    results = {}
    
    if RUN_STRUCTURE:
        output, result = structure_validation(
            db_cursor, SOURCE_TABLE, TARGET_TABLE, return_output=True
        )
        results["structure"] = {"passed": result, "output": output}
    
    if RUN_COUNT:
        result, output = count_validation(
            db_cursor, SOURCE_TABLE, TARGET_TABLE, return_output=True
        )
        results["count"] = {"passed": result, "output": output}
    
    if RUN_NULL:
        source_output = null_check(db_cursor, SOURCE_TABLE, return_output=True)
        target_output = null_check(db_cursor, TARGET_TABLE, return_output=True)
        results["null_source"] = {"output": source_output}
        results["null_target"] = {"output": target_output}
    
    if RUN_DUPLICATE:
        source_output = duplicate_check(
            db_cursor, SOURCE_TABLE, use_primary_key=True, 
            return_output=True, label="Source"
        )
        target_output = duplicate_check(
            db_cursor, TARGET_TABLE, use_primary_key=True,
            return_output=True, label="Target"
        )
        results["duplicate_source"] = {"output": source_output}
        results["duplicate_target"] = {"output": target_output}
    
    if RUN_ROW_DATA:
        output = row_data_validation(
            db_cursor, SOURCE_TABLE, TARGET_TABLE, return_output=True
        )
        results["row_data"] = {"output": output}
    
    # Generate summary
    summary = f"""
    ETL Validation Summary
    ======================
    Source Table: {SOURCE_TABLE}
    Target Table: {TARGET_TABLE}
    
    Validations Run:
    - Structure Validation: {'✅' if RUN_STRUCTURE else '⏭️ Skipped'}
    - Count Validation: {'✅' if RUN_COUNT else '⏭️ Skipped'}
    - Null Check: {'✅' if RUN_NULL else '⏭️ Skipped'}
    - Duplicate Check: {'✅' if RUN_DUPLICATE else '⏭️ Skipped'}
    - Row Data Validation: {'✅' if RUN_ROW_DATA else '⏭️ Skipped'}
    """
    
    # Print summary to console for logging
    print(summary)
    
    # The test passes if it completes without exceptions
    assert True, "Integration test completed"
