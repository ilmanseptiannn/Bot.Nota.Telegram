from datetime import date, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8617158165:AAFoT-KWonUGDH8lllTlv7fS-1lcH9pjpVU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Mexico", callback_data="Mexico")],
        [InlineKeyboardButton("Kembang Seruni", callback_data="Kembang Seruni")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Hai, Selamat datang di Tuumbooh Bot\nsilahkan pilih project",
        reply_markup=reply_markup,
    )


def build_calendar(year=None, month=None):
    today = date.today()
    if year is None or month is None:
        year = today.year
        month = today.month

    # navigation row: prev year, prev month, label, next month, next year
    prev_month_date = date(year, month, 1)
    if month == 1:
        prev_month_date = date(year - 1, 12, 1)
    else:
        prev_month_date = date(year, month - 1, 1)

    if month == 12:
        next_month_date = date(year + 1, 1, 1)
    else:
        next_month_date = date(year, month + 1, 1)

    nav_row = [
        InlineKeyboardButton("<<", callback_data=f"calendar_{year-1}_{month}"),
        InlineKeyboardButton("<", callback_data=f"calendar_{prev_month_date.year}_{prev_month_date.month}"),
        InlineKeyboardButton(f"{year}-{month:02d}", callback_data="noop"),
        InlineKeyboardButton(">", callback_data=f"calendar_{next_month_date.year}_{next_month_date.month}"),
        InlineKeyboardButton(">>", callback_data=f"calendar_{year+1}_{month}"),
    ]

    # compute number of days in month
    if month == 12:
        x = date(year + 1, 1, 1)
    else:
        x = date(year, month + 1, 1)
    days_count = (x - date(year, month, 1)).days

    rows = [nav_row]
    rows.append([
        InlineKeyboardButton('Mo', callback_data='noop'),
        InlineKeyboardButton('Tu', callback_data='noop'),
        InlineKeyboardButton('We', callback_data='noop'),
        InlineKeyboardButton('Th', callback_data='noop'),
        InlineKeyboardButton('Fr', callback_data='noop'),
        InlineKeyboardButton('Sa', callback_data='noop'),
        InlineKeyboardButton('Su', callback_data='noop'),
    ])

    first_weekday = date(year, month, 1).weekday()  # Mon=0
    week = []
    for _ in range(first_weekday):
        week.append(InlineKeyboardButton(' ', callback_data='noop'))

    for day in range(1, days_count + 1):
        d = date(year, month, day)
        label = f"{day:02d}"
        week.append(InlineKeyboardButton(label, callback_data=f"tgl_{d.isoformat()}"))

        if d.weekday() == 6:
            rows.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(' ', callback_data='noop'))
        rows.append(week)

    return InlineKeyboardMarkup(rows)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    project = query.data
    context.user_data['selected_project'] = project
    template = (
        "Silahkan isi Form dibawah ini ya!\n"
        f"Project: {project}\n"
        "Nama Barang:\n"
        "Jumlah Barang:\n"
        "Harga Satuan:\n"
        "Vendor:\n"
        "Pembayaran:\n"
        "Karegori Barang:"
    )

    await query.message.reply_text(template)


async def cross_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # form submission check
    if 'selected_project' in context.user_data and "Project:" in text:
        context.user_data['form_text'] = text
        await update.message.reply_text(text)

        keyboard = [
            [InlineKeyboardButton("Sesuai", callback_data="sesuai")],
            [InlineKeyboardButton("Tidak Sesuai", callback_data="tidak_sesuai")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("apakah nota sudah sesuai?", reply_markup=reply_markup)
        return

    # date selection step
    if context.user_data.get('awaiting_date'):
        tanggal = text
        context.user_data['selected_date'] = tanggal
        del context.user_data['awaiting_date']

        await update.message.reply_text(f"Tanggal Pengeluaran telah dipilih yaitu {tanggal}, apakah tanggal sudah sesuai?")
        keyboard = [
            [InlineKeyboardButton("Tanggal Sesuai", callback_data="tanggal_sesuai")],
            [InlineKeyboardButton("Tanggal Tidak Sesuai", callback_data="tanggal_tidak_sesuai")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("pilih salah satu:", reply_markup=reply_markup)
        return


async def sesuai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("Nota sesuai!, Silahkan pilih tanggal pengeluaran")
    calendar_markup = build_calendar()
    await query.message.reply_text("Pilih tanggal pengeluaran:", reply_markup=calendar_markup)

    context.user_data['awaiting_date'] = True
    await query.edit_message_text(text="(status: nota sesuai)")


async def tidak_sesuai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project = context.user_data.get('selected_project', 'Unknown')

    # chat pertama
    await query.edit_message_text(text="oh tidak nota tidak sesuai, silakan perbaiki nota sebelum nota diproses")

    # chat kedua
    template = (
        "Silahkan isi Form dibawah ini ya!\n"
        f"Project: {project}\n"
        "Nama Barang:\n"
        "Jumlah Barang:\n"
        "Harga Satuan:\n"
        "Vendor:\n"
        "Pembayaran:\n"
        "Karegori Barang:"
    )
    await query.message.reply_text(template)


async def tanggal_sesuai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tanggal = context.user_data.get('selected_date', 'tidak diketahui')
    await query.edit_message_text(text=f"Tanggal sudah sesuai ({tanggal}).")
    await query.message.reply_text("Nota dan Tanggal Pengeluaran telah sesuai!, silahkan Upload Receipt")
    context.user_data['awaiting_receipt'] = True


async def tanggal_pilih_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('tgl_'):
        tanggal = query.data.replace('tgl_', '')
        context.user_data['selected_date'] = tanggal
        if 'awaiting_date' in context.user_data:
            del context.user_data['awaiting_date']

        await query.message.reply_text(f"Tanggal Pengeluaran telah dipilih yaitu {tanggal}, apakah tanggal sudah sesuai?")
        keyboard = [
            [InlineKeyboardButton("Tanggal Sesuai", callback_data="tanggal_sesuai")],
            [InlineKeyboardButton("Tanggal Tidak Sesuai", callback_data="tanggal_tidak_sesuai")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Pilih salah satu:", reply_markup=reply_markup)
        return

    if query.data.startswith('calendar_'):
        _, yr, mo = query.data.split('_')
        year = int(yr)
        month = int(mo)
        calendar_markup = build_calendar(year=year, month=month)
        await query.message.edit_text(f"Pilih tanggal pengeluaran (tahun {year}, bulan {month:02d}):", reply_markup=calendar_markup)
        return


async def tanggal_tidak_sesuai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Tanggal tidak sesuai, silakan pilih kembali tanggal pengeluaran.")
    context.user_data['awaiting_date'] = True

    # Kirim kalender ulang
    calendar_markup = build_calendar()
    await query.message.reply_text("Pilih tanggal pengeluaran:", reply_markup=calendar_markup)


async def receipt_sesuai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Baik, Respon diterima!\n\nNota : Sesuai\nTanggal : Sesuai\nReciept : Sesuai\n\nNota sudah sesuai dan akan diproses menuju Spreadsheet!")

    # Tambahkan button Kirim Nota Baru
    keyboard = [
        [InlineKeyboardButton("Kirim Nota Baru", callback_data="kirim_nota_baru")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Apakah Anda ingin mengirim nota baru?", reply_markup=reply_markup)


async def receipt_tidak_sesuai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Receipt tidak sesuai, silakan upload receipt baru.")
    context.user_data['awaiting_receipt'] = True
    await query.message.reply_text("Silakan kirim receipt yang baru, berupa dokumen/foto/video.")


async def kirim_nota_baru_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Reset user data
    context.user_data.clear()

    # Kirim ulang start message
    keyboard = [
        [InlineKeyboardButton("Mexico", callback_data="Mexico")],
        [InlineKeyboardButton("Kembang Seruni", callback_data="Kembang Seruni")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "Hai, Selamat datang di Tuumbooh Bot\nsilahkan pilih project",
        reply_markup=reply_markup,
    )


async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_receipt'):
        return

    # copy the file back in response
    if update.message.document:
        await update.message.reply_document(update.message.document.file_id)
    elif update.message.photo:
        await update.message.reply_photo(update.message.photo[-1].file_id)
    elif update.message.video:
        await update.message.reply_video(update.message.video.file_id)
    else:
        await update.message.reply_text('Tolong kirim file/dokumen atau foto sebagai receipt.')
        return

    context.user_data.pop('awaiting_receipt', None)
    await update.message.reply_text('Receipt telah diterima, apakah receipt sudah sesuai?')
    keyboard = [
        [InlineKeyboardButton('Receipt Sesuai', callback_data='receipt_sesuai')],
        [InlineKeyboardButton('Receipt Tidak Sesuai', callback_data='receipt_tidak_sesuai')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Silakan pilih:', reply_markup=reply_markup)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(sesuai_handler, pattern="^sesuai$"))
    app.add_handler(CallbackQueryHandler(tidak_sesuai_handler, pattern="^tidak_sesuai$"))
    app.add_handler(CallbackQueryHandler(tanggal_pilih_handler, pattern="^(tgl_.*|calendar_.*)$"))
    app.add_handler(CallbackQueryHandler(tanggal_sesuai_handler, pattern="^tanggal_sesuai$"))
    app.add_handler(CallbackQueryHandler(tanggal_tidak_sesuai_handler, pattern="^tanggal_tidak_sesuai$"))
    app.add_handler(CallbackQueryHandler(receipt_sesuai_handler, pattern="^receipt_sesuai$"))
    app.add_handler(CallbackQueryHandler(receipt_tidak_sesuai_handler, pattern="^receipt_tidak_sesuai$"))
    app.add_handler(CallbackQueryHandler(kirim_nota_baru_handler, pattern="^kirim_nota_baru$"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(Mexico|Kembang Seruni)$"))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, receipt_handler))
    app.add_handler(MessageHandler(filters.TEXT, cross_check))

    print("Bot berjalan... tekan Ctrl+C untuk stop")
    app.run_polling()


if __name__ == "__main__":
    main()

