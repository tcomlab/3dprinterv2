"""InvenTree plugin for Bambu Lab printer farm monitoring."""

from __future__ import annotations

import json
import logging
from typing import Any

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin

from .client import BambuPrinterClient, PrinterConfig

logger = logging.getLogger("inventree.BambuLabFarmPlugin")


class BambuLabFarmPlugin(SettingsMixin, InvenTreePlugin):
    """Expose Bambu Lab farm status to InvenTree and keep printer state fresh."""

    NAME = "BambuLabFarm"
    SLUG = "bambulab-farm"
    TITLE = "Bambu Lab Farm"

    SETTINGS = {
        "ENABLED": {
            "name": "Enabled",
            "description": "Enable Bambu Lab farm integration",
            "default": True,
            "validator": bool,
        },
        "PRINTERS_JSON": {
            "name": "Printers JSON",
            "description": "JSON array of printers: name, serial, host, access_code, optional port",
            "default": "[]",
        },
    }

    def __init__(self):
        super().__init__()
        self._clients: dict[str, BambuPrinterClient] = {}

    def activate(self) -> None:
        if not self.get_setting("ENABLED"):
            logger.info("BambuLabFarm plugin disabled")
            return

        self._rebuild_clients()

    def deactivate(self) -> None:
        for client in self._clients.values():
            client.stop()
        self._clients.clear()

    def settings_updated(self, _key: str | None = None, _value: Any = None) -> None:
        self.deactivate()
        self.activate()

    def get_farm_status(self) -> list[dict[str, Any]]:
        """Helper callable from API/view code to inspect latest printer states."""
        return [client.status() for client in self._clients.values()]

    def refresh_farm(self) -> None:
        for client in self._clients.values():
            client.refresh()

    def _rebuild_clients(self) -> None:
        printers = self._parse_printers(self.get_setting("PRINTERS_JSON"))

        for printer in printers:
            serial = printer.serial
            if serial in self._clients:
                continue

            client = BambuPrinterClient(printer)
            client.start()
            self._clients[serial] = client
            logger.info("Connected Bambu printer %s (%s)", printer.name, serial)

    @staticmethod
    def _parse_printers(raw_value: str) -> list[PrinterConfig]:
        try:
            items = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            logger.error("Invalid PRINTERS_JSON payload: %s", exc)
            return []

        configs: list[PrinterConfig] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue

            try:
                config = PrinterConfig(
                    name=item["name"],
                    serial=item["serial"],
                    host=item["host"],
                    access_code=item["access_code"],
                    port=int(item.get("port", 8883)),
                )
            except (KeyError, TypeError, ValueError):
                logger.warning("Skipped invalid printer config: %s", item)
                continue

            configs.append(config)

        return configs
