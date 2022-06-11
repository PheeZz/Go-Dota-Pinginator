import yaml


def load_yaml(file):
    try:
        with open(file, 'r') as f:
            return yaml.full_load(f)
    except FileNotFoundError:
        return dict()


def dump_yaml(file, data):
    with open(file, 'w+') as f:
        yaml.dump(data, f)
