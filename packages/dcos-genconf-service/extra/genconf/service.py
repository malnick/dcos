import argparse
import sys
from . import configure


def get_config_yaml(path):
    pass


def do_genconf(args, config):
    configure.do_configure(
        config,
        bootstrap_path=args.bootstrap_tarball_path,
        active_json_path=args.active_json_path,
        work_dir=args.work_dir)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config-path',
        default='./config.yaml',
        type=str,
        help='Path to config.yaml')

    parser.add_argument(
        '--bootstrap-tarball-path',
        default=None,
        type=str,
        help='Path to the bootstrap tarball')

    parser.add_argument(
        '--active-json-path',
        default=None,
        type=str,
        help='Path to the active.json file')

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
    do_genconf(args, config)


if __name__ == '__main__':
    main()
