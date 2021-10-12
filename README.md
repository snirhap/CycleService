# CycleService

CycleService is a framework that runs 3rd parties security services as scheduled tasks.

CycleService.py is the main script that should be running via:
```
$ python CycleService.py
```

It opens all connectors configuration file (config.json) and in parallel, runs each relevant script file (if it exists), then writes the results to an output folder according to each connector's output folder in config.json.

Source files are JSON files that contain a list of domains to query within its relevant connector/3rd party security provider.

There are example source files, including negative cases where, for example, domains are illegal or there are no domains to process for a source file.

CycleService uses a logger class which can be defined to write all outputs to the stdout or to a file by using a flag "to_file" when initiating the logger.

To setup the api keys for the connector, use environment variables (See expected values in config.json), for example:
```
$ export VIRUS_TOTAL_API_KEY_1='123'
```
