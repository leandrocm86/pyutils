"""
A simple REST client utility module using urllib from the standard library.

This module provides a requests-like interface for making HTTP requests
while using only Python's standard library (urllib) under the hood.
"""

import urllib.request
import urllib.error
import urllib.parse
lazy import json
from typing import Any, TypeVar
from http.client import HTTPResponse

from . import log


T = TypeVar("T")


class Response:
    """
    Wrapper around urllib HTTPResponse providing a requests-like API.
    """

    def __init__(self, response: HTTPResponse):
        self._response: HTTPResponse = response
        self._content: bytes | None = None

    @property
    def status_code(self) -> int:
        return self._response.status

    @property
    def headers(self):
        return self._response.headers

    @property
    def content(self) -> bytes:
        if self._content is None:
            self._content = self._response.read()
        return self._content

    @property
    def encoding(self) -> str:
        content_type = self.headers.get("Content-Type", "")
        if "charset=" in content_type:
            return content_type.split("charset=")[-1].split(";")[0].strip()
        return "utf-8"

    @property
    def text(self) -> str:
        return self.content.decode(self.encoding, errors="replace")

    def json(self) -> Any:
        return json.loads(self.text)


class HTTPError(Exception):
    """Exception raised for HTTP errors."""

    def __init__(self, code: int, reason: str, response: Response | None = None):
        super().__init__(code, reason, response)
        self.code = code
        self.reason = reason
        self.response = response

    def __str__(self) -> str:
        return f"HTTP {self.code}: {self.reason}"


class RequestError(Exception):
    """Exception raised for request errors (network, timeout, etc.)."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Request failed: {reason}")


def _prepare_data(data: str | bytes | dict[str, Any] | None) -> bytes | None:
    """
    Prepare data for the request body.

    Args:
        data: The data to send. Can be string, bytes, or dict.

    Returns:
        The data encoded as bytes, or None if data is None.
    """
    if data is None:
        return None

    if isinstance(data, bytes):
        return data

    if isinstance(data, str):
        return data.encode('utf-8')

    if isinstance(data, dict):
        return urllib.parse.urlencode(data).encode('utf-8')

    return str(data).encode('utf-8')


def _make_request(
        url: str,
        method: str,
        data: str | bytes | dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = 10) -> Response:
    """
    Internal function to make HTTP requests.

    Args:
        url: The URL to request.
        method: HTTP method (GET, POST, PUT, DELETE, etc.).
        data: Optional data to send in the request body.
        headers: Optional dictionary of HTTP headers.
        timeout: Optional timeout in seconds (10 by default).

    Returns:
        A wrapper for the HTTPResponse object from urllib.

    Raises:
        HTTPError: If the server returns an HTTP error status.
        RequestError: If the request fails due to network or other issues.
    """
    prepared_data = _prepare_data(data)
    request_headers = headers or {}

    try:
        req = urllib.request.Request(
            url,
            data=prepared_data,
            headers=request_headers,
            method=method
        )

        log.debug('Requesting %s', url)
        raw_response = urllib.request.urlopen(req, timeout=timeout)  # nosec B310
        return Response(raw_response)

    except urllib.error.HTTPError as e:
        raise HTTPError(e.code, e.reason, None) from e

    except urllib.error.URLError as e:
        raise RequestError(str(e.reason)) from e

    except Exception as e:
        raise RequestError(str(e)) from e


def get(url: str, headers: dict[str, str] | None = None, timeout: float | None = 10) -> Response:
    """
    Perform a GET request.

    Args:
        url: The URL to request.
        headers: Optional dictionary of HTTP headers.
        timeout: Optional timeout in seconds (10 by default).

    Returns:
        The raw HTTPResponse object from urllib.

    Raises:
        HTTPError: If the server returns an HTTP error status.
        RequestError: If the request fails due to network or other issues.

    Example:
        response = get('https://api.example.com/data')
        data = response.read()
    """
    return _make_request(url, 'GET', headers=headers, timeout=timeout)


def post(
    url: str,
    data: str | bytes | dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = 10
) -> Response:
    """
    Perform a POST request.

    Args:
        url: The URL to request.
        data: Optional data to send in the request body.
        headers: Optional dictionary of HTTP headers.
        timeout: Optional timeout in seconds (10 by default).

    Returns:
        The raw HTTPResponse object from urllib.

    Raises:
        HTTPError: If the server returns an HTTP error status.
        RequestError: If the request fails due to network or other issues.

    Example:
        response = post('https://api.example.com/items',
        ...                 data={'key': 'value'},
        ...                 headers={'Content-Type': 'application/json'})
        result = response.read()
    """
    return _make_request(url, 'POST', data=data, headers=headers, timeout=timeout)


def put(
    url: str,
    data: str | bytes | dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = 10
) -> Response:
    """
    Perform a PUT request.

    Args:
        url: The URL to request.
        data: Optional data to send in the request body.
        headers: Optional dictionary of HTTP headers.
        timeout: Optional timeout in seconds (10 by default).

    Returns:
        The raw HTTPResponse object from urllib.

    Raises:
        HTTPError: If the server returns an HTTP error status.
        RequestError: If the request fails due to network or other issues.

    Example:
        response = put('https://api.example.com/items/123',
        ...                data={'updated': 'value'})
        result = response.read()
    """
    return _make_request(url, 'PUT', data=data, headers=headers, timeout=timeout)


def delete(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = 10
) -> Response:
    """
    Perform a DELETE request.

    Args:
        url: The URL to request.
        headers: Optional dictionary of HTTP headers.
        timeout: Optional timeout in seconds (10 by default).

    Returns:
        The raw HTTPResponse object from urllib.

    Raises:
        HTTPError: If the server returns an HTTP error status.
        RequestError: If the request fails due to network or other issues.

    Example:
        response = delete('https://api.example.com/items/123')
        status = response.status
    """
    return _make_request(url, 'DELETE', headers=headers, timeout=timeout)
