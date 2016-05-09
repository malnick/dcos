@asyncio.coroutine
def run_preflight(config, pf_script_path='/genconf/serve/dcos_install.sh', block=False, state_json_dir=None,
                  async_delegate=None, retry=False, options=None):
    '''
    Copies preflight.sh to target hosts and executes the script. Gathers
    stdout, sterr and return codes and logs them to disk via SSH library.
    :param config: Dict, loaded config file from /genconf/config.yaml
    :param pf_script_path: preflight.sh script location on a local host
    :param preflight_remote_path: destination location
    '''
    if not os.path.isfile(pf_script_path):
        log.error("genconf/serve/dcos_install.sh does not exist. Please run --genconf before executing preflight.")
        raise FileNotFoundError('genconf/serve/dcos_install.sh does not exist')
    targets = []
    for host in config['master_list']:
        s = Node(host, {'role': 'master'})
        targets += [s]

    for host in config['agent_list']:
        s = Node(host, {'role': 'agent'})
        targets += [s]

    pf = get_async_runner(config, targets, async_delegate=async_delegate)
    chains = []

    preflight_chain = ssh.utils.CommandChain('preflight')
    # In web mode run if no --offline flag used.
    if options.web:
        if options.offline:
            log.debug('Offline mode used. Do not install prerequisites on CentOS7, RHEL7 in web mode')
        else:
            _add_prereqs_script(preflight_chain)

    add_pre_action(preflight_chain, pf.ssh_user)
    preflight_chain.add_copy(pf_script_path, REMOTE_TEMP_DIR, comment='COPYING PREFLIGHT SCRIPT TO TARGETS')

    preflight_chain.add_execute(
        'sudo bash {} --preflight-only master'.format(
            os.path.join(REMOTE_TEMP_DIR, os.path.basename(pf_script_path))).split(),
        comment='EXECUTING PREFLIGHT CHECK ON TARGETS')
    chains.append(preflight_chain)

    # Setup the cleanup chain
    cleanup_chain = ssh.utils.CommandChain('preflight_cleanup')
    add_post_action(cleanup_chain)

    chains.append(cleanup_chain)
    master_agent_count = {
        'total_masters': len(config['master_list']),
        'total_agents': len(config['agent_list'])
    }

    result = yield from pf.run_commands_chain_async(chains, block=block, state_json_dir=state_json_dir,
                                                    delegate_extra_params=master_agent_count)
    return result


