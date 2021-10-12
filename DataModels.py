class ConnectorParams(object):
    source_folder_path: str = None  # string - file path for entity list files
    iteration_entities_count: int = None  # int - how many entities to process each interval (ignore the rest)
    api_key: str = None  # string - api key

    def __init__(self):
        self.source_folder_path = ''
        self.iteration_entities_count = 0
        self.api_key = ''


class ConnectorSettings(object):
    run_interval_seconds: int = None  # int - iterations interval in seconds for current connector
    script_file_path: str = None  # string - the file path to the connector script
    connector_name: str = None  # string - connector name
    params: ConnectorParams = None  # ConnectorParams object - see below
    output_folder_path: str = None  # string - file path for connector output

    def __init__(self):
        self.run_interval_seconds = 0
        self.script_file_path = ''
        self.connector_name = ''
        self.params = ConnectorParams()
        self.output_folder_path = ''


class ConnectorResult(object):
    alerts: dict = None  # Dictionary {string, any} - connector output with data per entity. Key = Entity, value = entity data

    def __init__(self):
        self.alerts = dict()
