
import pytest
import requests
import json
from pathlib import Path

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


def test_config_success(mocker):
    """Test successful loading of config from .easelrc."""
    mock_home = Path("/fake/home")
    mocker.patch('pathlib.Path.home', return_value=mock_home)

    config_data = {
        "hostname": "my.canvas.com",
        "access_token": "my_token",
        "db_path": "/fake/path/to/db.json"
    }
    mock_file_content = json.dumps(config_data)
    mocker.patch('builtins.open', mocker.mock_open(read_data=mock_file_content))

    config = helpers.Config()

    assert config.hostname == "my.canvas.com"
    assert config.access_token == "my_token"
    assert config.db_path == "/fake/path/to/db.json"
    assert config.config_file == mock_home / ".easelrc"


def test_config_file_not_found(mocker, capsys):
    """Test that Config exits if .easelrc is not found."""
    mock_home = Path("/fake/home")
    mocker.patch('pathlib.Path.home', return_value=mock_home)
    mocker.patch('builtins.open', side_effect=FileNotFoundError)

    with pytest.raises(SystemExit) as e:
        helpers.Config()

    assert e.type == SystemExit
    assert e.value.code == 1

    captured = capsys.readouterr()
    assert "Config file not found" in captured.err
    assert str(mock_home / ".easelrc") in captured.err


def test_config_malformed_json(mocker, capsys):
    """Test that Config exits if .easelrc is malformed."""
    mock_home = Path("/fake/home")
    mocker.patch('pathlib.Path.home', return_value=mock_home)
    mocker.patch('builtins.open', mocker.mock_open(read_data="not valid json"))

    with pytest.raises(SystemExit) as e:
        helpers.Config()

    assert e.type == SystemExit
    assert e.value.code == 1

    captured = capsys.readouterr()
    assert "is malformed" in captured.err
    assert str(mock_home / ".easelrc") in captured.err


def test_config_no_home_directory(mocker):
    """Test that Config raises ValueError if home directory is not set."""
    mocker.patch('pathlib.Path.home', return_value="")

    with pytest.raises(ValueError, match="home directory is not set"):
        helpers.Config()
