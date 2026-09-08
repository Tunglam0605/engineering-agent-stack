"""Exercise an installed CLI outside the source tree, without provider access."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True, help='canonical policy checkout')
    args = parser.parse_args()
    env = dict(os.environ, EAS_REPO=str(args.repo.resolve()))
    env.pop('PYTHONPATH', None)
    with tempfile.TemporaryDirectory(prefix='eas-installed-goal-') as tmp:
        project = Path(tmp)
        subprocess.run(['git', 'init', '-q', str(project)], check=True)

        def cli(*arguments):
            result = subprocess.run([sys.executable, '-m', 'eas_cli', 'goal', *arguments, '--json'],
                                    cwd=project, env=env, capture_output=True, text=True, encoding='utf-8')
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            return json.loads(result.stdout)

        # Assert imports really come from the installed environment.
        probe = subprocess.run([sys.executable, '-c',
                                'import runtime.workflow; print(runtime.workflow.__file__)'],
                               cwd=project, env=env, capture_output=True, text=True, check=True)
        module_path = Path(probe.stdout.strip()).resolve()
        if args.repo.resolve() in module_path.parents:
            raise RuntimeError('smoke imported source instead of installed package')
        init = cli('init', 'smoke')
        cli('gate', 'smoke', '--role', 'scout', '--domain', 'smoke', '--commit')
        cli('checkpoint', 'smoke', '--stage', 'verify', '--revision', '2',
            '--evidence', '{"tests":"installed-smoke"}')
        # Fixture-only timestamp change simulates an interruption, not executor evidence.
        state_path = Path(init['state_path'])
        state = json.loads(state_path.read_text(encoding='utf-8'))
        state['assignments'][0]['updated_at'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        state_path.write_text(json.dumps(state), encoding='utf-8')
        plan = cli('plan', 'smoke')
        assert plan['suspect'][0]['assignment_id'] == 'a-0001'
        approval = cli('approve', 'smoke', '--action', 'recover', '--target', 'a-0001',
                       '--revision', str(plan['revision']), '--approver', 'offline-smoke-operator',
                       '--reason', 'fixture reconciled', '--executor-stopped-evidence',
                       'No executor was dispatched by this isolated offline smoke fixture')
        receipt = cli('recover', 'smoke', 'a-0001', '--approval', approval['id'])
        assert cli('recover', 'smoke', 'a-0001', '--approval', approval['id']) == receipt
        trace = cli('export', 'smoke')
        assert trace['state']['assignments'][0]['assignment_id'] == 'a-0001'
        assert len(trace['state']['assignments']) == 1
        assert len(trace['state']['workflow']['receipts']) == 1
        assert trace['observations_transactional'] is False
        assert cli('plan', 'smoke')['suspect'] == []
        dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=project,
                               capture_output=True, text=True, check=True)
        assert not dirty.stdout
    print('PASS: installed goal checkpoint/approval/recovery/export; import=' + str(module_path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
