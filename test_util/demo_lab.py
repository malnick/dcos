#!/usr/bin/env python3
"""Integration test for SSH installer with CCM provided VPC

The following environment variables control test procedure:

INSTALLER_URL: URL that curl can grab the installer from (default=None)
    This option is only used if CCM_HOST_SETUP=true. See above.
"""
import logging
import os
import random
import stat
import string
import yaml
from contextlib import closing
from os.path import join

import pkg_resources
from retrying import retry

import test_util.ccm
import test_util.installer_api_test
from ssh.ssh_tunnel import SSHTunnel, TunnelCollection

LOGGING_FORMAT = '[%(asctime)s|%(name)s|%(levelname)s]: %(message)s'
logging.basicConfig(format=LOGGING_FORMAT, level=logging.DEBUG)
log = logging.getLogger(__name__)

DEFAULT_AWS_REGION = 'us-west-2'

REXRAY_CONFIG = """
rexray:
  loglevel: info
  storageDrivers:
    - ec2
  volume:
    unmount:
      ignoreusedcount: true
"""

assert 'INSTALLER_URL' in os.environ, 'INSTALLER_URL must be set!'
INSTALLER_URL = os.environ['INSTALLER_URL']


def pkg_filename(relative_path):
    return pkg_resources.resource_filename(__name__, relative_path)


def get_local_address(tunnel, remote_dir):
    """Uses checked-in IP detect script to report local IP mapping
    Args:
        tunnel (SSHTunnel): see ssh.ssh_tunnel.SSHTunnel
        remote_dir (str): path on hosts for ip-detect to be copied and run in

    Returns:
        dict[public_IP] = local_IP
    """
    ip_detect_script = pkg_resources.resource_filename('gen', 'ip-detect/aws.sh')
    tunnel.write_to_remote(ip_detect_script, join(remote_dir, 'ip-detect.sh'))
    local_ip = tunnel.remote_cmd(['bash', join(remote_dir, 'ip-detect.sh')]).decode('utf-8').strip('\n')
    assert len(local_ip.split('.')) == 4
    return local_ip


def main():
    # Get VPC
    random_identifier = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    unique_cluster_id = "training-{}".format(random_identifier)
    log.info("Spinning up AWS VPC via CCM with ID: {}".format(unique_cluster_id))
    ccm = test_util.ccm.Ccm()
    vpc = ccm.create_vpc(
        name=unique_cluster_id,
        time=60*24*3,
        instance_count=5,  # 1 bootstrap, 1 master, 2 agents, 1 public agent
        instance_type="m4.xlarge",
        instance_os="cent-os-7-dcos-prereqs",
        region=DEFAULT_AWS_REGION,
        key_pair_name=unique_cluster_id
        )
    host_list = vpc.hosts()

    # Get SSH key
    ssh_key, ssh_key_url = vpc.get_ssh_key()
    log.info("Download cluster SSH key: {}".format(ssh_key_url))
    ssh_key_path = unique_cluster_id + '.pkey'
    with open(ssh_key_path, "w") as ssh_key_fh:
        ssh_key_fh.write(ssh_key)
    os.chmod(ssh_key_path, stat.S_IREAD | stat.S_IWRITE)

    # Check that hosts are actually accessible
    ssh_user = 'centos'
    remote_dir = '/home/centos'
    host_list_w_port = [i+':22' for i in host_list]

    @retry(stop_max_delay=120000)
    def establish_host_connectivity():
        """Continually try to recreate the SSH Tunnels to all hosts for 2 minutes
        """
        return closing(TunnelCollection(ssh_user, ssh_key_path, host_list_w_port))

    log.info('Checking that hosts are accessible')
    with establish_host_connectivity() as tunnels:
        local_ip = {}
        for tunnel in tunnels.tunnels:
            local_ip[tunnel.host] = get_local_address(tunnel, remote_dir)
            # Make the default user priveleged to use docker
            tunnel.remote_cmd(['sudo', 'usermod', '-aG', 'docker', ssh_user])

    test_host = host_list[0]
    master_list = [local_ip[host_list[1]]]
    agent1 = local_ip[host_list[2]]
    agent2 = local_ip[host_list[3]]
    agent_list = [agent1, agent2]
    public_agent_list = [local_ip[host_list[4]]]
    log.info('Install host for {}: {}'.format(unique_cluster_id, test_host))

    with closing(SSHTunnel(ssh_user, ssh_key_path, test_host)) as test_host_tunnel:
        log.info('Setting up installer on test host')

        # Set up (download) the installer on test host
        installer = test_util.installer_api_test.DcosCliInstaller()
        installer.setup_remote(
                tunnel=test_host_tunnel,
                installer_path=remote_dir+'/dcos_generate_config.ee.sh',
                download_url=INSTALLER_URL)

        with open(pkg_resources.resource_filename("gen", "ip-detect/aws.sh")) as ip_detect_fh:
            ip_detect_script = ip_detect_fh.read()

        password_hash = '$6$rounds=656000$WZdTPdpxUZsDG5PG$6om6ApIm5l5639JNAUmtFD87cIXdWCAVKeJ4zNlhmPKWT3PARF6Ai.HpcjR8SPQSQnqoefBiLaZmPuMFhGhpm0'  # noqa
        add_config = {
                'customer_key': '123456-78901-234567-89012345-6789012',
                'superuser_username': 'trainee',
                'superuser_password_hash': password_hash}
        add_config_path = 'add_config.yaml'
        with open(add_config_path, 'w') as fh:
            yaml.dump(add_config, fh)
        log.info("Running genconf...")
        installer.genconf(
                zk_host=None,
                master_list=master_list,
                agent_list=agent_list,
                public_agent_list=public_agent_list,
                ip_detect_script=ip_detect_script,
                ssh_user=ssh_user,
                ssh_key=ssh_key,
                add_config_path=add_config_path,
                rexray_config=REXRAY_CONFIG)

        print("==>")
        print("VPC Deployed: {}".format(unique_cluster_id))
        print("Intaller Host: {}".format(test_host))
        print("Master(s): {}".format(master_list))
        print("Agent(s): {}".format(agent_list))
        print("SSH Key URL: {}".format(ssh_key_url))
        print("<==")

if __name__ == "__main__":
    main()
