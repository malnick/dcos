@asyncio.coroutine
def uninstall_dcos(config, block=False, state_json_dir=None, async_delegate=None, options=None):
    all_targets = config['master_list'] + config['agent_list']

    # clean the file to all targets
    runner = get_async_runner(config, all_targets, async_delegate=async_delegate)
    uninstall_chain = ssh.utils.CommandChain('uninstall')

    uninstall_chain.add_execute([
        'sudo',
        '-i',
        '/opt/mesosphere/bin/pkgpanda',
        'uninstall',
        '&&',
        'sudo',
        'rm',
        '-rf',
        '/opt/mesosphere/'], comment='Uninstalling DC/OS')
    result = yield from runner.run_commands_chain_async([uninstall_chain], block=block, state_json_dir=state_json_dir)

    return result


