from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

menu_kbd = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Просмотреть курсы"), KeyboardButton(text="Просмотреть купленные курсы")],
        [KeyboardButton(text="Info")]
    ],
    resize_keyboard=True
)


def buy_course_kbd(course_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Приобрести курс",
                    callback_data=f"buy_course:{course_id}"
                )
            ]
        ]
    )
    


def buy_course(purchase):
    inline_keyboard=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оплатить (TEST)",
                        callback_data=f"pay_test:{purchase.id}")]
        ]
    )
    
    return inline_keyboard