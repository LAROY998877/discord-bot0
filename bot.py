import discord
from discord.ext import commands
import random

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# قائمة الأسئلة التلقائية (يمكنك تعديلها وإضافة ما تشاء)
QUESTIONS = [
    "هل سبق لك ونسيت محفظتك عند الكاشير؟ 💸",
    "ما هو أغبى موقف سويته وأنت صغير؟ 🧸",
    "لو ملكت القوة لتغيير قانون واحد بالدولة، شتغير؟ ⚖️",
    "شنو أكثر شيء يخيفك بالحياة وتخبيها عن الكل؟ 🌙",
    "لو رجع فيك الزمن لورا، أي سنة تختار تعيشها من جديد؟ ⏳"
]

class GameView(discord.ui.View):
    def __init__(self, player: discord.Member):
        super().__init__(timeout=60)
        self.player = player

    @discord.ui.button(label="نفذ (بطل)", style=discord.ButtonStyle.green, emoji="🏆")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player:
            await interaction.response.send_message("❌ هذا الدور ليس دورك!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⚡ | تم التنفيذ بنجاح!",
            description=f"البطل **{self.player.mention}** كسب التحدي وأثبت شجاعته! 🔥",
            color=discord.Color.gold()
        )
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="انسحاب (جبان)", style=discord.ButtonStyle.danger, emoji="🏳️")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player:
            await interaction.response.send_message("❌ هذا الدور ليس دورك!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🐔 | انسحاب!",
            description=f"للأسف اللاعب **{self.player.mention}** انسحب من المعركة واستسلم! 💨",
            color=discord.Color.red()
        )
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(embed=embed, view=self)


class StartGameView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.players = []

    @discord.ui.button(label="دخول المعركة", style=discord.ButtonStyle.success, emoji="⚔️")
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.players:
            self.players.append(interaction.user)
            
            embed = interaction.message.embeds[0]
            embed.description = f"**اللاعبون المشاركون ({len(self.players)}):**\n" + "\n".join([f"🔹 {p.mention}" for p in self.players])
            await interaction.message.edit(embed=embed)
            await interaction.response.send_message("✅ تم انضمامك بنجاح للمعركة!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ أنت منضم مسبقاً!", ephemeral=True)

    @discord.ui.button(label="بدء التحدي", style=discord.ButtonStyle.primary, emoji="🚀")
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.players:
            await interaction.response.send_message("⚠️ لا يوجد لاعبون منضمون حتى تبدأ!", ephemeral=True)
            return
        
        # اختيار لاعب عشوائي وسؤال تلقائي
        chosen_player = random.choice(self.players)
        random_question = random.choice(QUESTIONS)

        fay_embed = discord.Embed(
            title="✨ | ساحة التحدي الكبرى",
            description=f"**السؤال التلقائي:**\n```{random_question}```",
            color=discord.Color.from_rgb(47, 49, 54)
        )
        fay_embed.set_footer(text=f"دور اللاعب: {chosen_player.display_name} | الإشراف الفخم", icon_url=chosen_player.display_avatar.url)

        view = GameView(chosen_player)
        await interaction.message.edit(content=f"🎯 الدور الآن على: {chosen_player.mention}", embed=fay_embed, view=view)
        await interaction.response.send_message("🔥 انطلقت الجولة بنجاح!", ephemeral=True)


@bot.command()
async def تحدي(ctx):
    embed = discord.Embed(
        title="🌟 | غرفة إعداد التحديات الأسطورية",
        description="**اضغط على زر (دخول المعركة) للانضمام، ثم (بدء التحدي) لتبدأ الأسئلة التلقائية الفخمة!**\n\n**اللاعبون المشاركون (0):**",
        color=discord.Color.dark_embed()
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    
    view = StartGameView()
    await ctx.send(embed=embed, view=view)

bot.run("YOUR_BOT_TOKEN")
