@asyncio.coroutine
def run_postflight(config, dcos_diag=None, block=False, state_json_dir=None, async_delegate=None, retry=False,
                   options=None):
    targets = []
    for host in config['master_list']:
        s = Node(host, {'role': 'master'})
        targets += [s]

    for host in config['agent_list']:
        s = Node(host, {'role': 'agent'})
        targets += [s]

    pf = get_async_runner(config, targets, async_delegate=async_delegate)
    postflight_chain = ssh.utils.CommandChain('postflight')
    add_pre_action(postflight_chain, pf.ssh_user)

    if dcos_diag is None:
        dcos_diag = """
#!/usr/bin/env bash
# Run the DC/OS diagnostic script for up to 15 minutes (900 seconds) to ensure
# we do not return ERROR on a cluster that hasn't fully achieved quorum.
T=900
until OUT=$(/opt/mesosphere/bin/./3dt -diag) || [[ T -eq 0 ]]; do
    sleep 1
    let T=T-1
done
RETCODE=$?
for value in $OUT; do
    echo $value
done
exit $RETCODE"""

    postflight_chain.add_execute([dcos_diag], comment='Executing local post-flight check for DC/OS servces...')
    add_post_action(postflight_chain)

    # Setup the cleanup chain
    cleanup_chain = ssh.utils.CommandChain('postflight_cleanup')
    add_post_action(cleanup_chain)

    master_agent_count = {
        'total_masters': len(config['master_list']),
        'total_agents': len(config['agent_list'])
    }

    result = yield from pf.run_commands_chain_async([postflight_chain, cleanup_chain], block=block,
                                                    state_json_dir=state_json_dir,
                                                    delegate_extra_params=master_agent_count)
    return result


