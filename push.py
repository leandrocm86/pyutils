import requests
from os import environ


NUC_URL = 'http://nuc/'
NUC_EXTERNAL_URL = 'http://www.portao.top/'
PUSH_EXTERNAL_URL = environ.get('PUSH_EXTERNAL_URL', '')
WARN_HEADERS = {"Priority": "urgent", "Tags": "warning"}


def push(msg: str, url=NUC_URL, warning=False):
    PUSH_URL = f'http://{environ["SERVER_IP"]}:1060/portal'
    _push(msg, url, PUSH_URL, warning)


def push_external(msg: str, url=NUC_EXTERNAL_URL, warning=False):
    assert PUSH_EXTERNAL_URL, 'Variável de ambiente PUSH_EXTERNAL_URL não definida!'
    _push(msg, url, PUSH_EXTERNAL_URL, warning)


def _push(msg: str, click_url: str, push_url: str, warning: bool):
    if click_url and not click_url.startswith('http://'):
        click_url = 'http://' + click_url
    headers = {"Click": click_url} if click_url else {}
    if warning:
        headers.update(WARN_HEADERS)
    requests.post(push_url, data=msg.encode('utf-8'), headers=headers)


if __name__ == '__main__':
    import sys
    msg = sys.argv[1]
    url = sys.argv[2] if len(sys.argv) > 2 else PUSH_EXTERNAL_URL
    _push(msg, '',  url, False)

