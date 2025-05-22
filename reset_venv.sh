#!/usr/bin/env bash

set -e

# Remove old venv folders
if [ -d "venv" ]; then
    echo "Removing existing venv..."
    rm -rf venv
fi

if [ -d ".venv" ]; then
    echo "Removing existing .venv..."
    rm -rf .venv
fi

# Install pyenv if not present
if ! command -v pyenv >/dev/null 2>&1; then
    echo "pyenv not found, installing pyenv..."
    curl https://pyenv.run | bash
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    # Add pyenv init lines to shell profile if not already there
    if ! grep -q 'pyenv init' ~/.bashrc; then
        echo -e '\n# pyenv config\nexport PATH="$HOME/.pyenv/bin:$PATH"\neval "$(pyenv init --path)"\neval "$(pyenv init -)"' >> ~/.bashrc
    fi
else
    echo "pyenv found."
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
fi

# Install Python build dependencies (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing python build dependencies for Linux..."
    sudo apt update
    sudo apt install -y build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
fi

# Install Python 3.10.14 if missing
PYTHON_VERSION="3.10.14"
pyenv install --skip-existing $PYTHON_VERSION
pyenv local $PYTHON_VERSION

# Create and activate venv
echo "Creating new venv..."
python -m venv venv
source venv/bin/activate

# Upgrade pip and setup tools
echo "Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel

# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found, skipping package installation."
fi

# Print activation command
echo
echo "Setup complete! To activate your virtual environment, run:"
echo "  source venv/bin/activate"
echo
