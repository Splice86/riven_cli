"""Tests for src/client.py"""

import json
import os
import tempfile
import uuid
from unittest.mock import patch, MagicMock

import pytest
import requests

# Patch config loading so it doesn't try to read secrets.yaml during import
with patch.dict(os.environ, {"RIVEN_API_URL": "http://localhost:9999"}):
    from src.client import (
        RivenClient,
        get_client,
        SESSION_FILE,
        API_URL,
        API_TIMEOUT,
        DEFAULT_SHARD,
    )


class TestRivenClientInit:
    """Tests for RivenClient initialization."""

    def test_client_uses_api_url_from_config(self):
        """Client should default to API_URL when no base_url given."""
        client = RivenClient()
        assert client.base_url == API_URL
        assert client.session_id is None
        assert client.shard_name == "default"

    def test_client_accepts_custom_base_url(self):
        """Client should use provided base_url over default."""
        client = RivenClient(base_url="http://custom:9000")
        assert client.base_url == "http://custom:9000"

    def test_client_shard_name_comes_from_default_shard_config(self):
        """shard_name should come from DEFAULT_SHARD config, not hardcoded."""
        client = RivenClient()
        assert client.shard_name == DEFAULT_SHARD


class TestCreateSession:
    """Tests for create_session()."""

    @patch("src.client.requests.post")
    def test_create_session_generates_uuid(self, mock_post):
        """Should generate a valid UUID as session_id."""
        client = RivenClient()
        result = client.create_session()
        assert result["ok"] is True
        assert result["session_id"] is not None
        uuid.UUID(result["session_id"])  # raises if invalid

    @patch("src.client.requests.post")
    def test_create_session_stores_on_client(self, mock_post):
        """Should store session_id on the client instance."""
        client = RivenClient()
        result = client.create_session()
        assert client.session_id == result["session_id"]

    @patch("src.client.requests.post")
    def test_create_session_uses_provided_shard(self, mock_post):
        """Should pass shard_name in the result."""
        client = RivenClient()
        result = client.create_session(shard_name="codehammer")
        assert result["shard_name"] == "codehammer"


class TestSendMessage:
    """Tests for send_message()."""

    def test_send_message_raises_if_no_session(self):
        """Should raise ValueError if session not created first."""
        client = RivenClient()
        with pytest.raises(ValueError, match="No session"):
            client.send_message("hello")

    @patch("src.client.requests.post")
    def test_send_message_posts_correct_payload(self, mock_post):
        """Should POST with correct JSON payload."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True, "response": "hi"}
        mock_post.return_value = mock_resp

        client = RivenClient()
        client.create_session()
        result = client.send_message("hello world")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["message"] == "hello world"
        assert call_kwargs["json"]["session_id"] == client.session_id
        assert call_kwargs["json"]["stream"] is False

    @patch("src.client.requests.post")
    def test_send_message_with_stream_returns_stream_true(self, mock_post):
        """stream=True should return stream flag in response dict."""
        mock_resp = MagicMock()
        mock_post.return_value = mock_resp

        client = RivenClient()
        client.create_session()
        result = client.send_message("hello", stream=True)
        assert result["stream"] is True
        assert result["response"] == mock_resp


class TestSessionPersistence:
    """Tests for session save/load/delete."""

    def test_save_session_writes_to_file(self):
        """save_session() should write session_id to SESSION_FILE."""
        client = RivenClient()
        client.session_id = "test-session-1234"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fake_file = f.name
        with patch("src.client.SESSION_FILE", fake_file):
            client.save_session()
            with open(fake_file) as f:
                assert f.read().strip() == "test-session-1234"
        os.unlink(fake_file)

    def test_load_session_reads_from_file(self):
        """load_session() should read session_id from SESSION_FILE."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            f.write("test-session-abcd")
            fake_file = f.name
        with patch("src.client.SESSION_FILE", fake_file):
            client = RivenClient()
            assert client.load_session() == "test-session-abcd"
        os.unlink(fake_file)

    def test_load_session_returns_none_when_file_missing(self):
        """load_session() should return None if no session file exists."""
        with patch("src.client.os.path.exists", return_value=False):
            client = RivenClient()
            assert client.load_session() is None

    def test_delete_saved_session_removes_file(self):
        """delete_saved_session() should remove SESSION_FILE."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fake_file = f.name
        with patch("src.client.SESSION_FILE", fake_file):
            client = RivenClient()
            client.delete_saved_session()
            assert not os.path.exists(fake_file)


class TestSessionExists:
    """Tests for session_exists()."""

    @patch("src.client.requests.get")
    def test_session_exists_returns_true_on_200(self, mock_get):
        """Should return True when server responds with 200."""
        mock_get.return_value = MagicMock(status_code=200)
        client = RivenClient()
        assert client.session_exists("any-id") is True

    @patch("src.client.requests.get")
    def test_session_exists_returns_false_on_404(self, mock_get):
        """Should return False when server responds with non-200."""
        mock_get.return_value = MagicMock(status_code=404)
        client = RivenClient()
        assert client.session_exists("any-id") is False

    @patch("src.client.requests.get")
    def test_session_exists_returns_false_on_connection_error(self, mock_get):
        """Should return False on connection error, not raise."""
        mock_get.side_effect = requests.exceptions.ConnectionError("nope")
        client = RivenClient()
        result = client.session_exists("any-id")
        # After fix: should return False, not raise
        assert result is False

    @patch("src.client.requests.get")
    def test_session_exists_handles_timeout(self, mock_get):
        """Should return False on timeout, not raise."""
        mock_get.side_effect = requests.exceptions.Timeout("timed out")
        client = RivenClient()
        assert client.session_exists("any-id") is False


class TestResumeSession:
    """Tests for resume_session()."""

    def test_resume_session_returns_none_when_no_saved_session(self):
        """Should return None if no session file exists."""
        with patch("src.client.os.path.exists", return_value=False):
            client = RivenClient()
            assert client.resume_session() is None

    def test_resume_session_returns_ok_with_saved_id(self):
        """Should return ok=True with saved session_id and shard."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            f.write("saved-session-xyz")
            fake_file = f.name
        with patch("src.client.SESSION_FILE", fake_file):
            client = RivenClient()
            result = client.resume_session(shard_name="codehammer")
            assert result is not None
            assert result["ok"] is True
            assert result["resumed"] is True
            assert result["session_id"] == "saved-session-xyz"
            assert result["shard_name"] == "codehammer"
            assert client.session_id == "saved-session-xyz"
        os.unlink(fake_file)


class TestCloseSession:
    """Tests for close_session()."""

    def test_close_session_clears_local_session_id(self):
        """close_session() should clear the local session_id."""
        client = RivenClient()
        client.create_session()
        assert client.session_id is not None
        client.close_session()
        assert client.session_id is None


class TestDefaultShardConfig:
    """Tests for DEFAULT_SHARD config value."""

    def test_default_shard_is_read_from_config(self):
        """DEFAULT_SHARD should be a string loaded from config."""
        assert isinstance(DEFAULT_SHARD, str)
        assert len(DEFAULT_SHARD) > 0


class TestGetClient:
    """Tests for get_client() convenience function."""

    def test_get_client_returns_riven_client_instance(self):
        """get_client() should return a RivenClient instance."""
        client = get_client()
        assert isinstance(client, RivenClient)
