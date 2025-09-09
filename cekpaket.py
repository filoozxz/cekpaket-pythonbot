import logging
import requests
from math import ceil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.request import HTTPXRequest

# ============= CONFIG =============
BOT_TOKEN = "7249796632:AAHov7MoOlAQHOVQ41ucAh3KCC1jXyNyOuU"
API_KEY = "cfd41e9d-c184-426c-8b99-94eef89ab3ec"
API_URL = f"https://golang-openapi-packagelist-xltembakservice.kmsp-store.com/v1?api_key={API_KEY}"
ITEMS_PER_PAGE = 10  # banyak data per halaman

# ============= LOGGING =============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= FUNCTION AMBIL DATA API =============
def get_api_data():
    try:
        response = requests.get(API_URL, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data
        else:
            logger.error(f"API Error: status {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"API Error: {e}")
        return []

# ============= PAGINATION HANDLER =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_page(update, context, page=0)

async def send_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    data = get_api_data()
    if not data:
        if update.message:
            await update.message.reply_text("❌ Gagal mengambil data dari API.")
        elif update.callback_query:
            await update.callback_query.edit_message_text("❌ Gagal mengambil data dari API.")
        return

    # pagination logic
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    packages = data[start_idx:end_idx]

    text = "📦 <b>Daftar Paket:</b>\n"
    for i, item in enumerate(packages, start=1):
        nama = item.get("package_name_alias_short", "Tidak ada nama")
        harga = item.get("package_harga_int", "-")
        text += f"{i+start_idx}. {nama} - Rp{harga}\n"

    # tombol pilihan per paket
    keyboard = []
    row = []
    for i, pkg in enumerate(packages):
        # nomor global = start_idx + i + 1
        btn = InlineKeyboardButton(
            f"{start_idx + i + 1}",
            callback_data=f"detail_{page}_{i}"
        )
        row.append(btn)

        if len(row) == 5:  # jika sudah 5 tombol, buat baris baru
            keyboard.append(row)
            row = []

    # tombol sisa
    if row:
        keyboard.append(row)
    
    # tombol pagination
    total_pages = ceil(len(data) / ITEMS_PER_PAGE)
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page-1}")
        )
    for p in range(max(0, page-2), min(total_pages, page+3)):
        pagination_buttons.append(
            InlineKeyboardButton(
                str(p+1) if p != page else f"[{p+1}]",
                callback_data=f"page_{p}"
            )
        )
    if page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}")
        )
    if pagination_buttons:
        keyboard.append(pagination_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # edit / kirim pesan
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
        
# ============= DETAIL PAKET =============
async def send_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int, index: int):
    data = get_api_data()
    start_idx = page * ITEMS_PER_PAGE
    item = data[start_idx + index]

    kode = item.get("package_code", "-")
    nama = item.get("package_name_alias_short", "Tidak ada nama")
    harga = item.get("package_harga_int", "-")
    deskripsi = item.get("package_description", "Tidak ada deskripsi")

    text = f"📦 <b>Detail Paket</b>\n\n"
    text += f"🔖 Kode: <code>{kode}</code>\n"
    text += f"📌 Nama: {nama}\n"
    text += f"💰 Harga: Rp{harga}\n"
    text += f"📝 Deskripsi: {deskripsi}\n"

    # tombol kembali
    keyboard = [[InlineKeyboardButton("⬅ Kembali", callback_data=f"page_{page}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# ============= HANDLER CALLBACK =============
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("page_"):
        page = int(query.data.split("_")[1])
        await send_page(update, context, page)

    elif query.data.startswith("detail_"):
        _, page, idx = query.data.split("_")
        await send_detail(update, context, int(page), int(idx))

# ============= MAIN =============
def main():
    request = HTTPXRequest(connect_timeout=30, read_timeout=30, write_timeout=30, pool_timeout=30)
    app = Application.builder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
