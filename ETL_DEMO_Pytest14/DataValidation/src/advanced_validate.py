import os
import hashlib
import re
from datetime import datetime, timedelta
from config.db_config import create_connection

def referential_integrity_check(cursor, parent_table, child_table, foreign_key):
    """
    Check referential integrity between parent and child tables.
    """
    query = f"""
    SELECT COUNT(*) FROM {child_table} c
    LEFT JOIN {parent_table} p ON c.{foreign_key} = p.{foreign_key}
    WHERE p.{foreign_key} IS NULL
    """
    cursor.execute(query)
    orphaned_count = cursor.fetchone()[0]
    return orphaned_count == 0, orphaned_count

def data_masking(data, columns_to_mask):
    """
    Mask sensitive data in specified columns.
    """
    masked_data = []
    for row in data:
        masked_row = list(row)
        for col in columns_to_mask:
            if col < len(masked_row):
                masked_row[col] = mask_value(str(masked_row[col]))
        masked_data.append(masked_row)
    return masked_data

def mask_value(value):
    """
    Simple masking: replace with hash or asterisks.
    """
    if len(value) > 4:
        return value[:2] + '*' * (len(value) - 4) + value[-2:]
    return '*' * len(value)

def data_freshness_check(cursor, table, timestamp_column, sla_hours=24):
    """
    Check if data is fresh within SLA.
    """
    query = f"SELECT MAX({timestamp_column}) FROM {table}"
    cursor.execute(query)
    latest_timestamp = cursor.fetchone()[0]
    if latest_timestamp:
        now = datetime.now()
        if isinstance(latest_timestamp, str):
            latest_timestamp = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
        freshness = now - latest_timestamp
        is_fresh = freshness < timedelta(hours=sla_hours)
        return is_fresh, freshness.total_seconds() / 3600
    return False, None

def incremental_refresh_validation(cursor, table, partition_column, expected_partitions):
    """
    Validate incremental refresh partitions.
    """
    query = f"SELECT DISTINCT {partition_column} FROM {table} ORDER BY {partition_column}"
    cursor.execute(query)
    actual_partitions = [row[0] for row in cursor.fetchall()]
    missing = set(expected_partitions) - set(actual_partitions)
    extra = set(actual_partitions) - set(expected_partitions)
    return len(missing) == 0 and len(extra) == 0, missing, extra

def anomaly_detection(data, column_index, method='zscore', threshold=3):
    """
    Detect anomalies in data using z-score or IQR.
    """
    values = [float(row[column_index]) for row in data if row[column_index] is not None]
    if not values:
        return [], []
    mean = sum(values) / len(values)
    std = (sum((x - mean)**2 for x in values) / len(values))**0.5
    anomalies = []
    for i, row in enumerate(data):
        if row[column_index] is not None:
            z = (float(row[column_index]) - mean) / std if std > 0 else 0
            if abs(z) > threshold:
                anomalies.append((i, row[column_index], z))
    return anomalies

def cross_system_comparison(source_data, target_data, key_columns):
    """
    Compare data between two systems.
    """
    source_dict = {tuple(row[i] for i in key_columns): row for row in source_data}
    target_dict = {tuple(row[i] for i in key_columns): row for row in target_data}
    mismatches = []
    for key, source_row in source_dict.items():
        if key in target_dict:
            target_row = target_dict[key]
            if source_row != target_row:
                mismatches.append((key, source_row, target_row))
        else:
            mismatches.append((key, source_row, None))
    for key, target_row in target_dict.items():
        if key not in source_dict:
            mismatches.append((key, None, target_row))
    return mismatches

# BI Validations
def validate_dax_measures(powerbi_connector, dataset_id, measures):
    """
    Validate DAX measures in Power BI dataset.
    """
    failures = []
    for measure in measures:
        query = f"EVALUATE {measure}"
        result = powerbi_connector.execute_dax_query(dataset_id, query)
        if not result or 'error' in result:
            failures.append(measure)
    return failures

def validate_visual_consistency(powerbi_connector, report_id, visuals):
    """
    Validate visual filters and consistency.
    """
    # This would require more complex API calls
    # For now, placeholder
    return []

def dataset_vs_report_validation(powerbi_connector, dataset_id, report_id):
    """
    Validate dataset and report consistency.
    """
    # Check if report uses the dataset
    reports = powerbi_connector.get_reports()
    if reports:
        for report in reports.get('value', []):
            if report['id'] == report_id:
                dataset_id_in_report = report.get('datasetId')
                return dataset_id_in_report == dataset_id
    return False

def validate_powerbi_measures(powerbi_connector, dataset_id, expected_measures):
    """
    Validate that expected measures exist and are valid in Power BI dataset.
    """
    measures = powerbi_connector.get_dataset_measures(dataset_id)
    if not measures:
        return False, []
    existing_measures = [m['name'] for m in measures.get('value', [])]
    missing = set(expected_measures) - set(existing_measures)
    return len(missing) == 0, list(missing)

def validate_powerbi_visuals(powerbi_connector, report_id, expected_visuals):
    """
    Validate visuals on report pages.
    """
    pages = powerbi_connector.get_report_pages(report_id)
    if not pages:
        return False, []
    all_visuals = []
    for page in pages.get('value', []):
        page_name = page['name']
        visuals = powerbi_connector.get_visuals_on_page(report_id, page_name)
        all_visuals.extend([v.get('title', '') for v in visuals])
    missing = set(expected_visuals) - set(all_visuals)
    return len(missing) == 0, list(missing)

def validate_rls(powerbi_connector, dataset_id):
    """
    Validate Row-Level Security settings.
    """
    # This would require more complex API calls
    # Placeholder
    return True, "RLS validation not implemented"

def validate_dataset_ownership(powerbi_connector, dataset_id, expected_owner):
    """
    Validate dataset ownership.
    """
    datasets = powerbi_connector.get_datasets()
    if datasets:
        for ds in datasets.get('value', []):
            if ds['id'] == dataset_id:
                owner = ds.get('owner', '')
                return owner == expected_owner, owner
    return False, None