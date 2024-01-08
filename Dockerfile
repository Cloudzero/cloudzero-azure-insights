# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /usr/src/app

# Install any needed packages specified in requirements.txt
# First, update apt-get and install gcc and Python development headers
RUN apt-get update && apt-get install -y gcc python3-dev

# Copy only the requirements.txt initially to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the current directory contents into the container at /usr/src/app
COPY . .

# Run app.py when the container launches
CMD ["python", "./app/app.py"]
