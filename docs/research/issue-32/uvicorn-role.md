# FastAPI and plain Uvicorn

Retain direct plain Uvicorn:

```console
uvicorn --factory spice.serving:create_app
```

In lay terms, FastAPI defines what the API does: routes, validation, and
responses. Uvicorn is the network-facing program that listens for HTTP requests
and hands them to that API. FastAPI's official deployment guide calls FastAPI an
ASGI web framework and says it needs an ASGI server program such as Uvicorn;
Uvicorn describes itself as an ASGI web server. FastAPI therefore does **not**
replace Uvicorn. Even `fastapi run` uses Uvicorn internally.
([FastAPI deployment guide](https://fastapi.tiangolo.com/deployment/manually/#asgi-servers),
[FastAPI CLI](https://fastapi.tiangolo.com/fastapi-cli/#fastapi-cli),
[Uvicorn overview](https://www.uvicorn.org/#welcome))

For an exported no-argument `create_app` factory, the direct command is the
smallest documented arrangement. Uvicorn calls its CLI the easiest way to run an
application and documents the exact `uvicorn --factory module:create_app`
pattern: `--factory` calls the named function with no arguments and serves the
ASGI application it returns. No SPICE server wrapper or FastAPI CLI layer adds a
needed role. ([Uvicorn application factories](https://www.uvicorn.org/#application-factories),
[Uvicorn settings](https://www.uvicorn.org/settings/#application))

`uvicorn spice.serving:app` would be shorter only if SPICE chose to export an
already-created module-level application. That changes the approved factory
boundary without removing the server, so it is not a simpler equivalent for
this contract.

Plain `uvicorn` is sufficient. Its official installation installs the minimal
HTTP server and CLI dependencies; `uvicorn[standard]` adds optional acceleration,
reload, WebSocket, and configuration packages. SPICE has no surviving consumer
for those extras. ([Uvicorn installation](https://www.uvicorn.org/installation/))

The short command identifies the application. For the physical Expo phone to
reach the Mac over the private LAN, the operator also supplies the ordinary
socket settings, for example:

```console
uvicorn --factory spice.serving:create_app --host 0.0.0.0 --port 8000
```

Uvicorn documents `127.0.0.1` as the default and `0.0.0.0` as the binding that
makes the application available on the local network.
([Uvicorn socket settings](https://www.uvicorn.org/settings/#socket-binding))
