import pytest
from pytest_mock import MockerFixture
from lodocker.helpers import Helpers
user_input = Helpers.user_input

def test_default_value(mocker: MockerFixture):
    mocker.patch('builtins.input', return_value='')  # Simulate pressing Enter
    mocker.patch('builtins.print')  # Suppress print output
    assert user_input(
        "Please choose:", default="Default Value", custom_value=True
    ) == "Default Value"

def test_option_selection(mocker: MockerFixture):
    mocker.patch('builtins.input', return_value='1')
    mocker.patch('builtins.print')
    assert user_input(
        "Please choose:", options=["Option 1", "Option 2"], default="Option 2"
    ) == "Option 1"

def test_custom_value_allowed_and_selected(mocker: MockerFixture):
    # First for selecting custom option, second for entering the value
    mocker.patch('builtins.input', side_effect=['3', 'Custom Value'])
    mocker.patch('builtins.print')
    assert user_input(
        "Please choose:",
        options=["Option 1", "Option 2"],
        custom_value=True
    ) == "Custom Value"

def test_custom_value_allowed_not_selected(mocker: MockerFixture):
    # Directly input custom value without selecting the option
    mocker.patch('builtins.input', return_value='Custom Direct Input')
    mocker.patch('builtins.print')
    assert user_input("Please choose:", custom_value=True) == "Custom Direct Input"

def test_invalid_option_retries(mocker: MockerFixture):
    # First input is invalid, second is valid
    mocker.patch('builtins.input', side_effect=['4', '1'])
    mocker.patch('builtins.print')
    assert user_input("Please choose:", options=["Option 1", "Option 2"]) == "Option 1"

def test_simplified_prompt_without_options(mocker: MockerFixture):
    # Simulate user entering a custom tag name
    input_text = 'Custom Tag Name'
    mocker.patch('builtins.input', return_value=input_text)
    mocker.patch('builtins.print')
    assert user_input(
        "Please select a git tag name",
        default="libreoffice-7.6.5.1",
        custom_value=True
    ) == input_text

def test_default_not_in_options_error(mocker: MockerFixture):
    mocker.patch('builtins.input', return_value='')
    mocker.patch('builtins.print')
    with pytest.raises(ValueError):
        user_input(
            "Please choose:",
            options=["Option 1", "Option 2"],
            default="Invalid Default"
        )

def test_no_options_custom_value_false_error(mocker: MockerFixture):
    mocker.patch('builtins.input', return_value='')
    mocker.patch('builtins.print')
    with pytest.raises(ValueError):
        user_input("Please choose:", custom_value=False)

def test_accept_input_no_default_no_options(mocker: MockerFixture):
    input_text = "User Input Without Default or Options"
    mocker.patch('builtins.input', return_value=input_text)
    mocker.patch('builtins.print')
    assert user_input("Please enter a value:", custom_value=True) == input_text

def test_empty_input_no_default(mocker: MockerFixture):
    mocker.patch('builtins.input', return_value='')
    mocker.patch('builtins.print')
    # Assuming the function should return None or prompt again.
    # Adjust based on actual behavior.
    assert user_input("Please enter a value:", custom_value=True) is None

def test_default_value_not_in_options_with_custom_value(mocker: MockerFixture):
    mocker.patch('builtins.input', return_value='')
    mocker.patch('builtins.print')
    assert user_input(
        "Please choose:",
        options=["Option 1", "Option 2"],
        default="Default Not in Options",
        custom_value=True
    ) == "Default Not in Options"

