import os  # <--- এখানে 'Import' থেকে 'import' এ পরিবর্তন করা হয়েছে
import requests
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from urllib.parse import urlparse
from typing import Dict, Any, Optional

# --- Configuration & Setup ---

# Bot Configuration
# NOTE: Replace with your actual Bot Token
BOT_TOKEN = "7344771509:AAG-TzGuhv1LE3t4i2KGqPdubicw1L2nuYU"

# --- Admin & Management Configuration ---
PRIMARY_ADMIN_USERNAME = "Jack_gameshop" 
SUPPORT_EMAIL = "Nssimkhanyt37@gmail.Com" 

# Admin and Moderator IDs (IMPORTANT: Replace 123456789 with YOUR actual Telegram User ID)
ADMINS = {123456789}  # <<-- আপনার Telegram User ID (integer) এখানে দিন
MODERATORS = set() 

# User Ban List (Store Telegram User IDs - Integers)
BANNED_USERS = set() 

# --- API Configuration ---
API_KEY = "hasan_key_5rhzUHR1qXnylvW5blQH"
API_URL = "https://tiksaveapi.vercel.app/api/download" 

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("📱 কীভাবে ব্যবহার করবেন", callback_data="help")],
        [InlineKeyboardButton("🌟 প্রিমিয়াম ফিচার্স", callback_data="premium")],
        [InlineKeyboardButton("📞 সাপোর্ট", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Bot Class ---

class TikTokDownloaderBot:
    """A Telegram Bot for downloading TikTok videos without watermark, with Admin controls."""

    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # --- Management Data (Initial values from Configuration) ---
        self.admins = ADMINS.copy()
        self.moderators = MODERATORS.copy()
        self.banned_users = BANNED_USERS.copy()
        self.api_key = API_KEY
        self.api_url = API_URL
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all message and callback handlers."""
        # Public Handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))

        # Admin/Moderator Handlers
        self.application.add_handler(CommandHandler("addadmin", self.add_admin)) 
        self.application.add_handler(CommandHandler("addmod", self.add_moderator)) 
        self.application.add_handler(CommandHandler("ban", self.ban_user)) 
        self.application.add_handler(CommandHandler("unban", self.unban_user)) 
        self.application.add_handler(CommandHandler("changeapi", self.change_api)) 
        self.application.add_handler(CommandHandler("status", self.status)) 

    # --- Authorization Checks ---

    def _is_admin(self, user_id: int) -> bool:
        """Check if the user is an Admin."""
        return user_id in self.admins

    def _is_moderator(self, user_id: int) -> bool:
        """Check if the user is a Moderator or Admin."""
        return user_id in self.moderators or user_id in self.admins

    # --- Command Handlers (Public) ---

    async def start_command(self, update: Update, context: CallbackContext):
        """Send welcome message when command /start is issued."""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name

        if user_id in self.banned_users:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🚫 <b>দুঃখিত!</b> আপনার অ্যাকাউন্টটি বট ব্যবহার করা থেকে <b>ব্যান</b> করা হয়েছে।\n"
                     f"সহায়তার জন্য <b>@{PRIMARY_ADMIN_USERNAME}</b>-এর সাথে যোগাযোগ করুন।",
                parse_mode='HTML'
            )
            return

        welcome_text = f"""
🤖 <b>TikTok ডাউনলোডার প্রো-তে স্বাগতম</b> 🎬

হাই <b>{user_name}</b>! আমি আপনাকে টিকটক ভিডিওগুলো ওয়াটারমার্ক ছাড়া ডাউনলোড করতে সাহায্য করতে পারি।

শুরু করতে একটি টিকটক লিঙ্ক পাঠান!
        """
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            reply_markup=create_main_menu_keyboard(),
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: CallbackContext):
        """Send help message when command /help is issued."""
        is_callback = update.callback_query is not None
        
        help_text = """
<b>📖 টিকটক ভিডিও ডাউনলোড করার পদ্ধতি:</b>

১. <b>টিকটক ভিডিও লিঙ্ক কপি করুন:</b>
   - টিকটক অ্যাপ খুলুন।
   - যে ভিডিওটি ডাউনলোড করতে চান, সেটি খুঁজুন।
   - "শেয়ার" বাটনে ট্যাপ করুন।
   - "লিঙ্ক কপি করুন" (Copy Link) নির্বাচন করুন।

২. <b>বট-কে লিঙ্কটি পাঠান:</b>
   - কপি করা টিকটক লিঙ্কটি এখানে পেস্ট করুন।
   - প্রসেসিং এর জন্য অপেক্ষা করুন।
   - আপনার ভিডিও ডাউনলোড করুন!

<b>⚠️ গুরুত্বপূর্ণ:</b>
- নিশ্চিত করুন যে ভিডিওটি <b>পাবলিক</b> করা আছে।
- লিঙ্কটি অবশ্যই বৈধ টিকটক URL হতে হবে।
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 ডাউনলোড শুরু করুন", callback_data="start_download")],
            [InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if is_callback:
            await update.callback_query.edit_message_text(
                help_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                help_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    # --- Callback Handlers ---

    async def button_handler(self, update: Update, context: CallbackContext):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "help":
            await self.help_command(update, context)
        elif data == "premium":
            await self._premium_info(update, context)
        elif data == "support":
            await self._support_info(update, context)
        elif data == "main_menu":
            user_name = update.effective_user.first_name
            welcome_text = f"""
🤖 <b>TikTok ডাউনলোডার প্রো-তে স্বাগতম</b> 🎬

হাই <b>{user_name}</b>! আমি আপনাকে টিকটক ভিডিওগুলো ওয়াটারমার্ক ছাড়া ডাউনলোড করতে সাহায্য করতে পারি।

শুরু করতে একটি টিকটক লিঙ্ক পাঠান!
            """
            await query.edit_message_text(
                welcome_text,
                reply_markup=create_main_menu_keyboard(),
                parse_mode='HTML'
            )
        elif data == "start_download":
            await query.edit_message_text(
                "🎯 <b>ডাউনলোডের জন্য প্রস্তুত!</b>\n\nকেবলমাত্র একটি টিকটক ভিডিও লিঙ্ক পাঠান এবং আমি সেটি ডাউনলোড করে দেবো!",
                parse_mode='HTML'
            )
        elif data == "contact_premium":
             await query.edit_message_text(
                "💎 <b>প্রিমিয়াম অ্যাক্সেস!</b>\n\nপ্রিমিয়াম ফিচারগুলো পেতে, অনুগ্রহ করে সরাসরি অ্যাডমিনকে মেসেজ করুন: "
                f"<b>@{PRIMARY_ADMIN_USERNAME}</b>\n\nআপনি চাইলে এখন প্রধান মেনুতে ফিরে যেতে পারেন।",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="main_menu")]]),
                parse_mode='HTML'
            )


    async def _premium_info(self, update: Update, context: CallbackContext):
        """Show premium features (Helper for button_handler)."""
        premium_text = """
<b>🌟 প্রিমিয়াম ফিচার্স (Premium Features):</b>

🚀 <b>অগ্রাধিকার প্রসেসিং (Priority Processing)</b>
   - দ্রুততম ডাউনলোড স্পিড

💎 <b>সর্বোচ্চ HD কোয়ালিটি</b>
   - 1080p পর্যন্ত সাপোর্ট

📁 <b>ব্যাচ ডাউনলোড (Batch Downloads)</b>
   - একসাথে একাধিক ভিডিও ডাউনলোড

🔒 <b>প্রাইভেট ভিডিও ডাউনলোড</b>
   - (সঠিক অনুমোদন সাপেক্ষে)

🎵 <b>শুধু অডিও এক্সট্র্যাকশন</b>
   - MP3 ফরম্যাটে অডিও সেভ করার সুবিধা

<b>প্রিমিয়াম অ্যাক্সেসের জন্য</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("💎 প্রিমিয়াম নিন", callback_data="contact_premium")],
            [InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            premium_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def _support_info(self, update: Update, context: CallbackContext):
        """Show support information (Helper for button_handler)."""
        support_text = f"""
<b>📞 সাপোর্ট ও সহায়তা</b>

যদি আপনি কোনো সমস্যার সম্মুখীন হন:

🔧 <b>সাধারণ সমাধান:</b>
   - নিশ্চিত করুন টিকটক লিঙ্কটি বৈধ।
   - ভিডিওটি ডিলিট হয়নি বা প্রাইভেট করা নেই।

📧 <b>যোগাযোগের মাধ্যম:</b>
   - টেলিগ্রাম অ্যাডমিন: <b>@{PRIMARY_ADMIN_USERNAME}</b>
   - ইমেইল: <b>{SUPPORT_EMAIL}</b>

🐛 <b>বাগ রিপোর্ট:</b>
   - সমস্যার বিস্তারিত বর্ণনা দিন।
   - টিকটক URL এবং স্ক্রিনশট দিন।

আমরা ২৪/৭ আপনাকে সাহায্য করতে প্রস্তুত!
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="main_menu")],
            [InlineKeyboardButton("🆘 সরাসরি সাহায্য (Telegram)", url=f"https://t.me/{PRIMARY_ADMIN_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            support_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # --- Utility Methods for Download Logic ---
    
    def _is_valid_tiktok_url(self, url: str) -> bool:
        """Check if the URL is a valid TikTok URL"""
        tiktok_domains = [
            'tiktok.com',
            'vm.tiktok.com',
            'vt.tiktok.com',
            'www.tiktok.com'
        ]
        
        try:
            parsed = urlparse(url)
            return any(domain in parsed.netloc for domain in tiktok_domains) and len(parsed.path) > 1
        except:
            return False
    
    def _fetch_tiktok_data(self, url: str) -> Dict[str, Any]:
        """Fetch TikTok video data from API"""
        try:
            # Dynamically use the current API settings
            api_url = f"{self.api_url}?key={self.api_key}&url={url}" 
            
            response = requests.get(api_url, timeout=30)
            response.raise_for_status() 
            
            data = response.json()
            
            if not data.get('success'):
                 return {"success": False, "error": data.get('message', 'API-তে তথ্য পাওয়া যায়নি বা ত্রুটি হয়েছে।')}
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request Error: {e}")
            return {"success": False, "error": "API সংযোগ বা অনুরোধে ত্রুটি।"}
        except json.JSONDecodeError:
            return {"success": False, "error": "API থেকে অবৈধ প্রতিক্রিয়া (JSON ত্রুটি)।"}
        except Exception as e:
            logger.error(f"Unexpected error during API call: {e}")
            return {"success": False, "error": "অপ্রত্যাশিত ত্রুটি।"}

    def _get_download_url(self, download_links: list) -> Optional[str]:
        """Find the best quality video URL from the list of links."""
        if not download_links:
            return None
        
        # 1. Prefer HD Quality
        for link in download_links:
            if link.get('type') == 'hd' and link.get('url'):
                return link['url']
        
        # 2. Fallback to SD Quality
        for link in download_links:
            if link.get('type') == 'sd' and link.get('url'):
                return link['url']

        return download_links[0].get('url') if download_links[0].get('url') else None
    
    # --- Main Message Handler (অটো কপি ফিচার যুক্ত করা হয়েছে) ---

    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle incoming messages (assumed to be a URL)."""
        user_message = update.message.text.strip()
        user_id = update.effective_user.id
        
        if user_id in self.banned_users:
            await update.message.reply_text("🚫 আপনি <b>ব্যান</b> হয়েছেন। আপনার জন্য কোনো কমান্ড কাজ করবে না।", parse_mode='HTML')
            return
        
        if not self._is_valid_tiktok_url(user_message):
            await update.message.reply_text(
                "❌ <b>অবৈধ টিকটক URL</b>\n\nঅনুগ্রহ করে একটি বৈধ টিকটক ভিডিও লিঙ্ক পাঠান।",
                parse_mode='HTML'
            )
            return
        
        processing_msg = await update.message.reply_text("⏳ <b>আপনার অনুরোধ প্রক্রিয়া করা হচ্ছে...</b>", parse_mode='HTML')
        
        api_data = self._fetch_tiktok_data(user_message)
        
        if not api_data.get('success'):
            error_msg = api_data.get('error', 'অজানা ত্রুটি ঘটেছে')
            await processing_msg.edit_text(
                f"❌ <b>ডাউনলোড ব্যর্থ</b>\n\nত্রুটি: <b>{error_msg}</b>\n\nঅনুগ্রহ করে লিঙ্কটি পরীক্ষা করে আবার চেষ্টা করুন।",
                parse_mode='HTML'
            )
            return
        
        # 4. Process and Send Video
        try:
            video_data = api_data['data']
            
            title = video_data.get('title', 'TikTok Video')
            author_name = video_data.get('author', {}).get('name', 'Unknown')
            username = video_data.get('author', {}).get('username', 'unknown')
            thumbnail = video_data.get('thumbnail', '')
            download_links = video_data.get('download_links', {}).get('video', [])
            video_url = self._get_download_url(download_links)
            
            if not video_url:
                raise ValueError("ডাউনলোড করার জন্য কোনো ভিডিও URL পাওয়া যায়নি।")
            
            # --- টাইটেল অটো-কপি করার জন্য পরিবর্তন: <code> ট্যাগ এবং HTML মোড ব্যবহার ---
            caption = f"""
✅ <b>সফলভাবে ডাউনলোড করা হয়েছে!</b>

🎬 <b>টাইটেল:</b> <code>{title}</code>
👤 <b>ক্রিয়েটর:</b> {author_name} (@{username})

📊 <b>পরিসংখ্যান:</b>
❤️ লাইক: {video_data.get('statistics', {}).get('likes', 'N/A')}

🎵 <b>মিউজিক:</b> {video_data.get('music', {}).get('title', 'Original Sound')}
"""
            # --- পরিবর্তন শেষ ---

            
            keyboard = [
                [InlineKeyboardButton("📥 অন্য ভিডিও ডাউনলোড", callback_data="start_download")],
                [InlineKeyboardButton("⭐ বটটিকে রেট দিন", url="https://t.me/")] # Change the URL as needed
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send Thumbnail and then Video
            caption_for_video = caption
            reply_markup_for_video = reply_markup
            if thumbnail:
                try:
                    await update.message.reply_photo(
                        photo=thumbnail,
                        caption=caption,
                        reply_markup=reply_markup,
                        parse_mode='HTML' # parse_mode HTML এ পরিবর্তন
                    )
                    caption_for_video = None
                    reply_markup_for_video = None
                except Exception as e:
                    logger.warning(f"Failed to send thumbnail: {e}")
            
            await update.message.reply_video(
                video=video_url,
                caption=caption_for_video,
                reply_markup=reply_markup_for_video,
                parse_mode='HTML' if caption_for_video else None, # parse_mode HTML এ পরিবর্তন
                supports_streaming=True # For faster sending
            )
            
            await processing_msg.delete()
            
        except ValueError as e:
            logger.error(f"Processing Error: {e}")
            await processing_msg.edit_text(
                f"❌ <b>ডাউনলোড ব্যর্থ</b>\n\nত্রুটি: {e}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error processing video and sending to Telegram: {e}")
            await processing_msg.edit_text(
                "❌ <b>ভিডিও প্রক্রিয়াকরণে ত্রুটি</b>\n\nঅনুগ্রহ করে পরে চেষ্টা করুন বা /help চাপুন।",
                parse_mode='HTML'
            )

    # --- Admin/Moderator Command Handlers ---

    async def add_admin(self, update: Update, context: CallbackContext):
        """Adds a new admin by User ID (Admin only)."""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ <b>অনুমতি নেই।</b> এই কমান্ডটি শুধুমাত্র <b>অ্যাডমিনদের</b> জন্য।", parse_mode='HTML')
            return

        if len(context.args) != 1:
            await update.message.reply_text("ব্যবহার: <code>/addadmin &lt;User ID&gt;</code>\n\nউদাহরণ: <code>/addadmin 123456789</code>", parse_mode='HTML')
            return

        try:
            target_id = int(context.args[0])
            if target_id in self.admins:
                await update.message.reply_text(f"ইউজার ID <b>{target_id}</b> ইতিমধ্যেই একজন অ্যাডমিন।", parse_mode='HTML')
            else:
                self.admins.add(target_id)
                self.moderators.discard(target_id) 
                await update.message.reply_text(f"✅ সফল! ইউজার ID <b>{target_id}</b>-কে নতুন <b>অ্যাডমিন</b> হিসেবে যোগ করা হলো।", parse_mode='HTML')
                logger.info(f"User {target_id} added as Admin by {update.effective_user.id}")
        except ValueError:
            await update.message.reply_text("❌ অবৈধ ইউজার ID। অনুগ্রহ করে শুধুমাত্র পূর্ণসংখ্যা (integer) ID দিন।")

    async def add_moderator(self, update: Update, context: CallbackContext):
        """Adds a new moderator by User ID (Admin only)."""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ <b>অনুমতি নেই।</b> এই কমান্ডটি শুধুমাত্র <b>অ্যাডমিনদের</b> জন্য।", parse_mode='HTML')
            return

        if len(context.args) != 1:
            await update.message.reply_text("ব্যবহার: <code>/addmod &lt;User ID&gt;</code>\n\nউদাহরণ: <code>/addmod 123456789</code>", parse_mode='HTML')
            return

        try:
            target_id = int(context.args[0])
            if target_id in self.admins:
                 await update.message.reply_text(f"ইউজার ID <b>{target_id}</b> ইতিমধ্যেই একজন <b>অ্যাডমিন</b>। মডারেটর হিসেবে যোগ করার প্রয়োজন নেই।", parse_mode='HTML')
            elif target_id in self.moderators:
                await update.message.reply_text(f"ইউজার ID <b>{target_id}</b> ইতিমধ্যেই একজন মডারেটর।", parse_mode='HTML')
            else:
                self.moderators.add(target_id)
                await update.message.reply_text(f"✅ সফল! ইউজার ID <b>{target_id}</b>-কে নতুন <b>মডারেটর</b> হিসেবে যোগ করা হলো।", parse_mode='HTML')
                logger.info(f"User {target_id} added as Moderator by {update.effective_user.id}")
        except ValueError:
            await update.message.reply_text("❌ অবৈধ ইউজার ID। অনুগ্রহ করে শুধুমাত্র পূর্ণসংখ্যা (integer) ID দিন।")

    async def ban_user(self, update: Update, context: CallbackContext):
        """Bans a user by User ID (Admin/Mod only)."""
        # Admin and Moderator can ban
        if not self._is_moderator(update.effective_user.id):
            await update.message.reply_text("⛔ <b>অনুমতি নেই।</b> এই কমান্ডটি শুধুমাত্র <b>অ্যাডমিন/মডারেটরদের</b> জন্য।", parse_mode='HTML')
            return

        if len(context.args) != 1:
            await update.message.reply_text("ব্যবহার: <code>/ban &lt;User ID&gt;</code>\n\nউদাহরণ: <code>/ban 987654321</code>", parse_mode='HTML')
            return

        try:
            target_id = int(context.args[0])
            if target_id in self.admins:
                await update.message.reply_text("❌ <b>অ্যাডমিনদের</b> ব্যান করা যাবে না।", parse_mode='HTML')
            elif target_id in self.banned_users:
                await update.message.reply_text(f"ইউজার ID <b>{target_id}</b> ইতিমধ্যেই ব্যান করা আছে।", parse_mode='HTML')
            else:
                self.banned_users.add(target_id)
                await update.message.reply_text(f"✅ সফল! ইউজার ID <b>{target_id}</b>-কে <b>ব্যান</b> করা হলো।", parse_mode='HTML')
                logger.info(f"User {target_id} banned by {update.effective_user.id}")
        except ValueError:
            await update.message.reply_text("❌ অবৈধ ইউজার ID। অনুগ্রহ করে শুধুমাত্র পূর্ণসংখ্যা (integer) ID দিন।")

    async def unban_user(self, update: Update, context: CallbackContext):
        """Unbans a user by User ID (Admin/Mod only)."""
        # Admin and Moderator can unban
        if not self._is_moderator(update.effective_user.id):
            await update.message.reply_text("⛔ <b>অনুমতি নেই।</b> এই কমান্ডটি শুধুমাত্র <b>অ্যাডমিন/মডারেটরদের</b> জন্য।", parse_mode='HTML')
            return

        if len(context.args) != 1:
            await update.message.reply_text("ব্যবহার: <code>/unban &lt;User ID&gt;</code>\n\nউদাহরণ: <code>/unban 987654321</code>", parse_mode='HTML')
            return

        try:
            target_id = int(context.args[0])
            if target_id not in self.banned_users:
                await update.message.reply_text(f"ইউজার ID <b>{target_id}</b> ইতিমধ্যেই ব্যান করা নেই।", parse_mode='HTML')
            else:
                self.banned_users.discard(target_id)
                await update.message.reply_text(f"✅ সফল! ইউজার ID <b>{target_id}</b>-কে <b>আনব্যান</b> করা হলো।", parse_mode='HTML')
                logger.info(f"User {target_id} unbanned by {update.effective_user.id}")
        except ValueError:
            await update.message.reply_text("❌ অবৈধ ইউজার ID। অনুগ্রহ করে শুধুমাত্র পূর্ণসংখ্যা (integer) ID দিন।")

    async def change_api(self, update: Update, context: CallbackContext):
        """Changes the API URL and/or Key (Admin only)."""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ <b>অনুমতি নেই।</b> এই কমান্ডটি শুধুমাত্র <b>অ্যাডমিনদের</b> জন্য।", parse_mode='HTML')
            return

        if len(context.args) == 0:
            await update.message.reply_text(
                "ব্যবহার:\n"
                "<code>/changeapi url &lt;New URL&gt;</code>\n"
                "<code>/changeapi key &lt;New Key&gt;</code>\n\n"
                f"বর্তমান API URL: <code>{self.api_url}</code>\n"
                f"বর্তমান API Key: <code>{self.api_key}</code>",
                parse_mode='HTML'
            )
            return
        
        # Check command structure
        if len(context.args) < 2:
            await update.message.reply_text("❌ কমান্ডের গঠন সঠিক নয়। দেখুন: <code>/changeapi url &lt;URL&gt;</code> বা <code>/changeapi key &lt;Key&gt;</code>", parse_mode='HTML')
            return

        field = context.args[0].lower()
        new_value = context.args[1]

        if field == 'url':
            self.api_url = new_value
            await update.message.reply_text(f"✅ সফল! নতুন API URL সেট করা হয়েছে: <code>{self.api_url}</code>", parse_mode='HTML')
            logger.info(f"API URL changed to {new_value} by {update.effective_user.id}")
        elif field == 'key':
            self.api_key = new_value
            await update.message.reply_text(f"✅ সফল! নতুন API Key সেট করা হয়েছে: <code>{self.api_key}</code>", parse_mode='HTML')
            logger.info(f"API Key changed to {new_value} by {update.effective_user.id}")
        else:
            await update.message.reply_text("❌ অবৈধ প্যারামিটার। 'url' বা 'key' ব্যবহার করুন।")
            
    async def status(self, update: Update, context: CallbackContext):
        """Shows current bot status (Admin only)"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ <b>অনুমতি নেই।</b> এই কমান্ডটি শুধুমাত্র <b>অ্যাডমিনদের</b> জন্য।", parse_mode='HTML')
            return
            
        status_text = f"""
<b>⚙️ বট স্ট্যাটাস (Admin View)</b>

<b>API সেটিংস:</b>
• API URL: <code>{self.api_url}</code>
• API Key: <code>{self.api_key}</code>

<b>ইউজার ম্যানেজমেন্ট:</b>
• অ্যাডমিন (সংখ্যা): {len(self.admins)}
• মডারেটর (সংখ্যা): {len(self.moderators)}
• ব্যান করা ইউজার (সংখ্যা): {len(self.banned_users)}

<b>অ্যাডমিন/মডারেটর IDs:</b>
• অ্যাডমিন IDs: {', '.join(map(str, self.admins))}
• মডারেটর IDs: {', '.join(map(str, self.moderators))}

<b>অন্যান্য কনফিগ:</b>
• প্রাইমারি অ্যাডমিন: @{PRIMARY_ADMIN_USERNAME}
• সাপোর্ট ইমেইল: {SUPPORT_EMAIL}
"""
        await update.message.reply_text(status_text, parse_mode='HTML')


    def run(self):
        """Run the bot by polling for updates."""
        logger.info("TikTok Downloader Bot is starting...")
        
        self.application.run_polling(poll_interval=1.0)

def main():
    """Main function to run the bot"""
    try:
        # Check for essential library presence
        try:
            import telegram.ext
        except ImportError:
            logger.error("The 'python-telegram-bot' library is not installed. Please run: pip install python-telegram-bot requests")
            return
            
        bot = TikTokDownloaderBot()
        bot.run()
    except Exception as e:
        logger.critical(f"Fatal error in main application: {e}")

if __name__ == '__main__':
    main()
