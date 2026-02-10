import uuid


def gen_id():
    uuid_no_dash = uuid.uuid4().hex
    return uuid_no_dash
