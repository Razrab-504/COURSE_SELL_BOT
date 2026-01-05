from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.users import User


async def get_user_by_telegram(db: AsyncSession, telegram_id: int) -> User | None:
    query = select(User).where(User.telegram_user_id == telegram_id)
    res = await db.execute(query)
    return res.scalar_one_or_none()


async def create_user(db: AsyncSession, telegram_id: int, first_name: str | None = None, last_name: str | None = "") -> User:
    user = User(telegram_user_id=telegram_id, first_name=first_name, last_name=last_name or "")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_user(db: AsyncSession, telegram_user) -> User:
    user = await get_user_by_telegram(db, telegram_user.id)
    if user:
        return user
    return await create_user(db, telegram_user.id, telegram_user.first_name, getattr(telegram_user, "last_name", ""))


async def count_users(db: AsyncSession) -> int:
    query = select(User)
    res = await db.execute(query)
    return len(res.scalars().all())

async def get_users_paginated(db: AsyncSession, offset: int = 0, limit: int = 10):
    query = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()

async def set_user_ban(db: AsyncSession, user_id: int, is_banned: bool):
    user = await db.get(User, user_id)
    if not user:
        return None
    user.is_banned = is_banned
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
