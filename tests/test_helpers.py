
import pytest

from easel import helpers

def test_isurl():
    assert helpers.isurl("http://example.com") == True
    assert helpers.isurl("https://example.com") == True
    assert helpers.isurl("ftp://example.com") == False
    assert helpers.isurl("example.com") == False
    assert helpers.isurl("/local/path") == False
    assert helpers.isurl(None) == False

def test_make_nested_filename():
    expected = "parent--child.yaml"
    actual = helpers.make_nested_filename("parent.yaml", "child.yaml")
    assert actual == expected

def test_filter_canvas_html():
    canvas_comment = '<!-- OMITTED ... -->'
    html_with_comment = f'<p>Some content.</p>{canvas_comment}'
    html_without_comment = '<p>Some content.</p>'

    assert helpers.filter_canvas_html(html_with_comment) == html_without_comment
    assert helpers.filter_canvas_html(html_without_comment) == html_without_comment
    assert helpers.filter_canvas_html(None) == None
