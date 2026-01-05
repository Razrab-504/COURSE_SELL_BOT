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
    await message.answer("Привет это бот в котором ты можешь купить курсы. Выбери одну из следующих кнопок", reply_markup=menu_kbd)


@user_router.message(F.text == "Просмотреть курсы")
async def get_courses(message: Message):
    
    async with LocalSession() as session:
        courses = await get_all_courses(db=session)
        
        if courses:
            for course in courses:
                text = (
                    f"<b>Название курса</b>: {course.title}\n"
                    f"<b>Описание курса</b>: {course.description}\n"
                    f"<b>Цена курса</b>: {course.price} $\n"
                    f"<b>Тип контента курса</b>: {course.content_type.value}\n"
                    f"<b>Время создания</b>: {course.created_at}"
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
            await message.answer("Курсов пока что нету")


@user_router.callback_query(F.data.startswith("buy_course"))
async def buy_course_cb(call: CallbackQuery):
    await call.answer()
    
    course_id = int(call.data.split(":")[1])
    
    async with LocalSession() as session:
        db_user = await get_or_create_user(db=session, telegram_user=call.from_user)
        paid_purchase = await get_paid_purchase_by_course(db=session, user_id=db_user.id, course_id=course_id)
        if paid_purchase:
            await call.message.answer(
                "Вы уже приобрели этот курс. Для доступа к курсам используйте 'Просмотреть купленные курсы'.",
                reply_markup=menu_kbd,
            )
            return

        purchase = await create_purchases(db=session, user_id=db_user.id, course_id=course_id, status=Status.PENDING)
        course = await get_course_by_id(db=session, course_id=course_id)
        
    await call.message.answer("💳 Оплатить курс", reply_markup=buy_course(purchase))
    
    

@user_router.callback_query(F.data.startswith("pay_test:"))
async def pay_test(call: CallbackQuery):
    purchase_id = int(call.data.split(":")[1])

    async with LocalSession() as session:
        purchase = await get_purchase_by_id(session, purchase_id)
        purchase.status = Status.PAID
        await session.commit()

    await call.message.answer(
        "✅ Оплата прошла успешно (TEST MODE)\n"
        "🎓 Доступ к курсу открыт"
    )


@user_router.message(F.text == "Просмотреть купленные курсы")
async def show_paid_courses(message: Message):
    async with LocalSession() as session:
        db_user = await get_or_create_user(db=session, telegram_user=message.from_user)
        purchases = await get_paid_purchase(db=session, user_id=db_user.id)

        if not purchases:
            await message.answer("У вас пока что нет приобретённых курсов.")
            return

        buttons = []
        for purchase in purchases:
            course = await get_course_by_id(db=session, course_id=purchase.course_id)
            if not course:
                continue
            buttons.append([KeyboardButton(text=course.title)])

        buttons.append([KeyboardButton(text="Назад")])

        keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        await message.answer("Выберите курс:", reply_markup=keyboard)


@user_router.message(F.text == "Info")
async def info_cmd(message: Message):
    text = (
        "ℹ️ <b>Информация о боте</b>\n\n"
        "Этот бот предназначен для покупки и просмотра онлайн-курсов 📚\n\n"
        "Здесь вы можете:\n"
        "• посмотреть доступные курсы\n"
        "• узнать описание и цену\n"
        "• приобрести курс\n"
        "• получить доступ к материалам после оплаты\n\n"
        "💳 <b>Оплата работает в тестовом режиме</b>\n"
        "Данный бот является демонстрационным проектом. "
        "Покупка курсов имитирует реальный процесс оплаты, деньги не списываются."
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
                "У вас нет доступа к этому курсу. Чтобы приобрести — перейдите в 'Просмотреть курсы'.",
                reply_markup=menu_kbd,
            )
            return

        await message.answer("Отправляю контент курса...", reply_markup=ReplyKeyboardRemove())

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
            await message.answer(f"Видео:\n{course.content_data}")

        else:
            await message.answer(f"Ссылка/контент:\n{course.content_data}")
        
        
