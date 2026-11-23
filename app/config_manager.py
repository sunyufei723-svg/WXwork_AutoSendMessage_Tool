"""config.json 配置读写。"""

import json
import os

from .constants import CONFIG_FILE
from .context import add_log, ctx
from .state import state


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        state.active_roster_id = config.get("active_roster_id", "")
        ctx.subject_var.set(config.get("subject", ""))
        ctx.template_name_var.set(config.get("template_name", ""))
        ctx.interval_entry.delete(0, "end")
        ctx.interval_entry.insert(0, config.get("interval", "1"))
        ctx.message_text.delete("1.0", "end")
        ctx.message_text.insert("1.0", config.get("message_content", ""))
        ctx.count_entry.insert(0, config.get("count", ""))
        ctx.rate_entry.insert(0, config.get("rate", ""))
        ctx.avg_entry.insert(0, config.get("avg", ""))
        ctx.max_entry.insert(0, config.get("max", ""))
        ctx.content_entry.insert(0, config.get("content", ""))
        ctx.last_valid_interval = ctx.interval_entry.get().strip()
    except Exception as e:
        add_log(f"读取配置失败：{e}", "error")


def save_config():
    config = {
        "active_roster_id": state.active_roster_id,
        "subject": ctx.subject_var.get(),
        "template_name": ctx.template_name_var.get(),
        "interval": ctx.interval_entry.get(),
        "count": ctx.count_entry.get(),
        "rate": ctx.rate_entry.get(),
        "avg": ctx.avg_entry.get(),
        "max": ctx.max_entry.get(),
        "content": ctx.content_entry.get(),
        "message_content": ctx.message_text.get("1.0", "end-1c"),
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
