import pytest

from kirallymanager import manager

@pytest.mark.parametrize("value, result", [('1', "'1'"), (1, 1), (1.0, 1.0)])
def test_quote_sql_string(value, result):
    """Test success cases with strings, ints, and floats.

    """

    assert manager.quote_sql_string(value) == result

def test_quote_sql_string_boolean():
    """Test that passing a boolean value raises a ValueError.

    """

    with pytest.raises(ValueError):
        manager.quote_sql_string(True)

def test_dict_to_sql_string():
    mydict = dict(a=1, b='2')
    expected_result = "a=1 AND b=\'2\'"
    assert manager.dict_to_sql_string(mydict) == expected_result


def test_dict_to_sql_string_empty():
    mydict = dict()
    assert manager.dict_to_sql_string(mydict) == ''


def test_dict_to_sql_string_fail():
    mydict = dict(a=1, b=True)
    with pytest.raises(ValueError):
        manager.dict_to_sql_string(mydict)
