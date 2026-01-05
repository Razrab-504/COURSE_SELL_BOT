from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.courses import Course


async def get_all_courses(db: AsyncSession):
    query = select(Course)
    res = await db.execute(query)
    courses = res.scalars().all()
    return courses


async def get_course_by_id(db: AsyncSession, course_id):
    query = select(Course).where(Course.id==course_id)
    res = await db.execute(query)
    course = res.scalar_one_or_none()
    return course

async def get_course_by_title(db: AsyncSession, title: str):
    query = select(Course).where(Course.title == title)
    res = await db.execute(query)
    course = res.scalar_one_or_none()
    return course


from src.db.enums import ContentType


async def create_course(db: AsyncSession, title: str, price: int, description: str | None, content_type: str | ContentType, content_data: str, photo_url: str | None = None):
    if isinstance(content_type, str):
        try:
            content_type = ContentType[content_type] if content_type in ContentType.__members__ else ContentType(content_type)
        except Exception:
            content_type = ContentType.LINK

    course = Course(
        title=title,
        price=price,
        description=description,
        content_type=content_type,
        content_data=content_data,
        photo_url=photo_url,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def update_course(db: AsyncSession, course_id: int, **kwargs):
    course = await db.get(Course, course_id)
    if not course:
        return None
    for k, v in kwargs.items():
        setattr(course, k, v)
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course_id: int):
    course = await db.get(Course, course_id)
    if not course:
        return False
    await db.delete(course)
    await db.commit()
    return True
