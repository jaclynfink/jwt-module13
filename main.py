# main.py

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator  # Use @validator for Pydantic 1.x
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models.calculation import Calculation
from app.models.user import User
from app.operations.factory import CalculationFactory
from app.operations import add, subtract, multiply, divide  # Ensure correct import path
from app.schemas.calculation import CalculationCreate, CalculationRead
from app.schemas.user import UserCreate, UserLogin, UserLoginResponse, UserRead
from app.security import hash_password, verify_password
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
def startup_event() -> None:
    """Create database tables when the app starts."""
    init_db()

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Pydantic model for request data
class OperationRequest(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")

    @field_validator('a', 'b')  # Correct decorator for Pydantic 1.x
    def validate_numbers(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError('Both a and b must be numbers.')
        return value

# Pydantic model for successful response
class OperationResponse(BaseModel):
    result: float = Field(..., description="The result of the operation")

# Pydantic model for error response
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")

# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extracting error messages
    error_messages = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(
        status_code=400,
        content={"error": error_messages},
    )

@app.get("/")
async def read_root(request: Request):
    """
    Serve the index.html template.
    """
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest):
    """
    Add two numbers.
    """
    try:
        result = add(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Add Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    """
    Subtract two numbers.
    """
    try:
        result = subtract(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Subtract Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    """
    Multiply two numbers.
    """
    try:
        result = multiply(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Multiply Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    """
    Divide two numbers.
    """
    try:
        result = divide(operation.a, operation.b)
        return OperationResponse(result=result)
    except ValueError as e:
        logger.error(f"Divide Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/users/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user using hashed password storage."""
    duplicate_username = db.query(User).filter(User.username == payload.username).first()
    if duplicate_username:
        raise HTTPException(status_code=409, detail="Username already exists.")

    duplicate_email = db.query(User).filter(User.email == payload.email).first()
    if duplicate_email:
        raise HTTPException(status_code=409, detail="Email already exists.")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.error("Registration integrity error: %s", exc)
        raise HTTPException(status_code=409, detail="User already exists.") from exc

    db.refresh(user)
    return user


@app.post("/users/login", response_model=UserLoginResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user by validating the password against the stored hash."""
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    return UserLoginResponse(message="Login successful.", user=UserRead.model_validate(user))


@app.get("/calculations", response_model=list[CalculationRead])
def browse_calculations(db: Session = Depends(get_db)):
    """Browse all persisted calculations."""
    return db.query(Calculation).order_by(Calculation.id.asc()).all()


@app.get("/calculations/{calculation_id}", response_model=CalculationRead)
def read_calculation(calculation_id: int, db: Session = Depends(get_db)):
    """Read a single calculation by id."""
    calculation = db.get(Calculation, calculation_id)
    if calculation is None:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    return calculation


@app.post("/calculations", response_model=CalculationRead, status_code=status.HTTP_201_CREATED)
def add_calculation(payload: CalculationCreate, db: Session = Depends(get_db)):
    """Add a new calculation record."""
    result = payload.result
    if result is None:
        result = CalculationFactory.calculate(payload.type.value, payload.a, payload.b)

    calculation = Calculation(
        a=payload.a,
        b=payload.b,
        type=payload.type.value,
        result=result,
        user_id=payload.user_id,
    )
    db.add(calculation)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create calculation.") from exc

    db.refresh(calculation)
    return calculation


@app.put("/calculations/{calculation_id}", response_model=CalculationRead)
def edit_calculation(calculation_id: int, payload: CalculationCreate, db: Session = Depends(get_db)):
    """Edit an existing calculation record using replacement payload data."""
    calculation = db.get(Calculation, calculation_id)
    if calculation is None:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    result = payload.result
    if result is None:
        result = CalculationFactory.calculate(payload.type.value, payload.a, payload.b)

    calculation.a = payload.a
    calculation.b = payload.b
    calculation.type = payload.type.value
    calculation.result = result
    calculation.user_id = payload.user_id

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to update calculation.") from exc

    db.refresh(calculation)
    return calculation


@app.delete("/calculations/{calculation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calculation(calculation_id: int, db: Session = Depends(get_db)):
    """Delete a calculation by id."""
    calculation = db.get(Calculation, calculation_id)
    if calculation is None:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    db.delete(calculation)
    db.commit()
    return None

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
