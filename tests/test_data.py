"""
Unit tests for data utilities
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
from datetime import datetime

# Import functions to test
from utils.data import validate_symbol, parse_symbols_input


class TestValidateSymbol:
    """Tests for validate_symbol function"""

    def test_valid_simple_symbols(self):
        """Test that standard ticker symbols are valid"""
        assert validate_symbol('AAPL') is True
        assert validate_symbol('MSFT') is True
        assert validate_symbol('A') is True
        assert validate_symbol('AA') is True
        assert validate_symbol('GOOGL') is True

    def test_valid_index_symbols(self):
        """Test that index symbols with ^ are valid"""
        assert validate_symbol('^GSPC') is True
        assert validate_symbol('^DJI') is True
        assert validate_symbol('^IXIC') is True

    def test_valid_symbols_with_suffix(self):
        """Test that symbols with exchange suffixes are valid"""
        assert validate_symbol('BRK.A') is True
        assert validate_symbol('BRK.B') is True

    def test_invalid_symbols(self):
        """Test that invalid symbols return False"""
        assert validate_symbol('') is False
        assert validate_symbol(None) is False
        assert validate_symbol('TOOLONG') is False  # More than 5 chars
        assert validate_symbol('123') is False  # Numbers only
        assert validate_symbol('AAP!L') is False  # Special characters
        assert validate_symbol('a a p l') is False  # Spaces
        assert validate_symbol('$AAPL') is False  # Invalid prefix

    def test_case_insensitivity(self):
        """Test that lowercase symbols are normalized and validated"""
        assert validate_symbol('aapl') is True
        assert validate_symbol('Aapl') is True
        assert validate_symbol('aApL') is True

    def test_whitespace_handling(self):
        """Test that whitespace is stripped"""
        assert validate_symbol('  AAPL  ') is True
        assert validate_symbol('\tMSFT\n') is True


class TestParseSymbolsInput:
    """Tests for parse_symbols_input function"""

    def test_comma_separated(self):
        """Test parsing comma-separated symbols"""
        result = parse_symbols_input('AAPL, MSFT, GOOGL')
        assert result == ['AAPL', 'MSFT', 'GOOGL']

    def test_newline_separated(self):
        """Test parsing newline-separated symbols"""
        result = parse_symbols_input('AAPL\nMSFT\nGOOGL')
        assert result == ['AAPL', 'MSFT', 'GOOGL']

    def test_mixed_separators(self):
        """Test parsing with mixed comma and newline separators"""
        result = parse_symbols_input('AAPL, MSFT\nGOOGL, AMZN')
        assert result == ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

    def test_handles_whitespace(self):
        """Test that extra whitespace is handled"""
        result = parse_symbols_input('  AAPL  ,   MSFT  ')
        assert result == ['AAPL', 'MSFT']

    def test_filters_invalid_symbols(self):
        """Test that invalid symbols are filtered out"""
        result = parse_symbols_input('AAPL, invalid!, MSFT, 123')
        assert 'AAPL' in result
        assert 'MSFT' in result
        assert 'invalid!' not in result
        assert '123' not in result

    def test_empty_input(self):
        """Test handling of empty input"""
        result = parse_symbols_input('')
        assert result == []

    def test_case_normalization(self):
        """Test that symbols are uppercased"""
        result = parse_symbols_input('aapl, msft')
        assert result == ['AAPL', 'MSFT']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
