def truncate_for_log(obj, max_len=20):
    if isinstance(obj, str):
        return obj[:max_len] + "..." if len(obj) > max_len else obj
    elif isinstance(obj, list):
        return [truncate_for_log(item, max_len) for item in obj[:5]]
    elif isinstance(obj, dict):
        return {k: truncate_for_log(v, max_len) for k, v in obj.items()}
    return obj
