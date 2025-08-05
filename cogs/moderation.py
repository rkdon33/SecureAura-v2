import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Kick
    @commands.hybrid_command(name="kick", with_app_command=True, description="Kick a member")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        try:
            await member.kick(reason=reason)
            await ctx.send(f"<:broken_pickaxe:1402342321953177671> {member.mention} has been kicked.")
        except Exception as e:
            await ctx.send(f"<:Unverified:1402342155489640521> Failed to kick: {e}")

    # Ban
    @commands.hybrid_command(name="ban", with_app_command=True, description="Ban a member")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        try:
            await member.ban(reason=reason)
            await ctx.send(f"<a:Verified:1402341882352111709> {member.mention} has been banned.")
        except Exception as e:
            await ctx.send(f"<:Unverified:1402342155489640521> Failed to ban: {e}")

    # Mute
    @commands.hybrid_command(name="mute", with_app_command=True, description="Mute a member (timeout)")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: int = 10, *, reason: str = None):
        # duration in minutes
        try:
            await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=duration), reason=reason)
            await ctx.send(f"<a:Verified:1402341882352111709> {member.mention} has been muted for {duration} minutes.")
        except Exception as e:
            await ctx.send(f"<:Unverified:1402342155489640521> Failed to mute: {e}")

    # Clear messages
    @commands.hybrid_command(name="clear", with_app_command=True, description="Clear messages")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        try:
            await ctx.channel.purge(limit=amount+1)
            await ctx.send(f"<a:Verified:1402341882352111709> Cleared {amount} messages.", delete_after=5)
        except Exception as e:
            await ctx.send(f"<:Unverified:1402342155489640521> Failed to clear messages: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))