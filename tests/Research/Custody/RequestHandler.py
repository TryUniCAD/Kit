from http.server import BaseHTTPRequestHandler as HttpHandler


# the server receives the actual encoded request and returns the status assigned to that attempt
def RequestHandler(
    Statuses: tuple[int, ...], Content: bytes, Requests: list[str]
) -> type[HttpHandler]:

    # scripted responses distinguish recovery from permanent refusal and retry exhaustion
    def SendFixtureMut(Handler: HttpHandler) -> None:
        Status = Statuses[len(Requests)] if len(Requests) < len(Statuses) else 500
        Requests.append(Handler.path)
        Handler.send_response(Status)
        Payload = Content if Status == 200 else b""
        Handler.send_header("Content-Length", str(len(Payload)))
        Handler.end_headers()
        _ = Handler.wfile.write(Payload)

    return type("FixtureResponse", (HttpHandler,), {"do_GET": SendFixtureMut})
