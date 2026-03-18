import json
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class EmailMessage:
    email_id: str
    subject: str
    sender: str
    date: str
    classification: str
    classification_reason: str
    summary: str
    full_text: str


class HimalayaError(RuntimeError):
    pass


class HimalayaClient:
    def __init__(self, unread_cmd: str, read_cmd: str, mark_read_cmd: str) -> None:
        self.unread_cmd = unread_cmd
        self.read_cmd = read_cmd
        self.mark_read_cmd = mark_read_cmd

    def _run(self, command_template: str, **kwargs: str) -> str:
        rendered = command_template.format(**kwargs)
        args = shlex.split(rendered)
        result = subprocess.run(args, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            stderr = result.stderr.strip() or "unknown error"
            raise HimalayaError(f"Command failed: {' '.join(args)}\n{stderr}")

        return result.stdout.strip()

    def list_unread_envelopes(self) -> list[dict[str, Any]]:
        output = self._run(self.unread_cmd)
        data = self._try_parse_json(output)

        if isinstance(data, dict):
            for key in ("items", "messages", "envelopes", "data"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break

        if not isinstance(data, list):
            raise HimalayaError(
                "Could not parse unread list. Set HIMALAYA_UNREAD_CMD to return JSON list output."
            )

        envelopes: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue

            email_id = item.get("id") or item.get("uid") or item.get("message_id") or item.get("hash")
            if not email_id:
                continue

            sender = self._extract_sender(item)
            envelopes.append(
                {
                    "email_id": str(email_id),
                    "subject": str(item.get("subject") or "(No subject)"),
                    "sender": sender,
                    "date": str(item.get("date") or item.get("internal_date") or "Unknown date"),
                }
            )

        return envelopes

    def read_email(self, email_id: str) -> str:
        output = self._run(self.read_cmd, id=email_id)
        parsed = self._try_parse_json(output)

        if isinstance(parsed, dict):
            full_text = self._extract_text(parsed)
            if full_text.strip():
                return full_text

        return output

    def mark_read(self, email_id: str) -> None:
        self._run(self.mark_read_cmd, id=email_id)

    @staticmethod
    def _try_parse_json(value: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    @staticmethod
    def _extract_sender(item: dict[str, Any]) -> str:
        raw_sender = item.get("from") or item.get("sender") or item.get("author")

        if isinstance(raw_sender, str):
            return raw_sender

        if isinstance(raw_sender, list) and raw_sender:
            first = raw_sender[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                name = first.get("name")
                addr = first.get("addr") or first.get("email")
                if name and addr:
                    return f"{name} <{addr}>"
                if name:
                    return str(name)
                if addr:
                    return str(addr)

        if isinstance(raw_sender, dict):
            name = raw_sender.get("name")
            addr = raw_sender.get("addr") or raw_sender.get("email")
            if name and addr:
                return f"{name} <{addr}>"
            if name:
                return str(name)
            if addr:
                return str(addr)

        return "Unknown sender"

    def _extract_text(self, payload: Any) -> str:
        if isinstance(payload, str):
            return payload

        if isinstance(payload, list):
            return "\n\n".join(self._extract_text(item) for item in payload if item)

        if not isinstance(payload, dict):
            return ""

        direct_keys = ("body", "text", "plain", "content", "message", "raw")
        chunks: list[str] = []

        for key in direct_keys:
            if key in payload and payload[key]:
                chunks.append(self._extract_text(payload[key]))

        for key in ("parts", "messages", "items"):
            if key in payload and isinstance(payload[key], list):
                chunks.append(self._extract_text(payload[key]))

        if chunks:
            return "\n\n".join(chunk for chunk in chunks if chunk)

        return json.dumps(payload, indent=2)
