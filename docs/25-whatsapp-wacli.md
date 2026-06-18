# WhatsApp Customer Gateway via wacli

Wasila supports WhatsApp customer conversations through the `wacli` customer gateway.

## Local config

Keep customer and owner gateways configured separately:

```toml
[gateways.customer]
type = "wacli"
command = "wacli"

[gateways.owner]
type = "webhook"
```

Use `command` when the binary is not named `wacli` or needs fixed flags:

```toml
[gateways.customer]
type = "wacli"
command = "/usr/local/bin/wacli --profile bisnis"
```

## Inbound payload

The gateway normalizes a local payload into `CustomerEvent`:

```json
{
  "id": "wamid.1",
  "from": "+628123",
  "text": "Halo Wasila",
  "timestamp": "2026-06-18T11:00:00Z"
}
```

Accepted conversation keys: `chat_id`, `from`, or `phone`.
Accepted message keys: `text`, `message`, or `body`.

## Reply delivery

When the daemon produces `customer_response`, the gateway runs:

```bash
wacli send <chat_id> <text>
```

The subprocess wrapper is intentionally boring: no shell, bounded timeout, captured stderr, and runtime errors for failed, timed out, or missing commands.

## Limitations

- This adapter assumes `wacli` is already installed, logged in, and able to send messages.
- Wasila does not own WhatsApp session storage; keep it outside committed files.
- Owner notifications stay on the configured owner gateway and do not reuse the customer WhatsApp channel.
