import os
from json import loads, dumps
from DataModels import ConnectorParams
from sys import stdin, stdout, stderr, exit


class SubProcessInputOutputHandler(object):
    @property
    def connector_params(self):
        result = ConnectorParams()
        try:
            stdin_dict = loads(stdin.readline())
            result.source_folder_path = stdin_dict["source_folder_path"]
            result.iteration_entities_count = stdin_dict["iteration_entities_count"]
            result.api_key = os.getenv(stdin_dict["api_key"])
            return result
        except Exception as error_message:
            self.error(error_message)

    @staticmethod
    def end(connector_result):
        """ connector_result is of type ConnectorResult"""
        stdout.write(dumps(connector_result.alerts))
        exit(0)

    @staticmethod
    def error(exception):
        stderr.write(dumps({"Error": exception}))
        exit(1)
