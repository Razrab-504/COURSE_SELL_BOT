from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.purchases import Purchases
from src.db.enums import Status
from typing import List


async def create_purchases(db: AsyncSession, user_id: int, course_id: int, status: Status):
    purchase = Purchases(
        user_id=user_id,
        course_id=course_id,
        status=status,
    )
    
    db.add(purchase)
    await db.commit()
    await db.refresh(purchase)
    return purchase


async def get_purchase_by_id(db: AsyncSession, purchase_id: int):
    query = select(Purchases).where(Purchases.id == purchase_id)
    res = await db.execute(query)
    purchase = res.scalar_one_or_none()
    return purchase


async def get_paid_purchase(db: AsyncSession, user_id: int) -> List[Purchases]:
    query = (
        select(Purchases)
        .where(Purchases.status == Status.PAID, Purchases.user_id == user_id)
        .order_by(Purchases.created_at.desc())
    )
    res = await db.execute(query)
    purchases = res.scalars().all()
    return purchases


async def get_paid_purchase_by_course(db: AsyncSession, user_id: int, course_id: int):
    query = select(Purchases).where(
        Purchases.user_id == user_id,
        Purchases.course_id == course_id,
        Purchases.status == Status.PAID,
    )
    res = await db.execute(query)
    purchase = res.scalar_one_or_none()
    return purchase


async def get_all_purchases(db: AsyncSession, offset: int = 0, limit: int = 100):
    query = select(Purchases).order_by(Purchases.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()