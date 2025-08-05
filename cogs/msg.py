import discord
from discord.ext import commands

class Msg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="msg", with_app_command=True, description="Send a message as the bot")
    @commands.has_permissions(administrator=True)
    async def msg(self, ctx, channel: discord.TextChannel, *, message: str):
        try:
            await channel.send(message)
            await ctx.send(f"<a:Verified:1402341882352111709> Message sent to {channel.mention}", delete_after=3)
        except Exception as e:
            await ctx.send(f"<:Unverified:1402342155489640521> Failed to send message: {e}", delete_after=5)

async def setup(bot):
    await bot.add_cog(Msg(bot))