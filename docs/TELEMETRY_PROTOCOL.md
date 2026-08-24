# Telemetry Protocol

## Connection

The Kali sender opens a TCP socket to `WINDOWS_HOST:PORT` (default `5003`). The Windows listener binds `LISTENER_IP:PORT` (default `0.0.0.0:5003`). There is no authentication or encryption handshake.

## Framing

Each message is:

```text
4-byte unsigned big-endian payload length
UTF-8 JSON payload of exactly that length
```

The sender uses `struct.pack("!I", len(message_bytes))`. The listener uses `recv_exact` for both header and payload, so TCP fragmentation is handled. There is no maximum length check. A clean close or incomplete payload closes the client; invalid JSON is logged and skipped for the next frame.

## Payloads

All sender payloads include `type`, `hostname`, and UTC `timestamp`. Verified types are `HARDWARE_METRICS` (`cpu`, `ram`, `disk`), `INITIAL_NETWORK_SNAPSHOT` (`network`), `INITIAL_PROCESS_SNAPSHOT` (`process`), `NETWORK_EVENT` (`events_network`, `network`), `PROCESS_EVENT` (`events_process`, `process`), `DOCKER_TELEMETRY` (`containers`, `docker_info`), `DOCKER_EVENT` (`events_docker`), and `HEARTBEAT`.

The listener updates in-memory state for these types, broadcasts a snapshot, and queues hardware/Docker/event/heartbeat persistence where implemented. Unknown types are logged and still reach the final state broadcast.

## Timing and Reconnect

Defaults are hardware loop every 5 seconds, heartbeat every 5 seconds, Docker telemetry every 10 seconds, and reconnect delay 3 seconds. The heartbeat worker is per active connection. The Windows monitor checks every second and marks an online host offline after more than 30 seconds without a parsed heartbeat. Sender connection attempts time out after 10 seconds.

## WebSocket Output

The separate web bridge serializes snapshots as JSON and constructs RFC 6455 unmasked server text frames. It sends targeted heartbeat and HTTP-monitor messages as JSON objects. The snapshot itself has no explicit `type` field; consumers use its shape/default handling. The server does not process client WebSocket frames after upgrade.

## Security and Limits

Telemetry clients are not authenticated, JSON schema validation is not present, payload size is unrestricted, and transport is plaintext. These are implementation limitations, not protocol guarantees.
