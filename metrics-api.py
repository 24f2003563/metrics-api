from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import os
import yaml
from dotenv import load_dotenv

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

os.environ["APP_PORT"] = "8019"
os.environ["APP_DEBUG"] = "false"


def to_bool(value):
    return str(value).lower() in ["true", "1", "yes", "on"]


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    with open("config.development.yaml") as f:
        config.update(yaml.safe_load(f))

    if os.getenv("APP_PORT"):
        config["port"] = int(os.getenv("APP_PORT"))

    if os.getenv("NUM_WORKERS"):
        config["workers"] = int(os.getenv("NUM_WORKERS"))

    if os.getenv("APP_LOG_LEVEL"):
        config["log_level"] = os.getenv("APP_LOG_LEVEL")

    if os.getenv("APP_PORT"):
        config["port"] = int(os.getenv("APP_PORT"))

    if os.getenv("APP_DEBUG"):
        config["debug"] = to_bool(os.getenv("APP_DEBUG"))

    for item in set:
        key, value = item.split("=", 1)

        if key in ["port", "workers"]:
            config[key] = int(value)

        elif key == "debug":
            config[key] = to_bool(value)

        else:
            config[key] = value

    config["api_key"] = "****"

    return config
