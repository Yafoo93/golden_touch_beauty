# Application Logging and Error Reporting

Golden Touch uses provider-neutral, structured logging so development works
without a paid service and production can forward the same stdout stream to a
host log collector, Sentry, Datadog, or another approved provider.

## Backend logging

- Every Django request receives an `X-Request-ID` response header. A safe
  caller-supplied ID is preserved; otherwise Django creates a UUID.
- Request logs are one-line JSON with method, path, status, duration, request
  ID, and authenticated user ID. Query strings, bodies, cookies, authorization
  headers, and customer contact details are deliberately omitted.
- Unexpected exceptions include a stack trace in server logs while API clients
  receive only a safe message and the request ID they can quote to support.
- Set `DJANGO_LOG_LEVEL` to `DEBUG`, `INFO`, `WARNING`, or `ERROR`. Production
  should normally use `INFO` and alert on `ERROR`.

## Frontend reporting

- Next.js `onRequestError` writes structured server-rendering failures to
  stdout.
- Route and root error boundaries show a safe recovery screen.
- Browser rendering failures send a short, sanitized report to
  `POST /api/v1/client-errors/`. No stack, form value, cookie, URL query, or
  browser storage is submitted.
- The reporting endpoint uses the standard anonymous API throttle and returns
  `202 Accepted`.

## Production operation

The deployment platform must retain stdout logs, redact infrastructure-level
secrets, alert on repeated `ERROR` entries, and link alerts by `request_id`.
Selecting and configuring a hosted monitoring provider, retention period,
notification destination, and uptime checks remains a launch-stage task.

## Local verification

Start Django and request the health endpoint:

```powershell
curl.exe -i http://127.0.0.1:8000/api/v1/health/
```

The response includes `X-Request-ID`, and the Django terminal prints a JSON
`request_completed` log with the same ID.

Report a simulated browser error:

```powershell
curl.exe -i -X POST http://127.0.0.1:8000/api/v1/client-errors/ -H "Content-Type: application/json" -d '{"name":"TestError","message":"Local observability test","path":"/test"}'
```

The response is `202`, and the Django terminal prints `client_error_reported`.
