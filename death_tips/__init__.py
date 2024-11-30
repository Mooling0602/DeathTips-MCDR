import os
try:
    import json5, json # type: ignore
    json_module = lambda *args, **kwargs: (json5(*args, **kwargs))
except ModuleNotFoundError:
    import json
    json_module = lambda *args, **kwargs: (json(*args, **kwargs))
from mcdreforged.api.all import *
try:
    from matrix_sync.reporter import send_matrix # type: ignore
    send = lambda *args, **kwargs: (send_matrix(*args, **kwargs))
except ModuleNotFoundError:
    send = lambda *args, **kwargs: psi.logger.info(*args, **kwargs)

psi = ServerInterface.psi()
MCDRConfig = psi.get_mcdr_config()
serverDir = MCDRConfig["working_directory"]

geyser_config = {
    "tr_lang": f"{serverDir}/plugins/Geyser-Spigot/locales/zh_cn.json",
    "use_json5": False
}

default_config = {
    "tr_lang": "zh_cn.json",
    "use_json5": False
}

def tr(tr_key):
    raw = psi.rtr(f"death_tips.{tr_key}")
    return str(raw)

def on_load(server: PluginServerInterface, prev_module):
    global tr_lang, tr_langRegion
    server.logger.info(tr("geyser_autodetect"))
    if os.path.exists(geyser_config["tr_lang"]):
        config = server.load_config_simple('config.json', geyser_config)
    else:
        config = server.load_config_simple('config.json', default_config)
    server.logger.info(tr("on_load"))
    tr_lang_path = config["tr_lang"]
    if os.path.exists(tr_lang_path):
        with open(f'{tr_lang_path}', 'r') as f:
            if config["use_json5"]:
                tr_lang = json_module.load(f)
            else:
                tr_lang = json.load(f)
        tr_langRegion = os.path.splitext(os.path.basename(tr_lang_path))[0]
        server.register_event_listener("PlayerDeathEvent", on_player_death)

def on_player_death(server: PluginServerInterface, player, event, content):
    from mg_events.config import langRegion, lang # type: ignore
    server.logger.info(tr("on_player_death"))
    if langRegion != tr_langRegion:
        raw = tr_lang.get(event, None)
        tip = raw.replace('%1$s', player)
        killer = content.death.killer
        weapon = content.death.weapon
        if killer is not None:
            if lang is not None:
                with open("death_tips_log.txt", "w", encoding="utf-8") as f:
                    json.dump(lang, f, ensure_ascii=False, indent=4)
                for key, value in lang.items():
                    if value == killer:
                        server.logger.info("detected mob key")
                        mobkey = key
            else:
                server.logger.info("lang cache from upstream error!")
            try:
                mob = tr_lang.get(mobkey, None)
            except UnboundLocalError:
                mob = None
            if mob is not None:
                tip = tip.replace('%2$s', mob)
            else:
                tip = tip.replace('%2$s', killer)
        if weapon is not None:
            tip = tip.replace('%3$s', weapon)
        send(tip)
