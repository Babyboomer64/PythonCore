# TODO – Service Roadmap

## Admin Features
- [X] Implement `/admin/reload-config` to reload queries and CSV configs without restarting the service.
- [X] Implement `/admin/info` to provide service metadata (version, start time, uptime).

## CSV Router
- [ ] Add support for async/background jobs for long-running exports.
- [ ] Provide a download endpoint for generated CSV files.

## Error Handling & Logging
- [ ] Standardize error messages using `config/messages.json` (language catalog).
- [ ] Add logging configuration (JSON-logs, log level via environment).

## Testing
- [ ] Write pytest-based tests for `/csv/export` with SQLite.
- [ ] Add integration tests for config reload functionality.

## Security
- [ ] Add token- or basic-auth protection for sensitive routes.
- [ ] Configure optional CORS support for future frontend integration.

## Frontend Preparation
- [ ] Define use cases for frontend interaction.
- [ ] Identify additional service endpoints needed for frontend support.