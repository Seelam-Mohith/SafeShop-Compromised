"""Configuration for ShopSafe Lab - Compromised Simulation.

All suspicious ("lab test") behavior is gated behind the LAB_SIMULATION_ENABLED
flag. This is an authorized, local-only security laboratory. The behaviors
implemented here are *simulated indicators* only: no malware, no exploitation,
no credential theft, and no contact with real external infrastructure.
"""

import os

# Base directory of this application (the folder containing config.py).
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Accepted textual representations of booleans.
_TRUE_VALUES = ("1", "true", "yes", "on")
_FALSE_VALUES = ("0", "false", "no", "off")


def str_to_bool(value, default=False):
    """Parse a string into a boolean, validating the input.

    Raises ValueError on an unrecognized value so misconfiguration is loud
    rather than silently ignored.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        "Invalid boolean value %r. Use one of: %s"
        % (value, ", ".join(_TRUE_VALUES + _FALSE_VALUES))
    )


def _default_log_file():
    return os.path.join(BASE_DIR, "logs", "compromised_access.jsonl")


class Config:
    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "shopsafe-lab-dev-key")

    BASE_DIR = BASE_DIR

    # Extra base path for templates of the compromised storefront.
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates", "compromised")

    # Logging: configurable so automated tests can use a temporary file.
    LOG_FILE = os.environ.get("LOG_FILE", _default_log_file())

    # Networking: localhost only by default (see app.py).
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5001"))

    # The single switch that enables/disables all simulated suspicious behavior.
    # Set LAB_SIMULATION_ENABLED=false (or 0/no/off) to run a benign storefront.
    LAB_SIMULATION_ENABLED = str_to_bool(
        os.environ.get("LAB_SIMULATION_ENABLED", "true"), default=True
    )

    # Fixed, hard-coded local redirect destination for Scenario A.
    # Never derived from user input.
    LAB_REDIRECT_TARGET = "/lab-test/redirect-target"


def validate_config(config):
    """Validate a Flask config mapping and return a list of error messages."""
    errors = []

    log_file = config.get("LOG_FILE")
    if not log_file or not isinstance(log_file, str):
        errors.append("LOG_FILE must be a non-empty string path.")

    port = config.get("PORT", 5001)
    try:
        port_int = int(port)
        if not (1 <= port_int <= 65535):
            errors.append("PORT must be between 1 and 65535.")
    except (TypeError, ValueError):
        errors.append("PORT must be an integer.")

    if "LAB_SIMULATION_ENABLED" not in config:
        errors.append("LAB_SIMULATION_ENABLED must be defined (true/false).")
    else:
        try:
            str_to_bool(config.get("LAB_SIMULATION_ENABLED"))
        except ValueError as exc:
            errors.append(str(exc))

    return errors
