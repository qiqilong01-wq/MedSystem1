"""Separate process check of packaged resources; never load models or call providers."""
import json
from pathlib import Path
from unittest.mock import patch

import medsystem1
from medsystem1 import MedSystem1, RequestModel, ResponseModel
from medsystem1.core.rules_engine import metadata_event
from medsystem1.policy import _resource_root


def main():
    checkout=Path(__file__).resolve().parents[1]
    assert not Path(medsystem1.__file__).resolve().is_relative_to(checkout), 'must use installed wheel'
    root=_resource_root()
    request=json.loads(root.joinpath('examples/ophthalmology/request.json').read_text(encoding='utf-8'))
    with patch('socket.socket',side_effect=AssertionError('network forbidden')):
        system=MedSystem1()
        high=system.decide(request)
        assert high['review_required'] and len(high['results'])==6
        request['tasks']=['laterality']
        request['patient_state']['facts']=[]
        request['patient_state']['sources'][0]['text']='患者右眼模糊三个月，否认闪光和飞蚊。'
        low=system.decide(request)
        assert low['route']=='rules' and low['results'][0]['value']=='right'
    schema_dir=Path(str(root))/'schemas/v0.1'
    model=RequestModel.from_dict(request,schema_dir)
    assert ResponseModel.from_dict(low,model,schema_dir).to_dict()==low
    assert 'evidence' not in json.dumps(metadata_event(low))
    print('PASS: installed wheel resources, canonical rules/review and zero provider calls')


if __name__=='__main__':
    main()
