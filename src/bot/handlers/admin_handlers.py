from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from src.bot.filters.admin_filter import IsAdmin
from src.bot.kbd import admin_kbd
from src.db.session import LocalSession
from src.db.crud.users import count_users, get_users_paginated, set_user_ban
from src.db.crud.courses import get_all_courses, create_course, delete_course, get_course_by_id
from src.db.models.purchases import Purchases
from src.db.models.courses import Course
from src.db.enums import Status
from sqlalchemy import select, func

admin_router = Router()
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


class BroadcastStates(StatesGroup):
    waiting_message = State()
    waiting_confirm = State()


class CourseCreateStates(StatesGroup):
    wait_title = State()
    wait_price = State()
    wait_description = State()
    wait_content_type = State()
    wait_content = State()
    wait_photo = State()
    wait_confirm = State()


class SettingsStates(StatesGroup):
    wait_currency = State()


@admin_router.message(Command("admin"))
async def admin_menu(message: Message):
    await message.answer("Панель администратора:", reply_markup=admin_kbd.admin_main_kbd())


@admin_router.callback_query(F.data.startswith("admin:"))
async def admin_callbacks(query: CallbackQuery, state: FSMContext):
    data = query.data or ""

    if data == "admin:menu":
        await query.message.edit_text("Панель администратора:", reply_markup=admin_kbd.admin_main_kbd())
        await query.answer()
        return

    if data == "admin:stats":
        async with LocalSession() as db:
            users_count = await count_users(db)
            courses = await get_all_courses(db)
            courses_count = len(courses)
            purchases_count = (await db.execute(select(func.count()).select_from(Purchases))).scalar_one()
            revenue_res = await db.execute(
                select(func.coalesce(func.sum(Course.price), 0)).select_from(Purchases).join(Course, Purchases.course_id == Course.id).where(Purchases.status == Status.PAID)
            )
            revenue = revenue_res.scalar_one() or 0
            text = (
                f"📊 Статистика\n"
                f"Пользователей: {users_count}\n"
                f"Курсов: {courses_count}\n"
                f"Покупок: {purchases_count}\n"
                f"Выручка: ${revenue} (USD)\n"
            )
        await query.message.edit_text(text, reply_markup=admin_kbd.admin_main_kbd())
        await query.answer()
        return

    if data.startswith("admin:users:page:"):
        try:
            page = int(data.split(":")[-1])
        except Exception:
            page = 0
        limit = 10
        offset = page * limit
        async with LocalSession() as db:
            users = await get_users_paginated(db, offset=offset, limit=limit)
            total = await count_users(db)
        has_prev = page > 0
        has_next = (offset + limit) < total
        if not users:
            await query.message.edit_text("Пользователи не найдены.", reply_markup=admin_kbd.users_page_kbd(page, has_prev, has_next))
            await query.answer()
            return
        msgs = []
        for u in users:
            name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "(no name)"
            text = f"ID: {u.id}\nTelegram: {u.telegram_user_id}\nName: {name}\nBanned: {u.is_banned}"
            await query.message.answer(text, reply_markup=admin_kbd.user_detail_kbd(u.id, u.is_banned))
        await query.message.edit_text("Список пользователей — страница {page+1}", reply_markup=admin_kbd.users_page_kbd(page, has_prev, has_next))
        await query.answer()
        return

    if data.startswith("admin:user:"):
        parts = data.split(":")
        if len(parts) >= 4:
            user_id = int(parts[2])
            action = parts[3]
            if action == "detail":
                async with LocalSession() as db:
                    user = await db.get(__import__("src.db.models.users", fromlist=["User"]).User, user_id)
                if not user:
                    await query.answer("Пользователь не найден", show_alert=True)
                    return
                name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "(no name)"
                text = f"ID: {user.id}\nTelegram: {user.telegram_user_id}\nName: {name}\nBanned: {user.is_banned}"
                await query.message.edit_text(text, reply_markup=admin_kbd.user_detail_kbd(user.id, user.is_banned))
                await query.answer()
                return
            if action == "toggle_ban":
                async with LocalSession() as db:
                    user = await set_user_ban(db, user_id, not (await db.get(__import__("src.db.models.users", fromlist=["User"]).User, user_id)).is_banned)
                if not user:
                    await query.answer("Ошибка", show_alert=True)
                    return
                await query.message.edit_text(f"Пользователь {user.id} обновлён. Забанен={user.is_banned}", reply_markup=admin_kbd.user_detail_kbd(user.id, user.is_banned))
                await query.answer("Готово")
                return
            if action == "message":
                async with LocalSession() as db:
                    user_obj = await db.get(__import__("src.db.models.users", fromlist=["User"]).User, user_id)
                if not user_obj:
                    await query.answer("Пользователь не найден", show_alert=True)
                    return
                await state.update_data(target_user=user_obj.telegram_user_id, target_db_user=user_obj.id)
                await state.set_state(BroadcastStates.waiting_message)
                await query.message.answer("Отправьте текст сообщения пользователю (или прикрепите медиа). Введите /cancel для отмены.")
                await query.answer()
                return

    if data == "admin:purchases":
        async with LocalSession() as db:
            from src.db.crud.purchases import get_all_purchases
            purchases = await get_all_purchases(db, offset=0, limit=50)
            if not purchases:
                await query.message.edit_text("Покупок не найдено.", reply_markup=admin_kbd.admin_main_kbd())
                await query.answer()
                return
            lines = []
            for p in purchases:
                lines.append(f"ID:{p.id} user:{p.user_id} course:{p.course_id} status:{p.status.value} created:{p.created_at}")
            text = "\n".join(lines)
        await query.message.edit_text("Последние покупки:\n" + text, reply_markup=admin_kbd.admin_main_kbd())
        await query.answer()
        return

    if data == "admin:courses":
        async with LocalSession() as db:
            courses = await get_all_courses(db)
        if not courses:
            await query.message.edit_text("Курсы не найдены.", reply_markup=admin_kbd.admin_main_kbd())
            await query.answer()
            return
        await query.message.edit_text("Список курсов:", reply_markup=admin_kbd.courses_list_kbd(courses))
        await query.answer()
        return

    if data == "admin:courses:create":
        await state.set_state(CourseCreateStates.wait_title)
        await state.update_data(course_data={})
        await query.message.answer("Создание курса — введите название курса:")
        await query.answer()
        return

    if data == "admin:courses":
        async with LocalSession() as db:
            courses = await get_all_courses(db)
        if not courses:
            await query.message.edit_text("Курсы не найдены.", reply_markup=admin_kbd.admin_main_kbd())
            await query.answer()
            return
        await query.message.edit_text("Список курсов:", reply_markup=admin_kbd.courses_list_kbd(courses))
        await query.answer()
        return

    if data.startswith("admin:courses:detail:"):
        course_id = int(data.split(":")[-1])
        async with LocalSession() as db:
            course = await get_course_by_id(db, course_id)
        if not course:
            await query.answer("Курс не найден", show_alert=True)
            return
        if getattr(course, "photo_url", None):
            try:
                await query.message.answer_photo(course.photo_url)
            except Exception:
                pass
        text = f"ID: {course.id}\nTitle: {course.title}\nPrice: ${course.price}\nDescription: {course.description or ''}\nContent type: {course.content_type}\nContent data: {course.content_data[:150] + ('...' if len(course.content_data)>150 else '')}"
        await query.message.edit_text(text, reply_markup=admin_kbd.course_detail_kbd(course.id))
        await query.answer()
        return

    if data.startswith("admin:courses:delete:"):
        course_id = int(data.split(":")[-1])
        await query.message.edit_text("Вы уверены, что хотите удалить курс?", reply_markup=admin_kbd.confirm_kbd("delete_course", course_id))
        await query.answer()
        return


    if data == "admin:broadcast":
        await state.set_state(BroadcastStates.waiting_message)
        await query.message.answer("Отправьте текст рассылки. После отправки вы увидите превью и сможете подтвердить отправку всем пользователям.")
        await query.answer()
        return

    if data == "admin:settings":
        from src.bot.app_settings import get_currency
        cur = get_currency()
        await query.message.edit_text("Настройки:", reply_markup=admin_kbd.settings_kbd(cur))
        await query.answer()
        return

    if data == "admin:settings:currency":
        await state.set_state(SettingsStates.wait_currency)
        await query.message.answer("Введите символ валюты (например, $):")
        await query.answer()
        return

    if data.startswith("admin:courses:content_type:"):
        ct_name = data.split(":")[-1]
        from src.db.enums import ContentType
        try:
            ct = ContentType[ct_name]
        except Exception:
            await query.answer("Неверный тип содержимого", show_alert=True)
            return
        data_s = await state.get_data()
        course_data = data_s.get("course_data", {})
        course_data["content_type"] = ct.value
        await state.update_data(course_data=course_data)
        await state.set_state(CourseCreateStates.wait_content)
        await query.message.answer(f"Тип содержимого установлен: {ct.value}. Теперь отправьте содержимое курса (текст, URL или идентификатор файла).")
        await query.answer()
        return
    if data.startswith("admin:confirm:"):
        parts = data.split(":")
        action = parts[2]
        if action == "broadcast":
            data_state = await state.get_data()
            text_to_send = data_state.get("broadcast_text")
            if not text_to_send:
                await query.answer("Нет текста для рассылки", show_alert=True)
            sent = 0
            failed = 0
            async with LocalSession() as db:
                users = await get_users_paginated(db, offset=0, limit=1000000)
                for u in users:
                    try:
                        await query.message.bot.send_message(u.telegram_user_id, text_to_send)
                        sent += 1
                    except Exception:
                        failed += 1
            await query.message.edit_text(f"Рассылка отправлена. Успешно: {sent}, ошибок: {failed}")
            await state.clear()
            await query.answer()
            return
        if action == "delete_course":
            course_id = int(parts[3])
            async with LocalSession() as db:
                ok = await delete_course(db, course_id)
            if ok:
                await query.message.edit_text("Курс удалён.", reply_markup=admin_kbd.admin_main_kbd())
            else:
                await query.answer("Не удалось удалить курс", show_alert=True)
            await query.answer()
            return
        if action == "create_course":
            data_s = await state.get_data()
            course_data = data_s.get("course_data") or {}
            async with LocalSession() as db:
                course = await create_course(
                    db,
                    title=course_data.get("title"),
                    price=int(course_data.get("price")),
                    description=course_data.get("description"),
                    content_type=course_data.get("content_type", "TEXT"),
                    content_data=course_data.get("content_data", ""),
                    photo_url=course_data.get("photo_url"),
                )
            await query.message.edit_text(f"Курс создан: {course.title} (ID: {course.id})", reply_markup=admin_kbd.admin_main_kbd())
            await state.clear()
            await query.answer()
            return
        if action == "delete_course":
            await query.answer()
            return

    if data.startswith("admin:cancel:"):
        await state.clear()
        await query.message.edit_text("Операция отменена.")
        await query.answer()
        return

    await query.answer()


@admin_router.message()
async def admin_waiting_message(message: Message, state: FSMContext):
    st = await state.get_state()

    if st == BroadcastStates.waiting_message.state:
        data_state = await state.get_data()
        target_user = data_state.get("target_user")
        if target_user:
            try:
                await message.bot.send_message(target_user, message.text)
                await message.answer("Сообщение отправлено пользователю.")
            except Exception:
                await message.answer("Не удалось отправить сообщение пользователю.")
            await state.clear()
            return
        await state.update_data(broadcast_text=message.text)
        await state.set_state(BroadcastStates.waiting_confirm)
        await message.answer("Превью рассылки:\n" + message.text, reply_markup=admin_kbd.confirm_kbd("broadcast", 0))
        return

    if st == CourseCreateStates.wait_title.state:
        await state.update_data(course_data={"title": message.text})
        await state.set_state(CourseCreateStates.wait_price)
        await message.answer("Введите цену (целое число):")
        return

    if st == CourseCreateStates.wait_price.state:
        try:
            price = int(message.text)
        except ValueError:
            await message.answer("Цена должна быть целым числом. Попробуйте ещё раз:")
            return
        data_s = await state.get_data()
        course_data = data_s.get("course_data", {})
        course_data["price"] = price
        await state.update_data(course_data=course_data)
        await state.set_state(CourseCreateStates.wait_description)
        await message.answer("Введите описание курса (или 'skip'):")
        return

    if st == CourseCreateStates.wait_description.state:
        data_s = await state.get_data()
        course_data = data_s.get("course_data", {})
        course_data["description"] = None if message.text.lower() == "skip" else message.text
        await state.update_data(course_data=course_data)
        await state.set_state(CourseCreateStates.wait_content_type)
        await message.answer("Выберите тип содержимого:", reply_markup=admin_kbd.content_type_kbd())
        return

    if st == SettingsStates.wait_currency.state:
        from src.bot.app_settings import set_currency
        symbol = message.text.strip()[:4]
        set_currency(symbol)
        await message.answer(f"Символ валюты установлен: {symbol}")
        await state.clear()
        return

    if st == CourseCreateStates.wait_content.state:
        data_s = await state.get_data()
        course_data = data_s.get("course_data", {})
        course_data["content_data"] = message.text
        await state.update_data(course_data=course_data)
        await state.set_state(CourseCreateStates.wait_photo)
        await message.answer("Отправьте изображение обложки курса или URL (или введите 'skip' чтобы пропустить):")
        return

    if st == CourseCreateStates.wait_photo.state:
        data_s = await state.get_data()
        course_data = data_s.get("course_data", {})

        if message.photo:
            file_id = message.photo[-1].file_id
            course_data["photo_url"] = file_id
            await state.update_data(course_data=course_data)
            try:
                await message.answer_photo(file_id)
            except Exception:
                pass
        else:
            txt = (message.text or "").strip()
            if txt.lower() == "skip":
                course_data["photo_url"] = None
                await state.update_data(course_data=course_data)
            else:
                course_data["photo_url"] = txt
                await state.update_data(course_data=course_data)
                try:
                    await message.answer_photo(txt)
                except Exception:
                    pass

        await state.set_state(CourseCreateStates.wait_confirm)
        from src.bot.app_settings import get_currency
        cur = get_currency()
        preview = (
            f"Превью курса:\nTitle: {course_data.get('title')}\nPrice: {cur}{course_data.get('price')}\nDescription: {course_data.get('description') or ''}\nContent type: {course_data.get('content_type')}\nContent: {course_data.get('content_data')[:200]}\nPhoto: {'yes' if course_data.get('photo_url') else 'no'}"
        )
        await message.answer(preview, reply_markup=admin_kbd.confirm_kbd("create_course", 0))
        return

    return


