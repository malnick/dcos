def _add_prereqs_script(chain):
    inline_script = """
#/bin/sh
# setenforce is in this path
PATH=$PATH:/sbin

dist=$(cat /etc/*-release | sed -n 's@^ID="\(.*\)"$@\\1@p')

if ([ x$dist != 'xrhel' ] && [ x$dist != 'xcentos' ]); then
  echo "$dist is not supported. Only RHEL and CentOS are supported" >&2
  exit 0
fi

version=$(cat /etc/*-release | sed -n 's@^VERSION_ID="\(.*\)"$@\\1@p')
if [ $version -lt 7 ]; then
  echo "$version is not supported. Only >= 7 version is supported" >&2
  exit 0
fi

sudo setenforce 0 && \
sudo sed -i 's/^SELINUX=.*/SELINUX=disabled/g' /etc/sysconfig/selinux

sudo tee /etc/yum.repos.d/docker.repo <<-'EOF'
[dockerrepo]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/centos/$releasever/
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOF

sudo yum -y update

sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/override.conf <<- EOF
[Service]
ExecStart=
ExecStart=/usr/bin/docker daemon --storage-driver=overlay -H fd://
EOF

sudo yum install -y docker-engine
sudo systemctl start docker
sudo systemctl enable docker

sudo yum install -y wget
sudo yum install -y git
sudo yum install -y unzip
sudo yum install -y curl
sudo yum install -y xz
sudo yum install -y ipset

sudo getent group nogroup || sudo groupadd nogroup
"""
    # Run a first command to get json file generated.
    chain.add_execute(['echo', 'INSTALL', 'PREREQUISITES'])
    chain.add_execute([inline_script], comment='INSTALLING PREFLIGHT PREREQUISITES')


@asyncio.coroutine
def install_prereqs(config, block=False, state_json_dir=None, async_delegate=None, options=None):
    all_targets = config['master_list'] + config['agent_list']
    runner = get_async_runner(config, all_targets, async_delegate=async_delegate)
    prereqs_chain = ssh.utils.CommandChain('install_prereqs')
    _add_prereqs_script(prereqs_chain)
    result = yield from runner.run_commands_chain_async([prereqs_chain], block=block, state_json_dir=state_json_dir)
    return result
