# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import patch

from app.utils import create_directory_if_not_exists


class TestCreateDirectoryIfNotExists:
    """Tests for create_directory_if_not_exists function."""

    @patch('app.utils.os.path.exists')
    @patch('app.utils.os.makedirs')
    @patch('app.utils.logging.info')
    def test_creates_directory_when_not_exists(self, mock_logging, mock_makedirs, mock_exists):
        """Should create directory when it doesn't exist."""
        # Arrange
        mock_exists.return_value = False

        # Act
        create_directory_if_not_exists("test_dir")

        # Assert
        mock_makedirs.assert_called_once_with("test_dir")
        mock_logging.assert_called()
        assert "created" in str(mock_logging.call_args).lower()

    @patch('app.utils.os.path.exists')
    @patch('app.utils.os.makedirs')
    @patch('app.utils.logging.info')
    def test_does_not_create_when_exists(self, mock_logging, mock_makedirs, mock_exists):
        """Should not create directory when it already exists."""
        # Arrange
        mock_exists.return_value = True

        # Act
        create_directory_if_not_exists("test_dir")

        # Assert
        mock_makedirs.assert_not_called()
        mock_logging.assert_called()
        assert "exists" in str(mock_logging.call_args).lower()

    @patch('app.utils.os.path.exists')
    @patch('app.utils.os.makedirs')
    def test_raises_os_error_on_permission_denied(self, mock_makedirs, mock_exists):
        """Should raise OSError when directory creation fails."""
        # Arrange
        mock_exists.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        # Act & Assert
        with pytest.raises(OSError):
            create_directory_if_not_exists("test_dir")

    @patch('app.utils.os.path.exists')
    @patch('app.utils.os.makedirs')
    def test_creates_nested_directories(self, mock_makedirs, mock_exists):
        """Should create nested directories using os.makedirs."""
        # Arrange
        mock_exists.return_value = False

        # Act
        create_directory_if_not_exists("path/to/nested/dir")

        # Assert
        mock_makedirs.assert_called_once_with("path/to/nested/dir")

    @patch('app.utils.os.path.exists')
    @patch('app.utils.os.makedirs')
    @patch('app.utils.logging.info')
    def test_logs_correct_directory_name(self, mock_logging, mock_makedirs, mock_exists):
        """Should log the correct directory name."""
        # Arrange
        mock_exists.return_value = False
        directory_name = "my_special_dir"

        # Act
        create_directory_if_not_exists(directory_name)

        # Assert
        log_message = str(mock_logging.call_args)
        assert directory_name in log_message
