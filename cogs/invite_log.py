import discord
from discord.ext import commands

# Set your channel IDs here
LANDING_LOG_CHANNEL_ID = 1386397028354887882  # Replace with your actual channel ID for landing logs
PERMALINK_CHANNEL_ID = 1387888344691642528   # Replace with your actual channel ID for permalinks

class InviteLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # Channel for landing log
        landing_channel = self.bot.get_channel(LANDING_LOG_CHANNEL_ID)
        if landing_channel:
            try:
                await landing_channel.send(
                    f"**SecureAura just landed to {guild.name}**"
                )
            except Exception as e:
                print(f"Error sending landing log: {e}")

        # Channel for permanent invite link
        permalink_channel = self.bot.get_channel(PERMALINK_CHANNEL_ID)
        # Try to get a permanent invite (max_age=0 means never expire)
        invite_url = None
        try:
            # Try to find a channel where bot can create invites
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).create_instant_invite:
                    invite = await channel.create_invite(max_age=0, max_uses=0, unique=True, reason="SecureAura landing permanent invite")
                    invite_url = invite.url
                    break
        except Exception as e:
            print(f"Error creating invite: {e}")

        if permalink_channel and invite_url:
            try:
                await permalink_channel.send(
                    f"Permanent invite to **{guild.name}**: {invite_url}"
                )
            except Exception as e:
                print(f"Error sending invite link: {e}")

async def setup(bot):
    await bot.add_cog(InviteLog(bot))