import os
import json
import yaml


def list_files_within_directory(directory: str) -> list[str]:
    """
    Returns a list of all files within a directory.
    Return values returned are relative path within the input directory.

    Given the following directory structure:

    ```
    docs/
        index.md
        about.md
        topics/
            topic1.md
            topic2.md
    ```

    The return values would be:

    ```python
    assert list_files_within_directory('docs') == [
        'index.md',
        'about.md',
        'topics/topic1.md',
        'topics/topic2.md'
    ]
    ```
    """
    filepaths = []
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            path = os.path.relpath(path, directory)
            filepaths.append(path)
    return filepaths


def make_parent_directories(path: str) -> None:
    """
    Create all parent directories to the given path, if they do not yet exist.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)


def url_for_path(path: str, base_url: str = '/') -> str:
    components = path.split(os.path.sep)
    if components and components[-1] == 'index.html':
        components[-1] = ''

    if not base_url.endswith('/'):
        base_url += '/'

    return base_url + '/'.join(components)


def merge_dict(x: dict, y: dict) -> dict:
    z = dict(x)
    for k in y.keys():
        if isinstance(y[k], dict):  #noqa
            z[k] = merge_dict(x.get(k, {}), y[k])
        else:
            z[k] = y[k]
    return z


def load_json(path: str) -> dict:
    with open(path, 'r') as file:
        return json.load(file)


def load_yaml(path: str) -> dict:
    with open(path, 'r') as file:
        return yaml.safe_load(file)
