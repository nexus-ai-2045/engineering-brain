import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from engineering_brain.orchestration_bridge import bind_lifecycle
from engineering_brain.cli import main


OWNER = Path(os.environ.get('ENGINEERING_LIFECYCLE_OWNER', '.')) / 'shared/skills/pr-lifecycle-orchestrator/scripts/autopilot_state.py'


def git(repo, *args):
    return subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def workspace(tmp_path):
    if not OWNER.is_file():
        pytest.skip('Set ENGINEERING_LIFECYCLE_OWNER for the external owner contract test')
    owner = tmp_path / 'owner'
    owner.mkdir()
    git(owner, 'init', '-b', 'main')
    git(owner, 'remote', 'add', 'origin', 'https://github.com/fixture/Projects.git')
    script = owner / 'shared/skills/pr-lifecycle-orchestrator/scripts/autopilot_state.py'
    script.parent.mkdir(parents=True)
    shutil.copyfile(OWNER, script)
    git(owner, 'add', '.')
    git(owner, 'commit', '-m', 'Create owner fixture')
    target = tmp_path / 'target'
    target.mkdir()
    git(target, 'init', '-b', 'main')
    git(target, 'remote', 'add', 'origin', 'https://github.com/example/target.git')
    (target / 'file.txt').write_text('base')
    git(target, 'add', '.')
    git(target, 'commit', '-m', 'Create target fixture')
    return owner, target, tmp_path / 'state.json'


def test_real_owner_state_is_initialized_and_local_gates_remain_required(workspace):
    owner, target, output = workspace
    result = bind_lifecycle(target, 'repair workflow', 'run-1', output, owner)
    state = json.loads(output.read_text())
    assert state['head_sha'] == git(target, 'rev-parse', 'HEAD')
    assert state['repository'] == 'example/target'
    assert state['approvals'] == []
    assert state['evidence'] == {}
    assert result['evaluation']['state'] == 'SECURITY_CLASSIFICATION_REQUIRED'
    assert result['external_actions_performed'] is False


def test_resume_preserves_evidence_and_does_not_overwrite_approval(workspace):
    owner, target, output = workspace
    bind_lifecycle(target, 'repair workflow', 'run-1', output, owner)
    state = json.loads(output.read_text())
    state['evidence']['design_complete'] = {'status': 'pass', 'source': 'design receipt'}
    output.write_text(json.dumps(state))
    before = output.read_bytes()
    result = bind_lifecycle(target, 'repair workflow', 'run-1', output, owner)
    assert output.read_bytes() == before
    assert result['resumed'] is True


def test_changed_head_cannot_resume_old_state(workspace):
    owner, target, output = workspace
    bind_lifecycle(target, 'repair workflow', 'run-1', output, owner)
    before = output.read_bytes()
    (target / 'file.txt').write_text('changed')
    git(target, 'commit', '-am', 'Change target')
    with pytest.raises(ValueError, match='binding'):
        bind_lifecycle(target, 'repair workflow', 'run-1', output, owner)
    assert output.read_bytes() == before


def test_uncommitted_owner_script_is_not_executed(workspace):
    owner, target, output = workspace
    script = owner / 'shared/skills/pr-lifecycle-orchestrator/scripts/autopilot_state.py'
    script.write_text('raise RuntimeError("untrusted")')
    with pytest.raises(ValueError, match='owner script'):
        bind_lifecycle(target, 'repair workflow', 'run-1', output, owner)
    assert not output.exists()


def test_output_must_not_replace_tracked_source(workspace):
    owner, target, _ = workspace
    with pytest.raises(ValueError):
        bind_lifecycle(target, 'repair workflow', 'run-1', target / 'file.txt', owner)
    assert (target / 'file.txt').read_text() == 'base'


def test_missing_run_identity_fails_without_dispatch(tmp_path):
    with pytest.raises(ValueError, match='run_id'):
        bind_lifecycle(tmp_path, 'repair', '', tmp_path / 'state.json', tmp_path)


def test_unknown_owner_is_rejected_before_script_execution(tmp_path):
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'remote', 'add', 'origin', 'https://github.com/example/unknown.git')
    with pytest.raises(ValueError, match='registered Projects'):
        bind_lifecycle(tmp_path, 'repair', 'run-1', tmp_path / 'state.json', tmp_path)
    assert not (tmp_path / 'state.json').exists()


def test_credential_remote_is_not_accepted_or_printed(tmp_path):
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'remote', 'add', 'origin', 'https://fixture:fake-token@github.com/example/target.git')
    with pytest.raises(ValueError, match='credential-free'):
        bind_lifecycle(tmp_path, 'repair', 'run-1', tmp_path / 'state.json', tmp_path)


def test_cli_invokes_existing_owner_and_emits_bound_state(workspace, capfd):
    owner, target, output = workspace
    assert main(['run', '--task', 'repair', '--repo', str(target), '--orchestrator-root', str(owner), '--run-id', 'run-1', '--lifecycle-state', str(output), '--json']) == 0
    payload = json.loads(capfd.readouterr().out)
    assert payload['status'] == 'ready_for_local_work'
    assert payload['lifecycle']['binding']['head_sha'] == git(target, 'rev-parse', 'HEAD')
    assert payload['lifecycle']['external_actions_performed'] is False


def test_partial_bridge_arguments_fail_before_state_creation(tmp_path):
    with pytest.raises(SystemExit) as failure:
        main(['run', '--task', 'repair', '--lifecycle-state', str(tmp_path / 'state.json')])
    assert failure.value.code == 2
    assert not (tmp_path / 'state.json').exists()
