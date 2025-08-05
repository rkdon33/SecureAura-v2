import discord
from discord.ext import commands
from discord import app_commands

def load_log_channels():
    # This function is kept for backward compatibility but uses MongoDB now
    from database import db
    return db.get_all_log_channels()

# Define the group ONCE at the module level
logschannel_group = app_commands.Group(
    name="logschannel",
    description="Log channel management"
)

@logschannel_group.command(name="create", description="Create or set the log channel for this server as #logs-secureaura")
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
async def logschannel_create(interaction: discord.Interaction):
    guild = interaction.guild
    bot_member = guild.me
    owner = guild.owner

    log_channel = discord.utils.get(guild.text_channels, name="logs-secureaura")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        owner: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        bot_member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    if not log_channel:
        log_channel = await guild.create_text_channel("logs-secureaura", overwrites=overwrites, reason="Logs channel for bot security and moderation.")
        await interaction.response.send_message(f"Created and locked log channel: {log_channel.mention}", ephemeral=True)
    else:
        await log_channel.edit(overwrites=overwrites)
        await interaction.response.send_message(f"Log channel set and locked: {log_channel.mention}", ephemeral=True)

    # Save to MongoDB
    interaction.client.db.save_log_channel(guild.id, log_channel.id)
    interaction.client.log_channels[guild.id] = log_channel.id

class LogChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, "log_channels"):
            bot.log_channels = load_log_channels()

    # Optionally, block prefix command and respond with a hint
    @commands.command(name="logs")
    async def logs_prefix(self, ctx):
        await ctx.send("This command is only available as a slash command: `/logschannel create`.", delete_after=5)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.strip().lower().startswith("?logs"):
            try:
                await message.channel.send("Please use the `/logschannel create` slash command for log channel setup.", delete_after=5)
            except Exception:
                pass

    async def cog_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You need Administrator permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

    async def cog_load(self):
        # Only add the group if it's not already added
        if not any(cmd.name == logschannel_group.name for cmd in self.bot.tree.get_commands()):
            self.bot.tree.add_command(logschannel_group)

async def setup(bot):
    await bot.add_cog(LogChannel(bot))