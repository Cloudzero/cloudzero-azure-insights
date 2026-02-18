# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import os


def create_directory_if_not_exists(directory_name: str) -> None:
    """Create a directory if it does not exist.

    Args:
        directory_name: Name of the directory to create

    Raises:
        OSError: If directory creation fails due to permissions or disk space
    """
    # Check if directory exists
    if not os.path.exists(directory_name):
        # Create directory
        os.makedirs(directory_name)
        logging.info(f"Directory '{directory_name}' created.")
    else:
        logging.info(f"Directory '{directory_name}' already exists.")
