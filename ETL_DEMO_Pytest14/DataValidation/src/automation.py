import schedule
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import os
from config.db_config import create_connection
from src.validate import *
from src.advanced_validate import *

class ValidationRule:
    def __init__(self, name, rule_type, params):
        self.name = name
        self.rule_type = rule_type
        self.params = params

    def execute(self, connector):
        if self.rule_type == 'count_validation':
            return count_validation(connector, **self.params)
        elif self.rule_type == 'null_check':
            return null_check(connector, **self.params)
        elif self.rule_type == 'duplicate_check':
            return duplicate_check(connector, **self.params)
        elif self.rule_type == 'referential_integrity':
            return referential_integrity_check(connector, **self.params)
        elif self.rule_type == 'data_freshness':
            return data_freshness_check(connector, **self.params)
        # Add more
        return None

class ValidationEngine:
    def __init__(self, rules_config_path):
        with open(rules_config_path, 'r') as f:
            rules_data = json.load(f)
        self.rules = [ValidationRule(**rule) for rule in rules_data['rules']]
        self.connectors = {}
        for conn_name, conn_config in rules_data.get('connectors', {}).items():
            self.connectors[conn_name] = create_connection(conn_config)

    def run_validation(self, rule_name=None):
        results = {}
        if rule_name:
            rule = next((r for r in self.rules if r.name == rule_name), None)
            if rule:
                connector = self.connectors.get(rule.params.get('connector', 'default'))
                results[rule.name] = rule.execute(connector)
        else:
            with ThreadPoolExecutor() as executor:
                futures = {}
                for rule in self.rules:
                    connector = self.connectors.get(rule.params.get('connector', 'default'))
                    futures[executor.submit(rule.execute, connector)] = rule.name
                for future in futures:
                    results[futures[future]] = future.result()
        return results

class Scheduler:
    def __init__(self, validation_engine):
        self.validation_engine = validation_engine
        self.jobs = []

    def add_job(self, rule_name, schedule_time):
        job = schedule.every().day.at(schedule_time).do(self.validation_engine.run_validation, rule_name)
        self.jobs.append(job)

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

def start_scheduler(validation_engine, jobs_config):
    scheduler = Scheduler(validation_engine)
    for job in jobs_config:
        scheduler.add_job(job['rule'], job['time'])
    threading.Thread(target=scheduler.run, daemon=True).start()

# Example usage
if __name__ == "__main__":
    engine = ValidationEngine('config/validation_rules.json')
    results = engine.run_validation()
    print(results)