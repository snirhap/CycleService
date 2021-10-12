#!/usr/bin/env python
from json import load
from requests import get
from os.path import exists
from os import listdir, rename
from DataModels import ConnectorResult
from SubProcessInputOutputHandler import SubProcessInputOutputHandler

SUSPICIOUS_STATUSES = ["malicious", "suspicious"]
JSON_EXTENSION = '.json'
DONE_EXTENSION = '.done'
VIRUS_TOTAL_DOMAINS_API_URL = 'https://www.virustotal.com/api/v3/domains/'


def main():
    io_mgr = SubProcessInputOutputHandler()
    connector_params = io_mgr.connector_params
    connector_result = ConnectorResult()
    connector_result.alerts = dict()
    error_message = ''

    if not exists(connector_params.source_folder_path):
        io_mgr.error(f'Source folder {connector_params.source_folder_path} does not exist')

    files_to_process = [file_name for file_name in listdir(connector_params.source_folder_path)
                        if DONE_EXTENSION not in file_name and JSON_EXTENSION in file_name]
    if files_to_process:
        file_to_process = files_to_process.pop()
        try:
            with open(f'{connector_params.source_folder_path}/{file_to_process}') as f:
                data = load(f)
            if isinstance(data["domains"], list) and data["domains"]:
                for domain in data["domains"][:connector_params.iteration_entities_count]:
                    response = get(f'{VIRUS_TOTAL_DOMAINS_API_URL}{domain}', headers={"x-apikey": connector_params.api_key})
                    if response.ok:
                        response_attributes = response.json().get("data").get("attributes")
                        if response_attributes.get("reputation") >= 0:
                            connector_result.alerts[domain] = {"result": "Not Suspicious"}
                        else:
                            connector_result.alerts[domain] = {"status": "Suspicious",
                                                               "reputation": response_attributes.get("reputation"),
                                                               "reason": ','.join([f'{value} security vendors flagged this domain as {status}'
                                                                                   for status, value in response_attributes.get('last_analysis_stats').items()
                                                                                   if status in SUSPICIOUS_STATUSES and value > 0])}
                    else:
                        error_message += f'{domain} got the following error: {response.json()["error"]["message"]}\n'
            else:
                error_message = f'Error in {file_to_process}. Expected domains to contain a list, but got different type or list of domains is empty.'
        except KeyError as missing_key:
            error_message = f'{missing_key} key is missing in source file: {file_to_process}'
        except Exception as error:
            error_message = error
        finally:
            rename(f'{connector_params.source_folder_path}/{file_to_process}',
                   f'{connector_params.source_folder_path}/{file_to_process}{DONE_EXTENSION}')
    else:
        error_message = 'There are no files left to process'

    if connector_result.alerts:
        io_mgr.end(connector_result)
    else:
        io_mgr.error(error_message)


if __name__ == "__main__":
    main()
