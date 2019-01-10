import os, json, sys, random

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def generate_secret_key():
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'

    secret_key = ''.join(
        random.choice(chars[random.randrange(0, len(chars))])
        for x in range(50)
        )

    new_secrets_json = None
    with open(os.path.join(BASE_DIR, 'settings', 'secrets.json'), 'r') as f:
        fsecrets_json = json.loads(f.read())
        fsecrets_json['SECRET_KEY'] = secret_key
        new_secrets_json = json.dumps(
            fsecrets_json, sort_keys=True, indent=2, separators=(',', ': ')
            )

    os.remove(os.path.join(BASE_DIR, 'settings', 'secrets.json'))

    with open(os.path.join(BASE_DIR, 'settings', 'secrets.json'), 'w+') as f:
        f.write(new_secrets_json)

def raise_configuration_exception(message):
    if __name__ == '__main__':
        raise Exception(message)
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(message)

def get_secret_json(setting, default=None):
    """Get the secret variable of return an explicit exception"""
    try:
        return secrets_json[setting]
    except KeyError:
        if default:
            return default
        error_msg = "Set the {0} property in secrets.json".format(setting)
        raise_configuration_exception(error_msg)

def get_secret_env(setting, default=None):
    """Get the secret variable of return an explicit exception"""
    try:
        return os.environ[setting]
    except KeyError:
        if default:
            return default
        error_msg = "Set the {0} property in an environment variable".format(setting)
        raise_configuration_exception(error_msg)

get_secret = None
if os.path.isfile(os.path.join(BASE_DIR, 'settings', 'secrets.json')):
    with open(os.path.join(BASE_DIR, 'settings', 'secrets.json')) as f:
        secrets_json = json.loads(f.read())
    get_secret = get_secret_json
else:
    get_secret = get_secret_env

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print( get_secret(sys.argv[1], sys.argv[2]) )
    else:
        if sys.argv[1] == '--generate-secret-key':
            generate_secret_key()
        else:
            print( get_secret(sys.argv[1]) )
