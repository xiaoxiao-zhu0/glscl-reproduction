#!/usr/bin/env python3
"""Generate one project image through an OpenAI-compatible image proxy.

Credentials are read from environment variables and are never written to the
project. The adapter accepts either b64_json or URL image responses.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def default_env_file() -> Path:
    override = os.environ.get("ASSET_IMAGE_ENV_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex" / "academic-slide-forge" / "image.env"


def load_env_file(path: Path | None = None) -> None:
    """Load simple KEY=VALUE entries without overriding real environment vars."""
    env_path = path or default_env_file()
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing environment variable: {name}")
    return value


def endpoint_from_env() -> str:
    explicit = os.environ.get("ASSET_IMAGE_ENDPOINT", "").strip()
    if explicit:
        return explicit.rstrip("/")
    base = env_required("ASSET_IMAGE_BASE_URL").rstrip("/")
    if base.endswith("/images/generations"):
        return base
    return base + "/images/generations"


def models_endpoint_from_env() -> str:
    base = os.environ.get("ASSET_IMAGE_BASE_URL", "").strip().rstrip("/")
    if base:
        return base + "/models"
    endpoint = env_required("ASSET_IMAGE_ENDPOINT").rstrip("/")
    suffix = "/images/generations"
    if endpoint.endswith(suffix):
        return endpoint[: -len(suffix)] + "/models"
    raise SystemExit("ASSET_IMAGE_ENDPOINT must end with /images/generations for auto model discovery")


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt and args.prompt_file:
        raise SystemExit("Use either --prompt or --prompt-file, not both")
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    else:
        prompt = (args.prompt or "").strip()
    if not prompt:
        raise SystemExit("A non-empty --prompt or --prompt-file is required")
    return prompt


def reference_endpoint() -> str:
    """Use an explicit edit route, or the conventional sibling of generations."""
    explicit = os.environ.get("ASSET_IMAGE_EDIT_ENDPOINT", "").strip()
    if explicit:
        return explicit.rstrip("/")
    endpoint = endpoint_from_env()
    if endpoint.endswith("/images/generations"):
        return endpoint[:-len("generations")] + "edits"
    raise SystemExit("Reference inputs require ASSET_IMAGE_EDIT_ENDPOINT for this relay")


def resolve_references(rows: list, base: Path) -> list:
    from PIL import Image
    if not isinstance(rows, list):
        raise ValueError("reference_images must be a list")
    resolved = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("path") or not str(row.get("role", "")).strip():
            raise ValueError("Each reference needs path and a nonempty role")
        path = (base / row["path"]).resolve()
        with Image.open(path) as image:
            image.verify()
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("Reference must be a PNG, JPEG or WebP image")
        resolved.append(dict(path=str(path), role=str(row["role"]).strip(),
                             sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return resolved


def conditioned_prompt(prompt: str, references: list) -> str:
    if not references:
        return prompt
    roles = "\n".join(f"Image {i}: {ref['role']}" for i, ref in enumerate(references, 1))
    return "Attached reference roles (in input order):\n" + roles + "\n\n" + prompt


def multipart_payload(payload: dict, references: list) -> tuple[bytes, str]:
    boundary = "slideforge" + uuid.uuid4().hex
    parts = []
    for key, value in payload.items():
        parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n'
                      f'{value}\r\n').encode("utf-8"))
    for i, ref in enumerate(references, 1):
        path = Path(ref["path"])
        # Stable ASCII names avoid Unicode header and path injection problems.
        name = f"reference-{i}{path.suffix.lower()}"
        kind = mimetypes.guess_type(name)[0] or "application/octet-stream"
        parts += [(f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; '
                   f'filename="{name}"\r\nContent-Type: {kind}\r\n\r\n').encode(),
                  path.read_bytes(), b"\r\n"]
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def request_image(endpoint: str, api_key: str, payload: dict, references: list | None = None) -> dict:
    if references:
        body, content_type = multipart_payload(payload, references)
    else:
        body, content_type = json.dumps(payload).encode("utf-8"), "application/json"
    if use_curl():
        raw = curl_request(endpoint, api_key, timeout=180, body=body, content_type=content_type)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit("Image proxy returned non-JSON data") from exc
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
            "Accept": "application/json",
            "User-Agent": "academic-slide-forge/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Image proxy HTTP {exc.code}; provider details withheld; no automatic retry") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Image proxy connection failed: {exc.reason}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit("Image proxy returned non-JSON data") from exc


def request_models(endpoint: str, api_key: str) -> dict:
    if use_curl():
        try:
            return json.loads(curl_request(endpoint, api_key, timeout=60).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit("Image model discovery returned non-JSON data") from exc
    req = urllib.request.Request(
        endpoint,
        method="GET",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "academic-slide-forge/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Image model discovery HTTP {exc.code}; set ASSET_IMAGE_MODEL explicitly") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise SystemExit("Image model discovery failed; set ASSET_IMAGE_MODEL explicitly") from exc


def use_curl() -> bool:
    """Use Windows' verified TLS stack before sending a request, never as a retry."""
    transport = os.environ.get("ASSET_IMAGE_HTTP_TRANSPORT", "auto").strip().lower()
    if transport not in {"auto", "curl", "urllib"}:
        raise SystemExit("ASSET_IMAGE_HTTP_TRANSPORT must be auto, curl, or urllib")
    available = bool(shutil.which("curl.exe" if os.name == "nt" else "curl"))
    if transport == "curl" and not available:
        raise SystemExit("curl transport requested but curl is unavailable")
    return transport == "curl" or (transport == "auto" and os.name == "nt" and available)


def curl_request(endpoint: str, api_key: str = "", payload: dict | None = None,
                 timeout: int = 180, *, body: bytes | None = None,
                 content_type: str = "application/json") -> bytes:
    """Keep credentials off command lines/files; verify TLS and do not retry POSTs."""
    if api_key and any(c in api_key for c in "\r\n"):
        raise SystemExit("Image API key contains an invalid newline")
    config = ["url = " + json.dumps(endpoint, ensure_ascii=False),
              'header = "Accept: application/json"',
              'user-agent = "academic-slide-forge/1.0"']
    if api_key:
        config.append("header = " + json.dumps("Authorization: Bearer " + api_key))
    proxy = os.environ.get("ASSET_IMAGE_HTTP_PROXY", "").strip()
    if proxy:
        config.append("proxy = " + json.dumps(proxy, ensure_ascii=False))
    if payload is not None:
        config += ['header = "Content-Type: application/json"',
                   "data-binary = " + json.dumps(json.dumps(payload, ensure_ascii=False), ensure_ascii=False)]
    body_path = None
    if body is not None:
        with tempfile.NamedTemporaryFile(prefix="slideforge-body-", suffix=".bin", delete=False) as handle:
            handle.write(body)
            body_path = Path(handle.name)
        config += ["header = " + json.dumps("Content-Type: " + content_type),
                   "data-binary = " + json.dumps("@" + str(body_path))]
    executable = "curl.exe" if os.name == "nt" else "curl"
    command = [executable, "--disable", "--config", "-", "--silent", "--show-error",
               "--proto", "=http,https", "--max-time", str(timeout),
               "--retry", "0", "--write-out", "\n%{http_code}"]
    try:
        completed = subprocess.run(command, input=("\n".join(config) + "\n").encode("utf-8"),
                                   capture_output=True, timeout=timeout + 10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit("Image HTTP transport failed; remote completion unknown; no automatic retry") from exc
    finally:
        if body_path:
            body_path.unlink(missing_ok=True)
    if completed.returncode:
        raise SystemExit(f"Image HTTP transport failed (curl {completed.returncode}); "
                         "remote completion unknown; no automatic retry")
    raw, separator, status = completed.stdout.rpartition(b"\n")
    if not separator or not status.isdigit():
        raise SystemExit("Image HTTP transport returned no status code")
    if not 200 <= int(status) < 300:
        raise SystemExit(f"Image proxy HTTP {int(status)}; provider details withheld; no automatic retry")
    return raw


def discover_image_model(api_key: str) -> str:
    response = request_models(models_endpoint_from_env(), api_key)
    rows = response.get("data") if isinstance(response, dict) else None
    if not isinstance(rows, list):
        raise SystemExit("Image model discovery returned no data; set ASSET_IMAGE_MODEL explicitly")

    candidates = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("id") or row.get("name") or "").strip()
        marker = str(row.get("type") or row.get("capabilities") or "").lower()
        lowered = name.lower()
        if name and ("image" in lowered or "dall" in lowered or "image" in marker):
            numbers = tuple(float(part) for part in re.findall(r"\d+(?:\.\d+)?", name))
            created = int(row.get("created") or 0)
            candidates.append((numbers, created, name))
    if not candidates:
        raise SystemExit("No image model was exposed by the relay; set ASSET_IMAGE_MODEL explicitly")
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return candidates[-1][2]


def first_image_record(response: dict) -> dict:
    data = response.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    # A few OpenAI-compatible relays wrap the normal response.
    result = response.get("result")
    if isinstance(result, dict):
        data = result.get("data")
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
    raise SystemExit("Image proxy response has no data[0] image record")


def save_record(record: dict, output: Path) -> None:
    b64 = record.get("b64_json") or record.get("base64")
    if b64:
        try:
            output.write_bytes(base64.b64decode(b64))
            return
        except Exception as exc:  # pragma: no cover - provider-specific payload
            raise SystemExit(f"Image base64 payload could not be decoded: {exc}") from exc

    url = record.get("url") or record.get("image_url")
    if url:
        if use_curl():
            output.write_bytes(curl_request(url))
            return
        try:
            with urllib.request.urlopen(url, timeout=180) as response:
                output.write_bytes(response.read())
            return
        except urllib.error.URLError as exc:
            raise SystemExit(f"Generated image could not be downloaded: {exc.reason}") from exc

    raise SystemExit("Image record has neither b64_json nor url")


def write_metadata(output: Path, prompt: str, endpoint: str, payload: dict,
                   references: list | None = None) -> None:
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    metadata = {
        "prompt": prompt,
        "endpoint_host": urllib.parse.urlparse(endpoint).netloc,
        "endpoint_path": urllib.parse.urlparse(endpoint).path,
        "input_mode": "reference-conditioned" if references else "text-only",
        "reference_images": references or [],
        "model": payload.get("model"),
        "size": payload.get("size"),
        "quality": payload.get("quality"),
        "http_transport": "curl" if use_curl() else "urllib",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sha256": digest,
    }
    output.with_suffix(output.suffix + ".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--output", required=True)
    parser.add_argument("--env-file")
    parser.add_argument("--model")
    parser.add_argument("--size")
    parser.add_argument("--quality")
    parser.add_argument("--references-json", type=Path,
                        help="JSON list of {path, role}; images sent as multipart to edit endpoint")
    args = parser.parse_args()

    load_env_file(Path(args.env_file) if args.env_file else default_env_file())

    prompt = read_prompt(args)
    api_key = env_required("ASSET_IMAGE_API_KEY")
    requested_model = (args.model or os.environ.get("ASSET_IMAGE_MODEL", "auto")).strip()
    if requested_model.lower() in {"auto", "latest"}:
        try:
            model = discover_image_model(api_key)
        except SystemExit:
            fallback = os.environ.get("ASSET_IMAGE_FALLBACK_MODEL", "").strip()
            if not fallback:
                raise
            model = fallback
    else:
        model = requested_model
    size = (args.size or os.environ.get("ASSET_IMAGE_SIZE", "1536x1024")).strip()
    quality = (args.quality or os.environ.get("ASSET_IMAGE_QUALITY", "")).strip()
    references = []
    if args.references_json:
        references = resolve_references(json.loads(args.references_json.read_text(encoding="utf-8")),
                                        args.references_json.resolve().parent)
    endpoint = reference_endpoint() if references else endpoint_from_env()

    payload = {
        "prompt": conditioned_prompt(prompt, references),
        "n": 1,
        "size": size,
        "response_format": "b64_json",
    }
    if model:
        payload["model"] = model
    if quality:
        payload["quality"] = quality

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    record = first_image_record(request_image(endpoint, api_key, payload, references))
    save_record(record, output)
    write_metadata(output, prompt, endpoint, payload, references)
    print(f"Saved image: {output}")
    print(f"Saved metadata: {output.with_suffix(output.suffix + '.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
