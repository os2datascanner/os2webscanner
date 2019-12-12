import json

def json_utf8_decode(body):
    try:
        body = json.loads(body.decode("utf-8"))
    except UnicodeDecodeError as ue:
        print('Error message: {0}'.format(ue))
        return None
    except json.JSONDecodeError as je:
        # TODO: What should happen if json data is corrupt?
        print('Error message: {0}'.format(je))
        print("* Invalid JSON: {0}".format(body))
        return None

    return body