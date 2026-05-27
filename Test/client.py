"""
MCP Client with Google OAuth Authentication
Handles browser-based Google login, persists tokens to disk,
and calls tools on the protected MCP server.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Mapping

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import OAuth

load_dotenv()

# ── File-backed AsyncKeyValue store ──────────────────────────────────────────
# FastMCP's OAuth client needs an AsyncKeyValue-compatible token store.
# The built-in MemoryStore loses tokens on restart.
# This stores everything in a local JSON file instead.

class FileKeyValueStore:
    """
    Implements the AsyncKeyValue protocol backed by a local JSON file.

    Structure on disk:
    {
      "collection_name": {
        "key": {
          "value": { ...dict... },
          "expires_at": 1234567890.0   # optional unix timestamp
        }
      }
    }
    """

    def __init__(self, path: str = ".oauth_tokens.json"):
        self._path = Path(path)
        self._data: dict[str, dict] = self._load()

    # ── Disk I/O ──────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        self._path.write_text(
            json.dumps(self._data, indent=2),
            encoding="utf-8"
        )

    def _get_collection(self, collection: str | None) -> dict:
        key = collection or "_default"
        if key not in self._data:
            self._data[key] = {}
        return self._data[key]

    def _is_expired(self, entry: dict) -> bool:
        expires_at = entry.get("expires_at")
        return expires_at is not None and time.time() > expires_at

    # ── AsyncKeyValue protocol ────────────────────────────────────────────────

    async def get(
        self,
        key: str,
        *,
        collection: str | None = None,
    ) -> dict[str, Any] | None:
        col = self._get_collection(collection)
        entry = col.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            del col[key]
            self._save()
            return None
        return entry["value"]

    async def put(
        self,
        key: str,
        value: Mapping[str, Any],
        *,
        collection: str | None = None,
        ttl: float | None = None,
    ) -> None:
        col = self._get_collection(collection)
        entry: dict = {"value": dict(value)}
        if ttl is not None:
            entry["expires_at"] = time.time() + float(ttl)
        col[key] = entry
        self._save()

    async def delete(
        self,
        key: str,
        *,
        collection: str | None = None,
    ) -> bool:
        col = self._get_collection(collection)
        if key in col:
            del col[key]
            self._save()
            return True
        return False

    async def ttl(
        self,
        key: str,
        *,
        collection: str | None = None,
    ) -> tuple[dict[str, Any] | None, float | None]:
        col = self._get_collection(collection)
        entry = col.get(key)
        if entry is None or self._is_expired(entry):
            return None, None
        value = entry["value"]
        expires_at = entry.get("expires_at")
        remaining = (expires_at - time.time()) if expires_at else None
        return value, remaining

    # ── Bulk operations (required by protocol) ────────────────────────────────

    async def get_many(
        self,
        keys: list[str],
        *,
        collection: str | None = None,
    ) -> dict[str, dict[str, Any] | None]:
        return {k: await self.get(k, collection=collection) for k in keys}

    async def put_many(
        self,
        items: Mapping[str, Mapping[str, Any]],
        *,
        collection: str | None = None,
        ttl: float | None = None,
    ) -> None:
        for key, value in items.items():
            await self.put(key, value, collection=collection, ttl=ttl)

    async def delete_many(
        self,
        keys: list[str],
        *,
        collection: str | None = None,
    ) -> dict[str, bool]:
        return {k: await self.delete(k, collection=collection) for k in keys}

    async def ttl_many(
        self,
        keys: list[str],
        *,
        collection: str | None = None,
    ) -> dict[str, tuple[dict[str, Any] | None, float | None]]:
        return {k: await self.ttl(k, collection=collection) for k in keys}


# ── Main ──────────────────────────────────────────────────────────────────────

SERVER_URL = "http://127.0.0.1:8000/mcp"

async def main():
    print("=" * 50)
    print("  MCP Client — Google OAuth")
    print("=" * 50)

    # Tokens persist across restarts — no re-login unless expired
    token_storage = FileKeyValueStore(".oauth_tokens.json")

    auth = OAuth(
        mcp_url=SERVER_URL,
        client_name="My MCP Client",
        token_storage=token_storage,
        scopes=["openid", "email", "profile"],
    )

    async with Client(SERVER_URL, auth=auth) as client:
        print("\n✅ Connected & authenticated\n")

        # List tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}\n")

        # Call public tool
        print("→ Calling hello() ...")
        result = await client.call_tool("hello", {})
        print(f"  {result[0].text}\n")

        # Call protected tool
        print("→ Calling get_secure_data() ...")
        result = await client.call_tool("get_secure_data", {})
        print(f"  {result[0].text}\n")


if __name__ == "__main__":
    asyncio.run(main())