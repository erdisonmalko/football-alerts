from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def format_field(loc: tuple) -> str:
    parts = [str(x) for x in loc if x not in ("body", "query", "path")]
    return ".".join(parts)


def unique(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}

    for err in exc.errors():
        field = format_field(err["loc"])

        if field not in errors:
            errors[field] = []

        msg = err["msg"]

        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")

        if msg != "Value error":
            errors[field].append(msg)

    return JSONResponse(
        status_code=422, content={"errors": {f: unique(errors[f]) for f in errors}}
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content={"errors": exc.detail},
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"errors": {"general": [str(exc.detail)]}},
    )
