import argparse
import json
import logging
import os
import sys
import yaml

from dcos_genconf import configure

log = logging.getLogger(__name__)


def get_config_yaml(path):
    if os.path.isfile(path):
        log.debug("Loading YAML configuration: %s", path)
        with open(path, 'r') as data:
            configuration = yaml.load(data)

    else:
        log.error("Configuration file not found: %s", path)
        return {}

    return configuration


def stringify_configuration(config):
    """Create a stringified version of the complete installer configuration
    to send to gen.generate()"""
    gen_config = {}
    for key, value in config.items():
        if isinstance(value, list):
            log.debug("Caught list for genconf configuration, transforming to JSON string: %s", value)
            value = json.dumps(value)

        elif isinstance(value, bool):
            if value:
                value = 'true'
            else:
                value = 'false'

        elif isinstance(value, int):
            log.debug("Caught int for genconf configuration, transforming to string: %s", value)
            value = str(value)

        gen_config[key] = value

    log.debug('Stringified configuration: \n{}'.format(gen_config))
    return gen_config


def do_genconf(args, config):
    configure.do_configure(
        config,
        work_dir=args.work_dir)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config-path',
        default='./config.yaml',
        type=str,
        help='Path to config.yaml')

    parser.add_argument(
        '--work-dir',
        default='./dcos_genconf_artifacts',
        type=str,
        help='The working directory to dump complete configuration.')

    args = parser.parse_args(sys.argv[1:])
    return args


def main():
    args = parse_args()
    config = get_config_yaml(args.config_path)
    gen_config = stringify_configuration(config)
    do_genconf(args, gen_config)


if __name__ == '__main__':
    main()
