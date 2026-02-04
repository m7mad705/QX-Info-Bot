import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View
import os

from config import (
    BOT_TOKEN, PANEL_CHANNEL_ID, BANNER_IMAGE, 
    COLORS, TEXTS, JOBS_DATABASE
)

# ==========================================
# 🤖 البوت
# ==========================================

class BuletoBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.default(),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="الوظائف والخبرات"
            )
        )
        self.panel_message = None
    
    async def on_ready(self):
        print(f"✅ {self.user.name} جاهز للعمل!")
        
        if PANEL_CHANNEL_ID:
            await self.send_or_update_panel()
        
        try:
            synced = await self.tree.sync()
            print(f"📋 تم مزامنة {len(synced)} أمر")
        except Exception as e:
            print(f"❌ خطأ في المزامنة: {e}")
    
    async def send_or_update_panel(self):
        """إرسال لوحة جديدة أو تحديث القديمة"""
        try:
            channel = self.get_channel(PANEL_CHANNEL_ID)
            if not channel:
                print(f"❌ ما لقيت الروم: {PANEL_CHANNEL_ID}")
                return
            
            # إنشاء الـ Embed والـ View
            embed = create_main_embed()
            view = MainView()
            
            # التحقق إذا الصورة محلية
            file = None
            if BANNER_IMAGE and not BANNER_IMAGE.startswith(("http://", "https://")):
                if os.path.exists(BANNER_IMAGE):
                    file = discord.File(BANNER_IMAGE, filename="banner.png")
                    embed.set_image(url="attachment://banner.png")
                else:
                    print(f"⚠️ ملف الصورة ما لقيته: {BANNER_IMAGE}")
            
            # محاولة تحديث رسالة قديمة
            async for message in channel.history(limit=10):
                if message.author == self.user and message.embeds:
                    if file:
                        await message.edit(embed=embed, view=view, attachments=[file])
                    else:
                        await message.edit(embed=embed, view=view)
                    self.panel_message = message
                    print(f"🔄 تم تحديث اللوحة في: {channel.name}")
                    return
            
            # إرسال رسالة جديدة
            if file:
                self.panel_message = await channel.send(embed=embed, view=view, file=file)
            else:
                self.panel_message = await channel.send(embed=embed, view=view)
            print(f"📋 تم إرسال لوحة جديدة في: {channel.name}")
            
        except Exception as e:
            print(f"❌ خطأ: {e}")

bot = BuletoBot()

# ==========================================
# 🎨 دوال تنسيق الرسائل
# ==========================================

def create_main_embed():
    """اللوحة الرئيسية"""
    embed = discord.Embed(
        title=f"⚡ {TEXTS['main_title']}",
        description=f"**{TEXTS['subtitle']}**",
        color=COLORS["primary"]
    )
    
    if BANNER_IMAGE:
        image_path = BANNER_IMAGE.strip()
        if image_path.startswith(("http://", "https://")):
            embed.set_image(url=image_path)
    
    embed.set_footer(text=TEXTS["bot_name"])
    return embed

def create_job_embed(job_name, job_data):
    """
    إنشاء Embed الوظيفة الخاصة بالترتيب الجديد:
    1. 📦 المستوى المطلوب (الأيقونة)
    2. 📊 الخبرة المطلوبة: X
    3. منطقة البيع
    4. 🏭 خارج الميناء / 💠 الميناء
    5. المكافآت من الكونفق (الخبرة والفلوس)
    """
    embed = discord.Embed(color=COLORS["embed_bg"])
    
    # العنوان: 🏢 اسم الشركة
    embed.title = f"{job_data['emoji']} {job_name}"
    
    # 1. 📦 المستوى المطلوب (الأيقونة)
    embed.add_field(
        name="",
        value=f"{job_data['icon']} المستوى المطلوب",
        inline=False
    )
    
    # 2. 📊 الخبرة المطلوبة: X
    embed.add_field(
        name="",
        value=f"📊 الخبرة المطلوبة: {job_data['experience']} 📊",
        inline=False
    )
    
    # 3. منطقة البيع (عنوان)
    embed.add_field(
        name="",
        value="**منطقة البيع**",
        inline=False
    )
    
    # 4. الموقع (بدون الرقم)
    location_type = job_data['location_type']
    
    if location_type == "ميناء":
        embed.add_field(
            name="",
            value=f"💠 الميناء",
            inline=False
        )
    else:
        embed.add_field(
            name="",
            value=f"🏭 خارج الميناء",
            inline=False
        )
    
    # 5. المكافآت من الكونفق (التغيير هنا)
    rewards = job_data.get('rewards', {'exp': 250, 'money': 500})
    rewards_text = (
        f"**المكافأة الممنوحة من الوظيفة**\n\n"
        f"الخبرة : {rewards['exp']}\n"
        f"الفلوس : {rewards['money']}"
    )
    
    embed.add_field(
        name="",
        value=rewards_text,
        inline=False
    )
    
    return embed

# ==========================================
# 📋 القائمة المنسدلة
# ==========================================

class JobsDropdown(Select):
    def __init__(self):
        options = []
        for job_name, job_data in JOBS_DATABASE.items():
            options.append(discord.SelectOption(
                label=job_name,
                emoji=job_data["icon"],
                description="",  # وصف فارغ
                value=job_name
            ))
        
        super().__init__(
            placeholder=TEXTS["select_placeholder"],
            options=options,
            custom_id="jobs_dropdown"
        )
    
    async def callback(self, interaction: discord.Interaction):
        job_name = self.values[0]
        job_data = JOBS_DATABASE[job_name]
        
        # إنشاء Embed بدل النص العادي
        embed = create_job_embed(job_name, job_data)
        
        # رسالة خاصة بالـ Embed
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

class MainView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(JobsDropdown())

# ==========================================
# ⚡ الأوامر
# ==========================================

@bot.tree.command(name="تحديث_اللوحة", description="تحديث لوحة الوظائف (للأدمن)")
async def refresh_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ للأدمن فقط", ephemeral=True)
        return
    
    await bot.send_or_update_panel()
    await interaction.response.send_message("✅ تم تحديث اللوحة", ephemeral=True)

# ==========================================
# 🚀 تشغيل
# ==========================================

if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "ضع_توكن_البوت_هنا":
        print("❌ خطأ: ضع التوكن في config.py")
    else:
        bot.run(BOT_TOKEN)