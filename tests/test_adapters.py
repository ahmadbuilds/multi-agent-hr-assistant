"""
Tests for infrastructure adapters.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from infrastructure.adapters.clerk_leave_balance_adapter import ClerkLeaveBalanceAdapter


class TestClerkLeaveBalanceAdapter:
    """Test cases for ClerkLeaveBalanceAdapter."""

    def test_adapter_initialization(self):
        """Test ClerkLeaveBalanceAdapter initialization."""
        with patch('infrastructure.adapters.clerk_leave_balance_adapter.CLERK_API_KEY', 'https://api.test.com'):
            adapter = ClerkLeaveBalanceAdapter()
            assert adapter.api_key == 'https://api.test.com'

    @patch('requests.get')
    def test_get_leave_balance_success(self, mock_get):
        """Test successful leave balance retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {"leave_balance": 15}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch('infrastructure.adapters.clerk_leave_balance_adapter.CLERK_API_KEY', 'https://api.test.com'):
            adapter = ClerkLeaveBalanceAdapter()
            balance = adapter.get_leave_balance("test_token_123")

            assert balance == 15
            mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_leave_balance_error_handling(self, mock_get):
        """Test error handling in get_leave_balance."""
        mock_get.side_effect = requests.RequestException("Connection error")

        with patch('infrastructure.adapters.clerk_leave_balance_adapter.CLERK_API_KEY', 'https://api.test.com'):
            adapter = ClerkLeaveBalanceAdapter()
            balance = adapter.get_leave_balance("test_token_123")

            # Should return 0 on error
            assert balance == 0

    @patch('requests.get')
    def test_get_leave_balance_zero_days(self, mock_get):
        """Test leave balance retrieval returning zero days."""
        mock_response = Mock()
        mock_response.json.return_value = {"leave_balance": 0}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch('infrastructure.adapters.clerk_leave_balance_adapter.CLERK_API_KEY', 'https://api.test.com'):
            adapter = ClerkLeaveBalanceAdapter()
            balance = adapter.get_leave_balance("test_token_123")

            assert balance == 0

    @patch('requests.get')
    def test_get_leave_balance_missing_key(self, mock_get):
        """Test when API response doesn't contain leave_balance key."""
        mock_response = Mock()
        mock_response.json.return_value = {}  # Missing leave_balance key
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch('infrastructure.adapters.clerk_leave_balance_adapter.CLERK_API_KEY', 'https://api.test.com'):
            adapter = ClerkLeaveBalanceAdapter()
            balance = adapter.get_leave_balance("test_token_123")

            # Should return 0 when key is missing
            assert balance == 0

    @patch('requests.get')
    def test_get_leave_balance_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_get.side_effect = requests.HTTPError("404 Not Found")

        with patch('infrastructure.adapters.clerk_leave_balance_adapter.CLERK_API_KEY', 'https://api.test.com'):
            adapter = ClerkLeaveBalanceAdapter()
            balance = adapter.get_leave_balance("test_token_123")

            assert balance == 0

    @patch('requests.get')
    def test_get_leave_balance_auth_token_passed(self, mock_get):
        """Test that auth token is correctly passed in request."""
        mock_response = Mock()
        mock_response.json.return_value = {"leave_balance": 10}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch('infrastructure.adapters.clerk_leave_balance_adapter.CLERK_API_KEY', 'https://api.test.com'):
            adapter = ClerkLeaveBalanceAdapter()
            adapter.get_leave_balance("test_token_xyz")

            # Verify the token was passed in headers
            call_args = mock_get.call_args
            assert 'Authorization' in call_args.kwargs['headers'] or 'Authorization' in str(call_args)


class TestLeaveBalancePortInterface:
    """Test cases for LeaveBalancePort interface."""

    def test_port_implementation(self, mock_leave_balance_port):
        """Test that LeaveBalancePort can be implemented."""
        balance = mock_leave_balance_port.get_leave_balance("test_token")
        assert balance == 15

    def test_multiple_calls_different_tokens(self, mock_leave_balance_port):
        """Test multiple calls with different tokens."""
        balance1 = mock_leave_balance_port.get_leave_balance("token_1")
        balance2 = mock_leave_balance_port.get_leave_balance("token_2")

        assert balance1 == 15
        assert balance2 == 15
        assert mock_leave_balance_port.get_leave_balance.call_count == 2


class TestTicketCreationPort:
    """Test cases for TicketCreationPort."""

    def test_port_implementation(self, mock_ticket_creation_port, sample_ticket_creation):
        """Test that TicketCreationPort can be implemented."""
        result = mock_ticket_creation_port.create_ticket(sample_ticket_creation, "test_token")
        assert result is True

    def test_ticket_creation_failure(self, mock_ticket_creation_port, sample_ticket_creation):
        """Test ticket creation failure."""
        mock_ticket_creation_port.create_ticket.return_value = False
        result = mock_ticket_creation_port.create_ticket(sample_ticket_creation, "test_token")
        assert result is False


class TestAdapterIntegration:
    """Integration tests for adapters."""

    def test_leave_balance_adapter_integration(self):
        """Test leave balance adapter integration."""
        with patch('infrastructure.adapters.clerk_leave_balance_adapter.CLERK_API_KEY', 'https://api.test.com'):
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.json.return_value = {"leave_balance": 20}
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                adapter = ClerkLeaveBalanceAdapter()
                
                # Test multiple calls
                balance1 = adapter.get_leave_balance("token_1")
                balance2 = adapter.get_leave_balance("token_2")

                assert balance1 == 20
                assert balance2 == 20
                assert mock_get.call_count == 2
