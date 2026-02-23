import pytest
from unittest.mock import patch
from sample_code import fizzbuzz, two_sum, is_palindrome, max_subarray, climbing_stairs, valid_parentheses

def test_fizzbuzz_happy_path():
    assert fizzbuzz(15) == ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]

def test_fizzbuzz_edge_case_zero():
    assert fizzbuzz(0) == []

def test_fizzbuzz_edge_case_one():
    assert fizzbuzz(1) == ["1"]

def test_fizzbuzz_negative():
    assert fizzbuzz(-5) == []

def test_two_sum_happy_path():
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]

def test_two_sum_no_pair():
    assert two_sum([1, 2, 3], 7) == []

def test_two_sum_multiple_pairs():
    result = two_sum([3, 2, 4, 3], 6)
    assert result == [0, 3] or result == [1, 2]

def test_two_sum_empty_list():
    assert two_sum([], 5) == []

def test_is_palindrome_happy_path():
    assert is_palindrome("A man a plan a canal Panama") is True

def test_is_palindrome_empty_string():
    assert is_palindrome("") is True

def test_is_palindrome_single_character():
    assert is_palindrome("a") is True

def test_is_palindrome_special_characters():
    assert is_palindrome("A!b@a") is True

def test_is_palindrome_not_palindrome():
    assert is_palindrome("hello") is False

def test_max_subarray_happy_path():
    assert max_subarray([-2,1,-3,4,-1,2,1,-5,4]) == 6

def test_max_subarray_single_element():
    assert max_subarray([1]) == 1

def test_max_subarray_all_negative():
    assert max_subarray([-1, -2, -3]) == -1

def test_max_subarray_empty_list():
    with pytest.raises(ValueError):
        max_subarray([])

def test_climbing_stairs_happy_path():
    assert climbing_stairs(5) == 8

def test_climbing_stairs_zero():
    with pytest.raises(ValueError):
        climbing_stairs(0)

def test_climbing_stairs_one():
    assert climbing_stairs(1) == 1

def test_climbing_stairs_negative():
    with pytest.raises(ValueError):
        climbing_stairs(-3)

def test_valid_parentheses_happy_path():
    assert valid_parentheses("()[]{}") is True

def test_valid_parentheses_empty_string():
    assert valid_parentheses("") is True

def test_valid_parentheses_unbalanced():
    assert valid_parentheses("(]") is False

def test_valid_parentheses_wrong_order():
    assert valid_parentheses("([)]") is False

def test_valid_parentheses_only_closing():
    assert valid_parentheses("}}}") is False