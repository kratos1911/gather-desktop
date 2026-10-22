import unittest
import json
from copy import deepcopy
from unittest.mock import patch, Mock

from scripts.pilot_capacity import warm_instance, set_minimum, CapacityError, ready_state, wait_ready


class CapacityTests(unittest.TestCase):
    def service(self):
        return dict(metadata=dict(name='gather-inference-pilot',namespace='119730530113',generation=5,
            annotations={'run.googleapis.com/minScale':'1','run.googleapis.com/maxScale':'1'}),
            status=dict(observedGeneration=5,conditions=[{'type':'Ready','status':'True'}]))

    def test_observed_generation_and_target_scaling_must_match(self):
        ready = self.service()
        self.assertTrue(ready_state(ready))
        stale = deepcopy(ready)
        stale['status']['observedGeneration']=4
        self.assertFalse(ready_state(stale))
        cold = deepcopy(ready)
        cold['metadata']['annotations']['run.googleapis.com/minScale']='0'
        self.assertFalse(ready_state(cold))
        foreign = deepcopy(ready)
        foreign['metadata']['namespace']='protected-project'
        with self.assertRaises(CapacityError):
            ready_state(foreign)

    def test_warm_update_is_async_but_restore_is_acknowledged(self):
        with patch('scripts.pilot_capacity.shutil.which',return_value='gcloud.cmd'), patch(
                'scripts.pilot_capacity.subprocess.run',return_value=Mock(returncode=0)) as run:
            set_minimum(1)
            set_minimum(0)
        self.assertIn('--async',run.call_args_list[0].args[0])
        self.assertNotIn('--async',run.call_args_list[1].args[0])

    def test_controlplane_wait_observes_progress_then_stops(self):
        ready = self.service()
        pending = deepcopy(ready)
        pending['status']['observedGeneration']=4
        responses = [Mock(returncode=0,stdout=json.dumps(v).encode()) for v in (pending,ready)]
        with patch('scripts.pilot_capacity.shutil.which',return_value='gcloud.cmd'), patch(
                'scripts.pilot_capacity.subprocess.run',side_effect=responses) as run, patch(
                'scripts.pilot_capacity.time.monotonic',return_value=0), patch('scripts.pilot_capacity.time.sleep'):
            wait_ready(60)
        self.assertEqual(run.call_count,2)

    def test_controlplane_poll_count_is_bounded(self):
        pending = self.service()
        pending['status']['observedGeneration']=4
        with patch('scripts.pilot_capacity.shutil.which',return_value='gcloud.cmd'), patch(
                'scripts.pilot_capacity.subprocess.run',return_value=Mock(returncode=0,stdout=json.dumps(pending).encode())) as run, patch(
                'scripts.pilot_capacity.time.monotonic',return_value=0), patch('scripts.pilot_capacity.time.sleep'):
            with self.assertRaisesRegex(CapacityError,'^pilot_capacity_ready_timeout$'):
                wait_ready(60)
        self.assertEqual(run.call_count,12)

    def test_success_restores_minimum_zero(self):
        with patch('scripts.pilot_capacity.record') as record, patch('scripts.pilot_capacity.set_minimum') as minimum, patch('builtins.print'):
            with warm_instance():
                pass
        self.assertEqual([c.args[0] for c in minimum.call_args_list],[1,0])
        self.assertEqual(record.call_args.args,(0,False))

    def test_failure_and_interrupt_restore_minimum_zero(self):
        for error in (RuntimeError('fixture'),KeyboardInterrupt()):
            with patch('scripts.pilot_capacity.record'), patch('scripts.pilot_capacity.set_minimum') as minimum, patch('builtins.print'):
                with self.assertRaises(type(error)):
                    with warm_instance():
                        raise error
            self.assertEqual([c.args[0] for c in minimum.call_args_list],[1,0])

    def test_uncertain_warm_update_still_attempts_restore(self):
        with patch('scripts.pilot_capacity.record'), patch('scripts.pilot_capacity.set_minimum',side_effect=[CapacityError('fixture'),None]) as minimum, patch('builtins.print'):
            with self.assertRaises(CapacityError):
                with warm_instance():
                    pass
        self.assertEqual([c.args[0] for c in minimum.call_args_list],[1,0])

    def test_restore_failure_keeps_pending_record_and_clear_error(self):
        with patch('scripts.pilot_capacity.record') as record, patch('scripts.pilot_capacity.set_minimum',side_effect=[None,RuntimeError('private')]), patch('builtins.print'):
            with self.assertRaisesRegex(CapacityError,'^pilot_minimum_zero_restore_unverified$'):
                with warm_instance():
                    pass
        record.assert_called_once_with(1,True)

    def test_cli_targets_only_gather_and_explicit_account(self):
        with patch('scripts.pilot_capacity.shutil.which',return_value='gcloud.cmd'), patch(
                'scripts.pilot_capacity.subprocess.run',return_value=Mock(returncode=0)) as run:
            set_minimum(0)
        args = run.call_args.args[0]
        self.assertIn('gather-inference-pilot',args)
        self.assertIn('--project=gather-development-511211',args)
        self.assertIn('--account=kpanigrahi5602@gmail.com',args)
        self.assertIn('--min=0',args)
        self.assertEqual(run.call_args.kwargs['timeout'],45)

    def test_invalid_capacity_never_launches_cli(self):
        with patch('scripts.pilot_capacity.subprocess.run') as run:
            for value in (2,-1,True,'1'):
                with self.assertRaises(CapacityError):
                    set_minimum(value)
            run.assert_not_called()


if __name__=='__main__':
    unittest.main()
