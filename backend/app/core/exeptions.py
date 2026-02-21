from fastapi.exceptions import RequestValidationError
from fastapi import status, Request, FastAPI
from fastapi.responses import JSONResponse


# Override Pydantic's exeption handler.
def setup_exeption_handler(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": error["loc"][-1],  # Field Name (example: "email")
                    "type": error["type"],  # Error type (example" "missing")
                    "ctx": error.get("ctx", {}),  # Context (limits, etc.)
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"success": False, "errors": errors},
        )
