import uuid

# ponytail: in-process cache only — each call's generated audio is fetched by Plivo within
# seconds of being created and is never needed again after hangup. A dict is enough; entries
# are cleared on hangup so this doesn't grow unbounded over the process's lifetime.
_store: dict[str, bytes] = {}


def put(call_id: uuid.UUID, data: bytes) -> None:
    _store[str(call_id)] = data


def get(call_id: uuid.UUID) -> bytes | None:
    return _store.get(str(call_id))


def discard(call_id: uuid.UUID) -> None:
    _store.pop(str(call_id), None)
