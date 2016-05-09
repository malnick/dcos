import json
import logging
import os

import pkgpanda

from .utils import REMOTE_TEMP_DIR, CLUSTER_PACKAGES_FILE, get_async_runner, add_post_action, add_pre_action

log = logging.getLogger(__name__)


class ExecuteException(Exception):
    """Raised when execution fails"""


def _add_copy_dcos_install(chain, local_install_path='/genconf/serve'):
    dcos_install_script = 'dcos_install.sh'
    local_install_path = os.path.join(local_install_path, dcos_install_script)
    remote_install_path = os.path.join(REMOTE_TEMP_DIR, dcos_install_script)
    chain.add_copy(local_install_path, remote_install_path, comment='COPYING dcos_install.sh TO TARGETS')


def _add_copy_packages(chain, local_pkg_base_path='/genconf/serve'):
    if not os.path.isfile(CLUSTER_PACKAGES_FILE):
        err_msg = '{} not found'.format(CLUSTER_PACKAGES_FILE)
        log.error(err_msg)
        raise ExecuteException(err_msg)

    cluster_packages = pkgpanda.load_json(CLUSTER_PACKAGES_FILE)
    for package, params in cluster_packages.items():
        destination_package_dir = os.path.join(REMOTE_TEMP_DIR, 'packages', package)
        local_pkg_path = os.path.join(local_pkg_base_path, params['filename'])

        chain.add_execute(['mkdir', '-p', destination_package_dir], comment='CREATING PKG DIR')
        chain.add_copy(local_pkg_path, destination_package_dir,
                       comment='COPYING PACKAGES TO TARGETS {}'.format(local_pkg_path))


def _add_copy_bootstap(chain, local_bs_path):
    remote_bs_path = REMOTE_TEMP_DIR + '/bootstrap'
    chain.add_execute(['mkdir', '-p', remote_bs_path], comment='CREATE DIR {}'.format(remote_bs_path))
    chain.add_copy(local_bs_path, remote_bs_path,
                   comment='COPYING BOOTSTRAP TO TARGETS (large file, can take up to 5min to transfer...)')


def _get_bootstrap_tarball(tarball_base_dir='/genconf/serve/bootstrap'):
    '''
    Get a bootstrap tarball from a local filesystem
    :return: String, location of a tarball
    '''
    if 'BOOTSTRAP_ID' not in os.environ:
        err_msg = 'BOOTSTRAP_ID must be set'
        log.error(err_msg)
        raise ExecuteException(err_msg)

    tarball = os.path.join(tarball_base_dir, '{}.bootstrap.tar.xz'.format(os.environ['BOOTSTRAP_ID']))
    if not os.path.isfile(tarball):
        log.error('Ensure environment variable BOOTSTRAP_ID is set correctly')
        log.error('Ensure that the bootstrap tarball exists in '
                  '/genconf/serve/bootstrap/[BOOTSTRAP_ID].bootstrap.tar.xz')
        log.error('You must run genconf.py before attempting Deploy.')
        raise ExecuteException('bootstrap tarball not found /genconf/serve/bootstrap')
    return tarball


def _read_state_file(state_file):
    if not os.path.isfile(state_file):
        return {}

    with open(state_file) as fh:
        return json.load(fh)


def _remove_host(state_file, host):

    json_state = _read_state_file(state_file)

    if 'hosts' not in json_state or host not in json_state['hosts']:
        return False

    log.debug('removing host {} from {}'.format(host, state_file))
    try:
        del json_state['hosts'][host]
    except KeyError:
        return False

    with open(state_file, 'w') as fh:
        json.dump(json_state, fh)

    return True
