from aiogram import Router, F
from dotenv import load_dotenv, find_dotenv
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, LabeledPrice, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from src.bot.filters.user_filter import IsUser
from src.bot.kbd.user_kbd import menu_kbd
from src.db.session import LocalSession
from src.db.crud.courses import get_all_courses, get_course_by_id, get_course_by_title
from src.db.crud.purchases import create_purchases, get_paid_purchase, get_paid_purchase_by_course
from src.bot.kbd.user_kbd import buy_course_kbd, buy_course
from src.db.crud.purchases import get_purchase_by_id
from src.db.enums import Status, ContentType
from src.db.crud.users import get_or_create_user
import os

load_dotenv(find_dotenv())

user_router = Router()
user_router.message.filter(IsUser())

@user_router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Hello, this is a bot where you can buy courses. Choose one of the following buttons", reply_markup=menu_kbd)


@user_router.message(F.text == "View courses")
async def get_courses(message: Message):
    
    async with LocalSession() as session:
        courses = await get_all_courses(db=session)
        
        if courses:
            for course in courses:
                text = (
                    f"<b>Course title</b>: {course.title}\n"
                    f"<b>Course description</b>: {course.description}\n"
                    f"<b>Course price</b>: {course.price} $\n"
                    f"<b>Course content type</b>: {course.content_type.value}\n"
                    f"<b>Creation time</b>: {course.created_at}"
                )

                
                if course.photo_url:
                    await message.answer_photo(
                        photo=course.photo_url,
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=buy_course_kbd(course.id)
                    )
                else:
                    await message.answer(text, parse_mode="HTML", reply_markup=buy_course_kbd(course.id))
        else:
            await message.answer("There are no courses yet")


@user_router.callback_query(F.data.startswith("buy_course"))
async def buy_course_cb(call: CallbackQuery):
    await call.answer()
    
    course_id = int(call.data.split(":")[1])
    
    async with LocalSession() as session:
        db_user = await get_or_create_user(db=session, telegram_user=call.from_user)
        paid_purchase = await get_paid_purchase_by_course(db=session, user_id=db_user.id, course_id=course_id)
        if paid_purchase:
            await call.message.answer(
                "You have already purchased this course. To access courses, use 'View purchased courses'.",
                reply_markup=menu_kbd,
            )
            return

        purchase = await create_purchases(db=session, user_id=db_user.id, course_id=course_id, status=Status.PENDING)
        course = await get_course_by_id(db=session, course_id=course_id)
        
    await call.message.answer("💳 Pay for course", reply_markup=buy_course(purchase))
    
    

@user_router.callback_query(F.data.startswith("pay_test:"))
async def pay_test(call: CallbackQuery):
    purchase_id = int(call.data.split(":")[1])

    async with LocalSession() as session:
        purchase = await get_purchase_by_id(session, purchase_id)
        purchase.status = Status.PAID
        await session.commit()

    await call.message.answer(
        "✅ Payment successful (TEST MODE)\n"
        "🎓 Course access opened"
    )


@user_router.message(F.text == "View purchased courses")
async def show_paid_courses(message: Message):
    async with LocalSession() as session:
        db_user = await get_or_create_user(db=session, telegram_user=message.from_user)
        purchases = await get_paid_purchase(db=session, user_id=db_user.id)

        if not purchases:
            await message.answer("You have no purchased courses yet.")
            return

        buttons = []
        for purchase in purchases:
            course = await get_course_by_id(db=session, course_id=purchase.course_id)
            if not course:
                continue
            buttons.append([KeyboardButton(text=course.title)])

        buttons.append([KeyboardButton(text="Back")])

        keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        await message.answer("Select a course:", reply_markup=keyboard)


@user_router.message(F.text == "Info")
async def info_cmd(message: Message):
    text = (
        "ℹ️ <b>Bot Information</b>\n\n"
        "This bot is designed for purchasing and viewing online courses 📚\n\n"
        "Here you can:\n"
        "• view available courses\n"
        "• learn description and price\n"
        "• purchase a course\n"
        "• access materials after payment\n\n"
        "💳 <b>Payment works in test mode</b>\n"
        "This bot is a demonstration project. "
        "Purchasing courses simulates the real payment process, money is not charged."
    )

    await message.answer(text, parse_mode="HTML")




@user_router.message()
async def send_course_content(message: Message):
    title = (message.text or "").strip()
    if not title:
        return

    async with LocalSession() as session:
        course = await get_course_by_title(db=session, title=title)
        if not course:
            return
        db_user = await get_or_create_user(db=session, telegram_user=message.from_user)
        purchase = await get_paid_purchase_by_course(db=session, user_id=db_user.id, course_id=course.id)

        if not purchase:
            await message.answer(
                "You do not have access to this course. To purchase, go to 'View courses'.",
                reply_markup=menu_kbd,
            )
            return

        await message.answer("Sending course content...", reply_markup=ReplyKeyboardRemove())

        if course.content_type == ContentType.PDF:
            if course.content_data.startswith("http"):
                try:
                    await message.answer_document(course.content_data)
                    return
                except Exception:
                    pass
            await message.answer(f"PDF:\n{course.content_data}")

        elif course.content_type == ContentType.VIDEO:
            if course.content_data.startswith("http") and any(ext in course.content_data for ext in (".mp4", ".webm", ".mov")):
                try:
                    await message.answer_video(course.content_data)
                    return
                except Exception:
                    pass
            await message.answer(f"Video:\n{course.content_data}")

        else:
            await message.answer(f"Link/content:\n{course.content_data}")
        
        
