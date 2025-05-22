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

# Ensure system dependencies for pyenv & python build (Debian/Ubuntu)
echo "Installing system build dependencies (Debian/Ubuntu)..."
sudo apt-get update
sudo apt-get install -y \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    git

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

# Install Python with pyenv and set as local
PYTHON_VERSION="3.10.14"
pyenv install --skip-existing $PYTHON_VERSION
pyenv local $PYTHON_VERSION

# Ensure the correct Python is used
PYTHON_BIN="$(pyenv which python)"
echo "Using Python binary: $PYTHON_BIN"
"$PYTHON_BIN" --version

# Create and activate venv using the forced Python version
echo "Creating new venv using Python $PYTHON_VERSION..."
"$PYTHON_BIN" -m venv venv
source venv/bin/activate

# Upgrade pip and setuptools
echo "Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel

# Install requirements.txt if present
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found, skipping package installation."
fi

echo
echo "Setup complete!"
echo "To activate your virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo

# Check for .venv directory and activate if present
if [ -f "train_model.py" ]; then
    echo "Running train_model.py..."
    python train_model.py
else
    echo "train_model.py not found, skipping model training."
fi

echo
echo "All done!"
