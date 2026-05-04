#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    env = os.environ.get("ENVIRONMENT", "dev")
    settings_map = {
        "dev": "config.settings.dev",
        "staging": "config.settings.staging",
        "production": "config.settings.production",
    }
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", settings_map.get(env, "config.settings.dev")
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django not found. Activate virtualenv.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
