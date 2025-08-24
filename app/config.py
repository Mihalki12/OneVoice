from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    admin_ids: List[int]
    db_path: str


settings: Config | None = None


def load_config(dotenv_path: str | None = None) -> Config:
    global settings
    load_dotenv(dotenv_path=dotenv_path)

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set in environment")

    admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
    admin_ids: List[int] = []
    if admin_ids_raw:
        for part in admin_ids_raw.replace(";", ",").split(","):
            part = part.strip()
            if part:
                try:
                    admin_ids.append(int(part))
                except ValueError:
                    continue

    db_path = os.getenv("DB_PATH", os.path.join(os.getcwd(), "taxi_bot.sqlite3")).strip()

    settings = Config(bot_token=bot_token, admin_ids=admin_ids, db_path=db_path)
    return settings