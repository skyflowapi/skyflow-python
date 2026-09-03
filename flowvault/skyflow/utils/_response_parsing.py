def parse_tokens(raw):
    if raw is None:
        return None
    parsed = {}
    for column, value in raw.items():
        entries = _parse_entries(value, _to_token)
        if entries is not None:
            parsed[column] = entries
    return parsed


def parse_hashed_data(raw):
    if raw is None:
        return None
    parsed = {}
    for column, value in raw.items():
        entries = _parse_entries(value, _to_hash)
        if entries is not None:
            parsed[column] = entries
    return parsed


def parse_metadata(raw):
    if raw is None:
        return None
    return {
        'skyflow_id': raw.get('skyflowID', raw.get('skyflowId', raw.get('skyflow_id'))),
        'table_name': raw.get('table', raw.get('tableName', raw.get('table_name'))),
    }


def _parse_entries(raw_value, to_entry):
    if raw_value is None:
        return None
    items = raw_value if isinstance(raw_value, list) else [raw_value]
    entries = []
    for item in items:
        entry = to_entry(item)
        if entry is not None:
            entries.append(entry)
    return entries


def _to_token(entry):
    if isinstance(entry, dict):
        return {
            'token': entry.get('token'),
            'token_group_name': entry.get('tokenGroupName', entry.get('token_group_name')),
            'path': entry.get('path'),
        }
    if entry is not None:
        return {'token': entry, 'token_group_name': None, 'path': None}
    return None


def _to_hash(entry):
    if isinstance(entry, dict):
        return {
            'data': entry.get('data'),
            'hash_name': entry.get('hashName', entry.get('hash_name')),
        }
    if entry is not None:
        return {'data': entry, 'hash_name': None}
    return None
