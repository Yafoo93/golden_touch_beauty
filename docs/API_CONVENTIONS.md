# API Conventions

## Versioning

Application endpoints use the `/api/v1/` prefix. API documentation remains available through `/api/schema/`, `/api/docs/`, and `/api/redoc/`.

## Error response format

Every REST API failure returns JSON with one stable envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Some submitted information is invalid.",
    "status": 400,
    "details": {
      "email": ["This field is required."]
    }
  }
}
```

Fields:

- `code`: stable machine-readable value used by the frontend.
- `message`: safe summary suitable for displaying to a user.
- `status`: HTTP status code repeated for convenient client handling.
- `details`: field-level or exception-specific information; an empty object when no safe details are available.

Common codes include:

| HTTP status | Code | Meaning |
| ---: | --- | --- |
| 400 | `validation_error` | Submitted fields failed validation. |
| 400 | `invalid_json` | The request body is not valid JSON. |
| 401/403 | `not_authenticated` | A valid login session is required. |
| 403 | `permission_denied` | The user is logged in but lacks permission. |
| 404 | `not_found` | The resource or API endpoint does not exist. |
| 405 | `method_not_allowed` | The endpoint does not support that HTTP method. |
| 409 | `conflict` | The request conflicts with current resource state. |
| 415 | `unsupported_media_type` | The request content type is unsupported. |
| 422 | `business_rule_violation` | Valid fields violate an application business rule. |
| 429 | `rate_limited` | The caller exceeded a request limit. |
| 500 | `server_error` | An unexpected internal error occurred. |

Unexpected errors are logged on the server with diagnostic context, while the response hides exception messages and sensitive implementation details.

## Frontend handling

Use `apiFetch` from `frontend/src/lib/api.ts`. It includes browser session cookies and throws `ApiError` for non-successful responses:

```ts
try {
  const result = await apiFetch<Result>("example/");
} catch (error) {
  if (error instanceof ApiError) {
    console.log(error.code, error.message, error.details);
  }
}
```

Form pages should use `error.details` for field-level messages and `error.message` for the page-level alert. They should not implement separate parsing rules for individual endpoints.
