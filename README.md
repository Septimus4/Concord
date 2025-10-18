# Concord

Concord is a Python project that leverages FastAPI, Neo4j, and BERTopic for advanced text analysis. It provides a
platform for analyzing and visualizing text data using state-of-the-art machine learning techniques.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
    - [Clone the Repository](#clone-the-repository)
    - [Set Up Dependencies](#set-up-dependencies)
        - [Debian-based Systems](#debian-based-systems)
        - [Windows](#windows)
- [Running the Application](#running-the-application)
    - [Start Docker Containers](#start-docker-containers)
    - [Run Pre-commit Hooks and Tests](#run-pre-commit-hooks-and-tests)

## Prerequisites

- **Python 3.12+**
- **Poetry** for dependency management
- **Docker** and **Docker Compose**
- **Git**

## Installation

### Clone the Repository

```bash
git clone https://github.com/boredlabsHQ/concord.git
cd concord
```

### Set Up Dependencies

#### Debian-based Systems

1. **Update Package Lists**

   ```bash
   sudo apt update
   ```

2. **Install Required Packages**

   ```bash
   sudo apt install -y software-properties-common curl git
   ```

3. **Install Python 3.12**

   Add the Deadsnakes PPA and install Python 3.12:

   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install -y python3.12 python3.12-venv python3.12-dev
   ```

4. **Install Poetry**

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

5. **Install Docker and Docker Compose**

   ```bash
   sudo apt install -y docker.io docker-compose
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker $USER
   ```

   Log out and log back in for the group changes to take effect.

6. **Install Project Dependencies**

   ```bash
   poetry install
   poetry run pre-commit install
   ```

#### Windows

1. **Install Python 3.12**

   Download and install Python 3.12 from the [official website](https://www.python.org/downloads/windows/). During
   installation, make sure to check the box **"Add Python to PATH"**.

2. **Install Git**

   Download and install Git from the [official website](https://git-scm.com/download/win).

3. **Install Poetry**

   Open Command Prompt or PowerShell and run:

   ```powershell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

   Add Poetry to your PATH by adding the following line to your PowerShell profile:

   ```powershell
   $env:Path += ";$env:APPDATA\Python\Scripts"
   ```

4. **Install Docker Desktop**

   Download and install Docker Desktop from the [official website](https://www.docker.com/products/docker-desktop).
   Ensure that it is running before proceeding.

5. **Install Project Dependencies**

   ```powershell
   poetry install
   poetry run pre-commit install
   ```

## Set Up nltk Data

Create nltk_data directory:

```bash
mkdir -p /YOUR-PATH/nltk_data
cd /YOUR-PATH/nltk_data
```

Open a Python shell and run the following commands:

   ```python
   import nltk
   nltk.download('stopwords')
   nltk.download('punkt')
   nltk.download('wordnet')
   nltk.download('punkt_tab')
   ```

Add this env variable
   ```bash
   NLTK_DATA=/YOUR-PATH/nltk_data
   ```

## Running the Application

### Start Docker Containers

Set up a temporary Neo4j database:

```bash
docker-compose up -d
```

> **Note:** On Windows, ensure Docker Desktop is running and has sufficient resources allocated.

### Run the Concord API (MVP)

Run the FastAPI server with Poetry:

```bash
poetry run uvicorn concord.server.main:app --reload --port 8000
```

The OpenAPI docs will be available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Run Pre-commit Hooks and Tests

```bash
poetry run pre-commit run -a
```

Run the test suite (optional):

```bash
poetry run pytest -q
```

## Development

### Generating server from OpenAPI schema

Install openapi-generator

```bash
openapi-generator-cli generate -c config.yml && \
  rm -rf .flake8 docker-compose.yaml requirements.txt Dockerfile && \
  poetry run pre-commit run -a
```

## Nuxt Frontend and API Base URL

The Nuxt app (in `frontend/`) can be pointed at a local Concord API by setting a public base URL.

1) Copy the example environment file and edit as needed:

```bash
cp frontend/.env.example frontend/.env
```

2) Ensure it contains:

```
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

3) Start the dev server from the `frontend/` folder:

```bash
npm install
npm run dev
```

You can now access the UI at http://localhost:3000 while it talks to the API at http://localhost:8000.

### License

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE.md)
