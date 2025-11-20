import pytest
from easel import course

def test_get_id_from_url():
    assert course.get_id_from_url("https://canvas.example.com/courses/12345") == 12345
    assert course.get_id_from_url("https://canvas.example.com/courses/12345/assignments") == 12345
    assert course.get_id_from_url("http://canvas.example.com/courses/54321/") == 54321
    assert course.get_id_from_url("https://canvas.example.com/api/v1/courses/999/quizzes") == 999
    assert course.get_id_from_url("not a url") is None
    assert course.get_id_from_url("https://canvas.example.com/accounts/123") is None
    assert course.get_id_from_url("https://canvas.example.com/courses/not-an-id") is None
    assert course.get_id_from_url(None) is None
    assert course.get_id_from_url("https://canvas.example.com/courses/") is None
