from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.auth.schemas import EmailRegDTO, EmailAuthDTO
from app.modules.auth.models import User
from app.core.security import get_password_hash, verify_password, create_access_token


# Auth with email and password.
async def auth(dto: EmailAuthDTO, db: AsyncSession):
    stmt = select(User).where(User.email == dto.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not verify_password(dto.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")

    access_token = create_access_token(data={"sub": user.email, "id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


# Register with email and password.
async def register(dto: EmailRegDTO, db: AsyncSession):
    if dto.password != dto.repassword:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    stmt = select(User).where(User.email == dto.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(dto.password)
    new_user = User(email=dto.email, hashed_password=hashed_password)

    db.add(new_user)
    await db.commit()
    # await db.refresh(new_user)

    return {"message": "User registered successfully"}
