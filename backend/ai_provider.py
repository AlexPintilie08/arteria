"""Bounded cloud model adapter for SIM's structured AI planning callback."""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
import json
import math
import re
from typing import Any, Callable
from urllib.parse import urlsplit

import httpx

from backend.settings import Settings

MAX_PROVIDER_RESPONSE_BYTES = 512 * 1024
MAX_PROVIDER_TIMEOUT_SECONDS = 20.0
_MODEL_ID = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


class OpenAIProviderError(Exception):
    """Safe provider failure; never includes response content or credentials."""


@dataclass(frozen=True)
class ProviderSelection:
    call_model: Callable[..., Any] | None
    provider_id: str | None
    model_id: str | None
    timeout_seconds: float
    unavailable_code: str | None = None


@dataclass(frozen=True)
class OpenAIResponsesProvider:
    model_id: str
    base_url: str
    api_key: str = field(repr=False)
    transport: httpx.BaseTransport | None = field(default=None, repr=False, compare=False)

    def structured_json(
        self,
        *,
        packet: dict[str, Any],
        system_prompt: str,
        output_schema: dict[str, Any],
        timeout_seconds: float,
    ) -> str:
        """Request strict JSON from the Responses API and return its text only."""
        try:
            packet_json = json.dumps(
                packet, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            )
            if len(packet_json.encode("utf-8")) > 65_536:
                raise OpenAIProviderError("Evidence packet exceeds the SIM limit")
            payload = {
                "model": self.model_id,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": packet_json},
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "arteria_ai_planning",
                        "strict": True,
                        "schema": output_schema,
                    }
                },
                "max_output_tokens": 4096,
                "store": False,
            }
            endpoint = self.base_url.rstrip("/") + "/responses"
            timeout = min(float(timeout_seconds), MAX_PROVIDER_TIMEOUT_SECONDS)
            if not math.isfinite(timeout) or timeout <= 0:
                raise OpenAIProviderError("Invalid provider timeout")
            with httpx.Client(timeout=timeout, transport=self.transport, follow_redirects=False) as client:
                with client.stream(
                    "POST",
                    endpoint,
                    headers={
                        "Authorization": "Bearer " + self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                ) as response:
                    if not 200 <= response.status_code < 300:
                        raise OpenAIProviderError("Cloud provider returned a non-success status")
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > MAX_PROVIDER_RESPONSE_BYTES:
                        raise OpenAIProviderError("Cloud provider response exceeds the size limit")
                    response_bytes = bytearray()
                    for chunk in response.iter_bytes():
                        response_bytes.extend(chunk)
                        if len(response_bytes) > MAX_PROVIDER_RESPONSE_BYTES:
                            raise OpenAIProviderError("Cloud provider response exceeds the size limit")
            envelope = json.loads(response_bytes.decode("utf-8"))
        except concurrent.futures.TimeoutError:
            raise
        except httpx.TimeoutException as exc:
            # SIM maps this exception type to its explicit `timeout` status.
            raise concurrent.futures.TimeoutError() from exc
        except httpx.HTTPError as exc:
            raise OpenAIProviderError("Cloud provider request failed") from exc
        except OpenAIProviderError:
            raise
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise OpenAIProviderError("Cloud provider returned an invalid response envelope") from exc

        if not isinstance(envelope, dict):
            raise OpenAIProviderError("Cloud provider returned an invalid response envelope")
        if envelope.get("status") == "incomplete":
            return ""
        if envelope.get("status") != "completed":
            raise OpenAIProviderError("Cloud provider returned an invalid response envelope")
        output = envelope.get("output")
        if not isinstance(output, list):
            return ""
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    return part["text"]
        # Refusals and empty model output are passed to SIM as invalid model JSON.
        return ""


def _valid_base_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
            and len(value) <= 300
        )
    except ValueError:
        return False


def resolve_provider(
    settings: Settings | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> ProviderSelection:
    """Return a configured callback, or an explicit unavailable reason."""
    configured = settings or Settings.from_environment()
    timeout = configured.ai_timeout_seconds
    if not math.isfinite(timeout) or timeout <= 0 or timeout > MAX_PROVIDER_TIMEOUT_SECONDS:
        return ProviderSelection(None, None, None, 18.0, "invalid_provider_configuration")
    if not configured.ai_enabled:
        return ProviderSelection(None, None, None, timeout, "provider_disabled")
    if configured.ai_provider != "openai":
        return ProviderSelection(None, None, None, timeout, "unsupported_provider")
    if not configured.ai_api_key:
        return ProviderSelection(None, None, None, timeout, "missing_provider_credentials")
    if not _MODEL_ID.fullmatch(configured.ai_model) or not _valid_base_url(configured.ai_base_url):
        return ProviderSelection(None, None, None, timeout, "invalid_provider_configuration")

    provider = OpenAIResponsesProvider(
        model_id=configured.ai_model,
        base_url=configured.ai_base_url,
        api_key=configured.ai_api_key,
        transport=transport,
    )

    def call_model(*, packet, system_prompt, output_schema, timeout_seconds):
        return provider.structured_json(
            packet=packet,
            system_prompt=system_prompt,
            output_schema=output_schema,
            timeout_seconds=min(timeout, timeout_seconds),
        )

    return ProviderSelection(call_model, "openai", configured.ai_model, timeout)
