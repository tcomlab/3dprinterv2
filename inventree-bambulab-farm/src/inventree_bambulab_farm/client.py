"""Thin MQTT client for a single Bambu Lab printer."""

from __future__ import annotations

from dataclasses import dataclass
import json
import threading
from typing import Any

import paho.mqtt.client as mqtt


@dataclass(frozen=True)
class PrinterConfig:
    """Runtime configuration for one printer in the farm."""

    name: str
    serial: str
    host: str
    access_code: str
    port: int = 8883


class BambuPrinterClient:
    """Maintains connection and last-known status for one Bambu printer."""

    def __init__(self, config: PrinterConfig):
        self.config = config
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.username_pw_set("bblp", config.access_code)
        self._client.tls_set()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self._lock = threading.Lock()
        self._last_report: dict[str, Any] = {}
        self._connected = False

    def start(self) -> None:
        self._client.connect(self.config.host, self.config.port, keepalive=30)
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def refresh(self) -> None:
        payload = {
            "pushing": {
                "sequence_id": "0",
                "command": "pushall",
                "version": 1,
                "push_target": 1,
            }
        }
        self._client.publish(f"device/{self.config.serial}/request", json.dumps(payload), qos=1)

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "name": self.config.name,
                "serial": self.config.serial,
                "host": self.config.host,
                "connected": self._connected,
                "report": dict(self._last_report),
            }

    def _on_connect(self, _client, _userdata, _flags, reason_code, _properties) -> None:
        self._connected = reason_code == 0
        if self._connected:
            topic = f"device/{self.config.serial}/report"
            self._client.subscribe(topic, qos=1)
            self.refresh()

    def _on_message(self, _client, _userdata, msg) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            return

        report = payload.get("print")
        if isinstance(report, dict):
            with self._lock:
                self._last_report = report
