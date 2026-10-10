"""Only mock the runner here; real smoke is an explicit separate command."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from medsystem1.bounded import BoundedAnswer, BoundedDescriptor, BoundedResult, BoundedProviderError  # noqa: E402
from tools.run_strands_smoke import run_smoke  # noqa: E402


class SmokeRunnerTests(unittest.TestCase):
    def test_missing_opt_in_does_not_load_deployment_or_call_provider(self):
        with patch('tools.run_strands_smoke.load_local_deployment') as loader:
            with self.assertRaises(BoundedProviderError):
                run_smoke(Path('not-read.json'))
        loader.assert_not_called()

    def test_mock_runner_has_ten_cases_metadata_and_truthful_match_counts(self):
        with patch('tools.run_strands_smoke.load_local_deployment') as loader, patch('tools.run_strands_smoke.StrandsHttpProvider') as cls:
            loader.return_value.config_sha256 = 'a'*64
            provider = cls.return_value
            provider.descriptor = BoundedDescriptor('strands', 'synthetic', 'a'*40, 'b'*40, 'c'*40, ('laterality',))
            provider.decide.side_effect = lambda state, tasks, timeout_ms: BoundedResult(
                (BoundedAnswer(tasks[0], 'unknown', .1, '{"unknown":0.1}'),), provider.descriptor, 1.0)
            with redirect_stdout(io.StringIO()) as output:
                report = run_smoke(Path('synthetic.json'), allow_real_provider=True)
        self.assertEqual(provider.decide.call_count, 10)
        self.assertEqual(report['contract_valid'], 10)
        self.assertLess(report['expected_label_matches'], 10)
        self.assertFalse(report['clinical_validation'])
        self.assertFalse(report['auto_enabled'])
        self.assertEqual(output.getvalue(), '')
        self.assertTrue(all('state' not in case for case in report['cases']))

    def test_mock_failures_remain_in_denominator(self):
        with patch('tools.run_strands_smoke.load_local_deployment') as loader, patch('tools.run_strands_smoke.StrandsHttpProvider') as cls:
            loader.return_value.config_sha256 = 'a'*64
            cls.return_value.descriptor = BoundedDescriptor('strands', 'synthetic', 'a'*40, 'b'*40, 'c'*40, ())
            cls.return_value.decide.side_effect = BoundedProviderError('provider_timeout')
            report = run_smoke(Path('synthetic.json'), allow_real_provider=True)
        self.assertEqual(report['attempted'], 10)
        self.assertEqual(report['contract_valid'], 0)
        self.assertTrue(all(c['error_code']=='provider_timeout' for c in report['cases']))

    def test_disabled_cli_opt_in_still_fails_without_calls(self):
        result = subprocess.run([sys.executable, str(ROOT/'tools/run_strands_smoke.py'),
            '--deployment', str(ROOT/'configs/v0.1/local-deployment.disabled.json'), '--allow-real-provider'],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertIn('capability_missing', result.stdout)
        self.assertEqual(result.stderr, '')
