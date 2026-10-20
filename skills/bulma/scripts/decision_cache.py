"""Short-lived cache for unchanged, explicitly identified Jev evidence."""
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

ELIGIBLE = {'fd.triage', 'lstm.verify', 'review.risk', 'reviewer.failure_class',
            'dispatch.tier', 'insight.classify'}
TTL = 300


def cache_key(hook, request, thresholds, doc, graph_answers, context, policy):
    if (os.environ.get('BULMA_JEV_CACHE') == '0' or hook['id'] not in ELIGIBLE
            or doc.get('truncated') or not context.get('evidence')):
        return None
    if hook['id'] != 'insight.classify' and not context.get('repo'):
        return None
    payload = [hook, request, thresholds, doc['power'], doc['model'], graph_answers, context, policy]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def read(folder, key):
    if not key:
        return None
    try:
        record = json.loads((Path(folder) / (key + '.json')).read_text())
        age = time.time() - record['created_at']
        if (record['key'] == key and 0 <= age <= TTL and isinstance(record['response'], dict)
                and record.get('response_hash') == hashlib.sha256(
                    json.dumps(record['response'], sort_keys=True).encode()).hexdigest()):
            return record['response']
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def write(folder, key, response):
    if not key:
        return
    folder = Path(folder)
    tmp = folder / (key + '.' + uuid.uuid4().hex + '.tmp')
    try:
        folder.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({'key': key, 'created_at': time.time(), 'response': response,
                                  'response_hash': hashlib.sha256(json.dumps(response, sort_keys=True).encode()).hexdigest()}))
        tmp.replace(folder / (key + '.json'))
    except OSError:
        # Optimization failure must not change a decision or repeat a remote call.
        pass
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
