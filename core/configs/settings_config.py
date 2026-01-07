from pydantic import ValidationError
from pydantic_settings import BaseSettings
from typing import Callable
import sys


def init_settings(settings:BaseSettings,service_name:str,env_prefix:str) -> BaseSettings:
    try:
        return settings()
        
    except ValidationError as e:
        print(f"\n❌ {service_name.upper()}-SERVICE CONFIGURATION ERROR\n {e}")

        missing = [
            err["loc"][0]
            for err in e.errors()
            if err["type"] == "missing"
        ]

        if missing:
            print(f"The following environment variables are REQUIRED for {service_name.upper()}-SERVICEE:\n")
            for field in missing:
                print(f"  - {env_prefix}{field}")

        print("\nFix your .env or environment variables and restart.\n")
        sys.exit(1)
