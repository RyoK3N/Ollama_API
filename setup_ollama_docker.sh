#!/bin/bash

# ==============================================================================
# Script Name: setup_ollama_docker.sh
# Description: Installs Docker, sets up the NVIDIA Container Toolkit if applicable,
#              and runs the Ollama Docker container based on the system's hardware
#              configuration. It ensures Ollama runs on port 11434 (default Ollama port).
# Author:      Reiyo
# Email:       reiyo@sparrowup.com
# Version:     1.0.0
# Date:        2025-01-17
# License:     MIT License
# ==============================================================================
#
# ==============================================================================
# Copyright (c) 2025 Reiyo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

# Exit immediately if a command exits with a non-zero status,treat unset variables as an error, and ensure that pipelines return the exit status of the last command to exit with a non-zero status
set -euo pipefail

# Configuration
CONFIG_FILE="./config.toml"
LOG_FILE="./setup_ollama_docker.log"

# Redirect stdout and stderr to log file
exec > >(tee -a "$LOG_FILE") 2>&1

# Function to print messages
print_message() {
    echo "========================================"
    echo "$1"
    echo "========================================"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to parse configuration TOML file
parse_toml() {
    local key="$1"
    local table="$2"
    if [ -z "$table" ]; then
        grep "^$key" "$CONFIG_FILE" | sed -E 's/^.*= *"?(.*?)"?$/\1/'
    else
        # Extract lines from a specific table
        # Assumes no nested tables
        awk "/^\[$table\]/,/^\[/" "$CONFIG_FILE" | grep "^$key" | sed -E 's/^.*= *"?(.*?)"?$/\1/'
    fi
}

# Function to install Docker
install_docker() {
    if command_exists docker; then
        print_message "Docker is already installed."
    else
        print_message "Installing Docker..."
        # Update apt package index
        sudo apt-get update -y

        # Install packages to allow apt to use a repository over HTTPS
        sudo apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg-agent \
            software-properties-common

        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

        # Verify the fingerprint (optional but recommended)
        sudo apt-key fingerprint 0EBFCD88

        # Add Docker repository
        sudo add-apt-repository \
           "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
           $(lsb_release -cs) \
           stable"

        # Update the apt package index again
        sudo apt-get update -y

        # Install Docker Engine
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io

        # Add current user to the docker group
        sudo usermod -aG docker "$USER"

        print_message "Docker installed successfully."

        # Prompt user to log out and back in
        echo "Please log out and log back in to apply Docker group changes."
        exit 0
    fi
}

# Function to install NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    print_message "Installing NVIDIA Container Toolkit..."

    # Add the GPG key
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -

    # Add the repository
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/ubuntu$VERSION_ID/libnvidia-container.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    # Create keyring file if it doesn't exist
    sudo mkdir -p /usr/share/keyrings
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/amd64/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

    # Update apt and install the toolkit
    sudo apt-get update -y
    sudo apt-get install -y nvidia-container-toolkit

    # Configure Docker to use the NVIDIA runtime
    sudo nvidia-ctk runtime configure --runtime=docker

    # Restart Docker to apply changes
    sudo systemctl restart docker

    print_message "NVIDIA Container Toolkit installed and configured."
}

# Function to run Ollama Docker container
run_ollama_container() {
    local docker_run_cmd="$1"

    # Check if a container named 'ollama' already exists
    if docker ps -a --format '{{.Names}}' | grep -Eq "^ollama$"; then
        print_message "Existing 'ollama' container found. Removing it..."
        docker stop ollama || true
        docker rm ollama || true
        print_message "'ollama' container removed."
    fi

    print_message "Running Ollama Docker container..."
    eval "$docker_run_cmd"

    print_message "Ollama Docker container is up and running."
}

# Function to determine GPU Vendor
determine_gpu_vendor() {
    local vendor="CPU"
    for name in $GPU_NAMES; do
        if [[ "$name" == *"Tesla"* || "$name" == *"GeForce"* || "$name" == *"Quadro"* || "$name" == *"RTX"* || "$name" == *"GTX"* ]]; then
            vendor="NVIDIA"
            break
        elif [[ "$name" == *"Radeon"* || "$name" == *"AMD"* ]]; then
            vendor="AMD"
            break
        fi
    done
    echo "$vendor"
}

# Function to validate Docker installation
validate_docker_installation() {
    if ! command_exists docker; then
        echo "Docker installation failed. Please check the logs for details."
        exit 1
    fi

    # Test Docker by running a hello-world container
    if ! docker run --rm hello-world >/dev/null 2>&1; then
        echo "Docker is not functioning correctly. Please check the installation."
        exit 1
    fi
}

# Function to validate NVIDIA Container Toolkit installation
validate_nvidia_installation() {
    if ! docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu20.04 nvidia-smi >/dev/null 2>&1; then
        echo "NVIDIA Container Toolkit installation failed or GPU not accessible to Docker."
        exit 1
    fi
}

# Main Execution Flow

print_message "Starting Ollama Docker Setup..."

# Step 1: Install Docker
install_docker

# After installing Docker and adding user to docker group, prompt user to log out and log back in
# Since the script already exited after docker installation, the user needs to rerun the script after logging back in

# Check if the user is in the docker group
if groups "$USER" | grep -Eq '\bdocker\b'; then
    print_message "User '$USER' is already in the docker group."
else
    print_message "User '$USER' has been added to the docker group."
    print_message "Please log out and log back in to apply Docker group changes."
    exit 0
fi

# Step 2: Validate Docker Installation
validate_docker_installation

# Step 3: Determine GPU and CUDA availability
VENDOR=$(determine_gpu_vendor)

if [ "$CUDA_AVAILABLE" = "true" ] && [ "$VENDOR" = "NVIDIA" ]; then
    echo "Detected NVIDIA GPU with CUDA support: $GPU_NAMES"
    install_nvidia_container_toolkit
    # Validate NVIDIA installation
    validate_nvidia_installation
    # Docker run command for NVIDIA GPU
    DOCKER_RUN_CMD="docker run -d --gpus all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama"
elif [ "$CUDA_AVAILABLE" = "true" ] && [ "$VENDOR" = "AMD" ]; then
    echo "Detected AMD GPU: $GPU_NAMES"
    # Install AMD ROCm Toolkit (Not implemented in this script)
    echo "AMD GPU detected. Please install ROCm manually or extend the script to support AMD GPUs."
    # Example Docker run command for AMD GPU:
    # DOCKER_RUN_CMD="docker run -d --device /dev/kfd --device /dev/dri -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama:rocm"
    # For now, fallback to CPU-only
    DOCKER_RUN_CMD="docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama"
else
    echo "No compatible GPU detected or CUDA not available. Proceeding with CPU-only setup."
    # Docker run command for CPU only
    DOCKER_RUN_CMD="docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama"
fi

# Step 4: Run Ollama Docker container
run_ollama_container "$DOCKER_RUN_CMD"

print_message "Ollama Docker Setup Completed Successfully!"

echo "You can verify the Ollama container status by running:"
echo "  docker ps -a | grep ollama"

echo "To run a model locally, execute:"
echo "  docker exec -it ollama ollama run llama3"

# ==============================================================================
# End of setup_ollama_docker.sh
# ==============================================================================