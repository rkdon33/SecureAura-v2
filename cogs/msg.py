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
            await ctx.send(f"Sent message to {channel.mention}.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Failed to send message: {e}")

async def setup(bot):
    await bot.add_cog(Msg(bot))