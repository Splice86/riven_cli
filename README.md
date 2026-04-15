# Riven CLI

CLI client for the Riven API server. Connects to a running Riven instance and provides an interactive terminal interface.

## Install

```bash
pip install -e .
```

## Configure

Copy and edit the secrets file:

```bash
cp secrets_template.yaml secrets.yaml
# Edit secrets.yaml with your API URL
```

Or set via environment variable:

```bash
export RV_API__URL=http://localhost:8080
```

## Usage

```bash
riven
# or
python -m src
```

## Session persistence

Your session ID is saved to `~/.riven_session` so sessions persist across CLI restarts. Use `/clear` to wipe it.
