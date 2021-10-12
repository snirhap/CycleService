from Logger import Logger
from inspect import ismethod
from datetime import datetime
from os import makedirs, listdir
from subprocess import Popen, PIPE
from DataModels import ConnectorSettings
from json import load, loads, dumps, dump
from os.path import abspath, dirname, exists, join, getctime


CONFIG_FILE_NAME = 'config.json'
RESOURCES_FOLDER = 'resources'
OUTPUT_FOLDER = "outputs"
DATE_FORMAT = "%Y%m%d-%H%M%S"
OUTPUT_FILE_EXTENSION = '.json'


def get_file_path(folder_name: str, file_name: str = None) -> str:
    return join(dirname(abspath(__file__)), f'{folder_name}{"/" + file_name if file_name else ""}')


def get_class_attributes(instance_object: object) -> dict:
    attributes = dict()
    for name in dir(instance_object):
        value = getattr(instance_object, name)
        if not name.startswith('__') and not ismethod(value):
            attributes[name] = type(value)
    return attributes


def create_connector_definition(connector_dict: dict, logger: Logger) -> ConnectorSettings:
    connector_settings = ConnectorSettings()
    connector_settings_attributes = get_class_attributes(connector_settings)
    connector_settings_params_attributes = get_class_attributes(connector_settings.params)

    try:
        # Accommodate ConnectorSettings parameters using input parameters from config file
        # Validate that each parameter type in config file matches its equivalent in ConnectorSettings
        for attribute in connector_settings_attributes.keys():
            if isinstance(connector_dict[attribute], dict):
                for params_key in connector_settings_params_attributes.keys():
                    if isinstance(connector_dict[attribute][params_key], connector_settings_params_attributes.get(params_key)):
                        setattr(connector_settings.params, params_key, connector_dict[attribute][params_key])
                    else:
                        raise TypeError(f"{attribute}.{params_key} - Expected type: {connector_settings_params_attributes.get(params_key)}, "
                                        f"but instead got type: {type(connector_dict[attribute][params_key])}")
            else:
                if isinstance(connector_dict[attribute], connector_settings_attributes.get(attribute)):
                    setattr(connector_settings, attribute, connector_dict[attribute])
                else:
                    raise TypeError(f"{attribute} - Expected type: {connector_settings_attributes.get(attribute)}, "
                                    f"but instead got type: {type(connector_dict[attribute])}")
    except TypeError as error:
        logger.error(error)
        raise
    except KeyError as key:
        connector_name = connector_dict.get("connector_name")
        raise KeyError(f'Missing key {key} in {f"{connector_name} configuration" if connector_name else "one of the configurations"}')

    return connector_settings


def write_results_to_output_folder(connector_output_path: str, file_content: dict, logger: Logger) -> None:
    output_file_path = get_file_path(connector_output_path, datetime.now().strftime(DATE_FORMAT))
    if not is_folder_exists(connector_output_path):
        logger.info(f'Creating dir: {connector_output_path}')
        makedirs(connector_output_path)
    with open(f'{output_file_path}.json', 'w') as write_file:
        dump(file_content, write_file, indent=2)


def is_folder_exists(folder_path: str) -> bool:
    return exists(get_file_path(folder_path))


def is_folder_empty(folder_path: str) -> bool:
    return len(listdir(get_file_path(folder_path))) == 0


def get_latest_output_file_created(folder_path: str, logger: Logger) -> datetime:
    full_folder_path = get_file_path(folder_path)
    if not is_folder_exists(folder_path):
        logger.info(f'Creating dir: {full_folder_path}')
        makedirs(full_folder_path)
    files = listdir(full_folder_path)
    paths = [join(full_folder_path, basename) for basename in files]
    latest_file = max(paths, key=getctime).split('/')[-1].strip(OUTPUT_FILE_EXTENSION)
    return datetime.strptime(latest_file, DATE_FORMAT)


def main():
    logger = Logger().get_logger()
    # Open global configs file
    input_file = get_file_path(RESOURCES_FOLDER, CONFIG_FILE_NAME)
    with open(input_file) as f:
        input_data = load(f)

    # Parse each record as a ConnectorSettings and append to a list
    connectors_settings = [create_connector_definition(connector, logger) for connector in input_data]

    while True:
        sub_processes = list()
        for connector_setting in connectors_settings:
            # Check if another iteration should be invoked (if interval time since last run has passed or if there are not outputs for this connector)
            latest_file_created_datetime = get_latest_output_file_created(connector_setting.output_folder_path, logger) \
                if is_folder_exists(connector_setting.output_folder_path) and not is_folder_empty(connector_setting.output_folder_path) else None
            if latest_file_created_datetime is None or (datetime.now() - latest_file_created_datetime).total_seconds() > \
                    connector_setting.run_interval_seconds:
                # Run connector as subprocess
                logger.info(f'Running a new job for {connector_setting.connector_name}')
                if exists(get_file_path(connector_setting.script_file_path)):
                    sub_process_object = Popen(['python', get_file_path(connector_setting.script_file_path)], stdout=PIPE, stderr=PIPE, stdin=PIPE,
                                               encoding='utf8')
                    sub_process_object.stdin.write(f'{dumps(vars(connector_setting.params))}\n')  # vars creates a dictionary out of class attributes
                    sub_process_object.stdin.flush()
                    sub_processes.append({connector_setting: sub_process_object})
                else:
                    raise FileNotFoundError(f'Script file {get_file_path(connector_setting.script_file_path)} defined for {connector_setting.connector_name} '
                                            f'does not exist.')
        while sub_processes:
            for sub_process in sub_processes:
                for connector_setting, sub_process_details in sub_process.items():
                    if sub_process_details.poll() is not None:
                        # Subprocess has finished
                        std_out, std_err = sub_process_details.communicate()
                        if len(std_err):
                            logger.error(f'Error in {connector_setting.connector_name}: {std_err}')
                            write_results_to_output_folder(connector_setting.output_folder_path, loads(std_err), logger)
                        else:
                            logger.info(f'{connector_setting.connector_name} job has finished successfully. Result: {std_out}')
                            write_results_to_output_folder(connector_setting.output_folder_path, loads(std_out), logger)
                        sub_processes.remove(sub_process)


if __name__ == "__main__":
    main()
