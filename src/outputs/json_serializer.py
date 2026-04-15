import json
from typing import List, Dict
from datetime import datetime

class JSONSerializer:
    @staticmethod
    def serialize(sources_metadata: List[Dict], all_claims: List[Dict], output_path: str):
        data = {
            'generated_at': datetime.now().isoformat(),
            'sources': sources_metadata,
            'claims': all_claims
        }
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)