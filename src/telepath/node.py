"""Signed request/response peer with vault sessions and real shard transfer."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import time
from pathlib import Path
from ssl import SSLContext

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from vault.access import NonceCache

from . import protocol as protocol
from .cache import ShardCache
from .reputation import Reputation
from .session import SessionRegistry
from .tiers import TierRegistry
from .transport import recv_frame, send_frame


class TelepathNode:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7788,
        name: str = "node",
        *,
        key: Ed25519PrivateKey | None = None,
        receipts=None,
        vault_store=None,
        vault_acl=None,
        ssl_context: SSLContext | None = None,
    ):
        self.host = host
        self.port = port
        self.name = name
        self.key = key or Ed25519PrivateKey.generate()
        self.pub = self.key.public_key().public_bytes_raw().hex()
        self.receipts = receipts
        self.vault_store = vault_store
        self.vault_acl = vault_acl
        self.ssl_context = ssl_context
        self.sessions = SessionRegistry()
        self.cache = ShardCache()
        self.reputation = Reputation()
        self.tiers = TierRegistry()
        self.nonces = NonceCache()
        self.peers: dict[str, tuple[str, int]] = {}
        self.peer_info: dict[str, dict] = {}
        self.server: asyncio.AbstractServer | None = None

    def _receipt(self, kind: str, model_id: str, actor: str, payload: dict) -> None:
        if self.receipts is not None:
            self.receipts.emit(kind, model_id, actor, payload)

    def _reply(self, kind: str, payload: dict | None = None) -> protocol.Message:
        return protocol.make(kind, self.key, payload)

    async def start(self) -> None:
        self.server = await asyncio.start_server(
            self._handle_connection, self.host, self.port, ssl=self.ssl_context
        )
        sockets = self.server.sockets or []
        if sockets and self.port == 0:
            self.port = int(sockets[0].getsockname()[1])

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            message = protocol.Message.from_dict(await recv_frame(reader))
            ok, reason = protocol.verify(message)
            if not ok:
                response = self._reply(protocol.ERROR, {"reason": reason})
            elif not self.nonces.accept(message.sender, message.nonce):
                response = self._reply(protocol.ERROR, {"reason": "replayed nonce"})
            else:
                peer = writer.get_extra_info("peername")
                peer_ip = str(peer[0]) if peer else "127.0.0.1"
                response = await self._dispatch(message, peer_ip)
            response.payload["request_nonce"] = message.nonce
            response.sign(self.key)
            await send_frame(writer, response.to_dict())
        except (asyncio.IncompleteReadError, ConnectionError, KeyError, TypeError, ValueError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass

    async def _dispatch(self, message: protocol.Message, peer_ip: str) -> protocol.Message:
        if message.type == protocol.HELLO:
            advertised_port = int(message.payload.get("port", 0))
            if 0 < advertised_port < 65536:
                self.peers[message.sender] = (peer_ip, advertised_port)
                self.peer_info[message.sender] = message.payload
            return self._reply(
                protocol.HELLO,
                {"name": self.name, "port": self.port, "capabilities": self.capabilities()},
            )
        if message.type == protocol.SESSION_OPEN:
            return self._open_session(message)
        if message.type == protocol.REQUEST_SHARD:
            return self._serve_shard(message)
        if message.type == protocol.RAM_BROADCAST:
            key = str(message.payload.get("key", "state"))
            size = int(message.payload.get("size_bytes", 0))
            self.tiers.touch(key, size, f"ram://{message.sender[:8]}")
            self._receipt("telepath.ram_recv", "-", message.sender, {"key": key, "bytes": size})
            return self._reply(protocol.ACK, {"received": key})
        return self._reply(protocol.ERROR, {"reason": f"unsupported message: {message.type}"})

    def _open_session(self, message: protocol.Message) -> protocol.Message:
        model_id = str(message.payload.get("model_id", ""))
        if self.vault_store is None:
            return self._reply(protocol.SESSION_DENY, {"model_id": model_id, "reason": "no vault"})
        manifest = self.vault_store.get_manifest(model_id)
        if manifest is None:
            return self._reply(protocol.SESSION_DENY, {"model_id": model_id, "reason": "not found"})
        if self.vault_acl is not None and not self.vault_acl.is_allowed(model_id, message.sender):
            self.reputation.record(message.sender, "denied")
            return self._reply(
                protocol.SESSION_DENY, {"model_id": model_id, "reason": "ACL denied"}
            )
        try:
            session = self.sessions.open(
                message.sender,
                model_id,
                str(message.payload.get("purpose", "read")),
                int(message.payload.get("budget_shards", manifest.n_shards)),
                float(message.payload.get("ttl_s", 600)),
            )
        except ValueError as exc:
            return self._reply(protocol.SESSION_DENY, {"model_id": model_id, "reason": str(exc)})
        self._receipt(
            "telepath.session_open",
            model_id,
            message.sender,
            {"session_id": session.session_id, "budget": session.budget_shards},
        )
        return self._reply(
            protocol.SESSION_ACCEPT,
            {
                "session_id": session.session_id,
                "model_id": model_id,
                "n_shards": manifest.n_shards,
                "size_bytes": manifest.size_bytes,
                "merkle_root": manifest.merkle_root,
                "file_sha256": manifest.metadata.get("file_sha256"),
            },
        )

    def _serve_shard(self, message: protocol.Message) -> protocol.Message:
        session = self.sessions.get(str(message.payload.get("session_id", "")))
        index = int(message.payload.get("shard_idx", -1))
        if session is None or session.peer_pub != message.sender or not session.consume():
            self.reputation.record(message.sender, "denied")
            return self._reply(
                protocol.SHARD_DENY,
                {"shard_idx": index, "reason": "invalid, expired, or exhausted session"},
            )
        manifest = self.vault_store.get_manifest(session.model_id)
        started = time.monotonic()
        try:
            data = self.vault_store.read_shard_plaintext(manifest, index)
        except (IndexError, RuntimeError, OSError, ValueError):
            self.reputation.record(message.sender, "failed")
            return self._reply(
                protocol.SHARD_DENY, {"shard_idx": index, "reason": "shard unavailable"}
            )
        latency = (time.monotonic() - started) * 1000
        self.reputation.record(message.sender, "success", len(data), latency, inbound=False)
        self._receipt(
            "telepath.shard_served",
            session.model_id,
            message.sender,
            {"shard_idx": index, "bytes": len(data), "session_id": session.session_id},
        )
        return self._reply(
            protocol.SHARD_DATA,
            {
                "model_id": session.model_id,
                "shard_idx": index,
                "plaintext_hash": hashlib.sha256(data).hexdigest(),
                "payload_b64": base64.b64encode(data).decode(),
            },
        )

    def capabilities(self) -> list[str]:
        return ["signed-tcp", "session", "shard", *(["vault"] if self.vault_store else [])]

    async def _request(
        self,
        host: str,
        port: int,
        message: protocol.Message,
        timeout: float = 30,
        expected_sender: str | None = None,
    ) -> protocol.Message:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=self.ssl_context), timeout=timeout
        )
        try:
            await send_frame(writer, message.to_dict())
            response = protocol.Message.from_dict(
                await asyncio.wait_for(recv_frame(reader), timeout)
            )
            ok, reason = protocol.verify(response)
            if not ok:
                raise RuntimeError(f"invalid peer response: {reason}")
            if expected_sender is not None and response.sender != expected_sender:
                raise RuntimeError("response was signed by an unexpected peer")
            if response.payload.get("request_nonce") != message.nonce:
                raise RuntimeError("response is not bound to this request")
            return response
        finally:
            writer.close()
            await writer.wait_closed()

    async def connect(self, host: str, port: int) -> str:
        response = await self._request(
            host,
            port,
            protocol.make(
                protocol.HELLO,
                self.key,
                {"name": self.name, "port": self.port, "capabilities": self.capabilities()},
            ),
        )
        if response.type != protocol.HELLO:
            raise RuntimeError(response.payload.get("reason", "HELLO rejected"))
        self.peers[response.sender] = (host, port)
        self.peer_info[response.sender] = response.payload
        return response.sender

    async def open_session(
        self, peer: str, model_id: str, budget_shards: int, ttl_s: float = 600
    ) -> dict:
        host, port = self.peers[peer]
        response = await self._request(
            host,
            port,
            protocol.make(
                protocol.SESSION_OPEN,
                self.key,
                {
                    "model_id": model_id,
                    "purpose": "pull",
                    "budget_shards": budget_shards,
                    "ttl_s": ttl_s,
                },
            ),
            expected_sender=peer,
        )
        if response.type != protocol.SESSION_ACCEPT:
            self.reputation.record(peer, "denied")
            raise PermissionError(response.payload.get("reason", "session denied"))
        return response.payload

    async def fetch_shard(self, peer: str, model_id: str, session_id: str, index: int) -> bytes:
        cache_key = (peer, model_id, index)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        host, port = self.peers[peer]
        started = time.monotonic()
        response = await self._request(
            host,
            port,
            protocol.make(
                protocol.REQUEST_SHARD, self.key, {"session_id": session_id, "shard_idx": index}
            ),
            expected_sender=peer,
        )
        if response.type != protocol.SHARD_DATA:
            self.reputation.record(peer, "denied")
            raise RuntimeError(response.payload.get("reason", "shard denied"))
        data = base64.b64decode(response.payload["payload_b64"], validate=True)
        if hashlib.sha256(data).hexdigest() != response.payload["plaintext_hash"]:
            self.reputation.record(peer, "failed")
            raise RuntimeError("transferred shard hash mismatch")
        latency = (time.monotonic() - started) * 1000
        self.reputation.record(peer, "success", len(data), latency)
        self.cache.put(cache_key, data)
        self.tiers.touch(f"{model_id}#{index}", len(data), f"ram://{self.pub[:8]}")
        self._receipt(
            "telepath.shard_received", model_id, peer, {"shard_idx": index, "bytes": len(data)}
        )
        return data

    async def pull_model(self, peer: str, model_id: str, destination: str | Path) -> dict:
        initial = await self.open_session(peer, model_id, budget_shards=1_000_000, ttl_s=3600)
        target = Path(destination) / model_id.replace("/", "__") / "model.bin"
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".part")
        digest = hashlib.sha256()
        total = 0
        try:
            with temporary.open("wb") as handle:
                for index in range(int(initial["n_shards"])):
                    chunk = await self.fetch_shard(peer, model_id, initial["session_id"], index)
                    handle.write(chunk)
                    digest.update(chunk)
                    total += len(chunk)
            expected = initial.get("file_sha256")
            if expected and digest.hexdigest() != expected:
                raise RuntimeError("reassembled model hash mismatch")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        self._receipt(
            "telepath.model_pulled", model_id, peer, {"bytes": total, "path": str(target)}
        )
        return {"model_id": model_id, "path": str(target), "bytes": total, **initial}

    async def broadcast_ram(self, key: str, size_bytes: int) -> None:
        message = protocol.make(
            protocol.RAM_BROADCAST, self.key, {"key": key, "size_bytes": size_bytes}
        )
        for peer, (host, port) in self.peers.items():
            await self._request(host, port, message, expected_sender=peer)

    def state(self) -> dict:
        return {
            "name": self.name,
            "pub": self.pub,
            "listen": f"{self.host}:{self.port}",
            "peers": [key for key in self.peers],
            "cache": self.cache.summary(),
            "sessions": self.sessions.summary(),
            "tiers": self.tiers.summary(),
            "reputation": self.reputation.summary(),
        }
