import requests
from os import environ

PUSH_EXTERNAL_URL = 'https://ntfy.sh/leandrocm86'
PUSH_URL = f'http://{environ["SERVER_IP"]}:1060/portal'
NUC_URL = 'http://nuc/'
WARN_HEADERS = {"Priority": "urgent", "Tags": "warning"}


def push(msg: str, url=NUC_URL, warning=False, external=False):
    if not url.startswith('http://'):
        url = 'http://' + url
    headers = {"Click": url}
    if warning:
        headers.update(WARN_HEADERS)
    requests.post(PUSH_URL if not external else PUSH_EXTERNAL_URL, data=msg.encode('utf-8'), headers=headers)
