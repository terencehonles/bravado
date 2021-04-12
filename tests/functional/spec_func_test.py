# -*- coding: utf-8 -*-
"""
Swagger Specification related functional tests
"""
import httpretty
import pytest
from swagger_spec_validator.common import SwaggerValidationError

from bravado.client import ResourceDecorator
from bravado.client import SwaggerClient
from tests.functional.conftest import API_DOCS_URL
from tests.functional.conftest import register_get
from tests.functional.conftest import register_spec


def test_invalid_spec_raises_SwaggerValidationError(
        httprettified, swagger_dict):
    swagger_dict['paths']['/test_http']['get']['parameters'][0]['type'] = 'X'
    register_spec(swagger_dict)
    with pytest.raises(SwaggerValidationError) as excinfo:
        SwaggerClient.from_url(API_DOCS_URL)
    assert 'is not valid' in str(excinfo.value)


def test_correct_route_with_basePath_as_slash(httprettified, swagger_dict):
    register_spec(swagger_dict)
    register_get("http://localhost/test_http?test_param=foo")
    resource = SwaggerClient.from_url(API_DOCS_URL).api_test
    assert resource.testHTTP(test_param="foo").result() is None


def test_basePath_works(httprettified, swagger_dict):
    swagger_dict["basePath"] = "/append"
    register_spec(swagger_dict)
    register_get("http://localhost/append/test_http?test_param=foo")
    resource = SwaggerClient.from_url(API_DOCS_URL).api_test
    resource.testHTTP(test_param="foo").result()
    assert ["foo"] == httpretty.last_request().querystring['test_param']


def test_resources_are_attrs_on_client(httprettified, swagger_dict):
    register_spec(swagger_dict)
    client = SwaggerClient.from_url(API_DOCS_URL)
    assert isinstance(client.api_test, ResourceDecorator)


def test_headers_sendable_with_api_doc_request(httprettified, swagger_dict):
    register_spec(swagger_dict)
    SwaggerClient.from_url(API_DOCS_URL, request_headers={'foot': 'bart'})
    assert 'bart' == httpretty.last_request().headers.get('foot')


def test_hostname_if_passed_overrides_origin_url(httprettified, swagger_dict):
    register_get("http://foo/test_http?", body='{}')
    swagger_dict['host'] = 'foo'
    register_spec(swagger_dict)
    resource = SwaggerClient.from_url(API_DOCS_URL).api_test
    resource.testHTTP(test_param="foo").result()
    assert ["foo"] == httpretty.last_request().querystring['test_param']


def test_correct_route_with_basePath_no_slash(httprettified, swagger_dict):
    register_get(
        "http://localhost/lame/test/test_http?test_param=foo",
        body=u'""')
    swagger_dict["basePath"] = "/lame/test"
    register_spec(swagger_dict)
    resource = SwaggerClient.from_url(API_DOCS_URL).api_test
    assert resource.testHTTP(test_param="foo").result() is None
