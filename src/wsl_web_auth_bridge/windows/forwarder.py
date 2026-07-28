from __future__ import annotations

import asyncio
import contextlib
import logging

logger = logging.getLogger(__name__)


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, label: str) -> int:
    total = 0
    try:
        while True:
            chunk = await reader.read(65536)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()
            total += len(chunk)
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        pass
    finally:
        with contextlib.suppress(Exception):
            writer.close()
            await writer.wait_closed()
    logger.debug("%s forwarded %s bytes", label, total)
    return total


async def relay_tcp(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    target_host: str,
    target_port: int,
) -> int:
    remote_reader, remote_writer = await asyncio.open_connection(target_host, target_port)
    client_addr = client_writer.get_extra_info("peername")
    logger.info("Callback connection from %s → %s:%s", client_addr, target_host, target_port)

    upstream = asyncio.create_task(pipe(client_reader, remote_writer, "client→wsl"))
    downstream = asyncio.create_task(pipe(remote_reader, client_writer, "wsl→client"))
    results = await asyncio.gather(upstream, downstream, return_exceptions=True)
    return sum(r for r in results if isinstance(r, int))


async def run_listener(
    *,
    listen_host: str,
    listen_port: int,
    target_host: str,
    target_port: int,
    stop_event: asyncio.Event,
) -> int:
    server = await asyncio.start_server(
        lambda r, w: relay_tcp(r, w, target_host, target_port),
        host=listen_host,
        port=listen_port,
        reuse_address=True,
    )
    logger.info(
        "Forwarding %s:%s → %s:%s",
        listen_host,
        listen_port,
        target_host,
        target_port,
    )

    async def _serve() -> None:
        async with server:
            await server.serve_forever()

    task = asyncio.create_task(_serve())
    try:
        await stop_event.wait()
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        server.close()
        await server.wait_closed()
    return 0
