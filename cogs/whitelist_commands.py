import discord
from discord.ext import commands
from discord import app_commands
from .whitelist_utils import get_whitelist, add_to_whitelist, remove_from_whitelist, is_whitelisted

class WhitelistCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whitelist", description="Manage whitelist settings")
    @app_commands.describe(
        action="Choose an action",
        user="User to add/remove from whitelist"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="list", value="list"),
        app_commands.Choice(name="check", value="check")
    ])
    async def whitelist(self, interaction: discord.Interaction, action: str, user: discord.Member = None):
        # Check if user has administrator permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need Administrator permissions to manage whitelist."
            )
            return

        guild_id = interaction.guild_id

        if action == "add":
            if not user:
                await interaction.response.send_message(
                    "❌ Please specify a user to add to the whitelist."
                )
                return

            if is_whitelisted(guild_id, user.id):
                await interaction.response.send_message(
                    f"❌ {user.mention} is already whitelisted."
                )
                return

            add_to_whitelist(guild_id, user.id)
            embed = discord.Embed(
                title="✅ User Added to Whitelist",
                description=f"{user.mention} has been added to the whitelist.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

        elif action == "remove":
            if not user:
                await interaction.response.send_message(
                    "❌ Please specify a user to remove from the whitelist."
                )
                return

            if not is_whitelisted(guild_id, user.id):
                await interaction.response.send_message(
                    f"❌ {user.mention} is not in the whitelist."
                )
                return

            remove_from_whitelist(guild_id, user.id)
            embed = discord.Embed(
                title="✅ User Removed from Whitelist",
                description=f"{user.mention} has been removed from the whitelist.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

        elif action == "list":
            whitelist = get_whitelist(guild_id)
            if not whitelist:
                embed = discord.Embed(
                    title="📋 Whitelist",
                    description="No users are currently whitelisted.",
                    color=discord.Color.blue()
                )
            else:
                user_mentions = []
                for user_id in whitelist:
                    user_obj = interaction.guild.get_member(user_id)
                    if user_obj:
                        user_mentions.append(f"• {user_obj.mention}")
                    else:
                        user_mentions.append(f"• <@{user_id}> (User left)")

                embed = discord.Embed(
                    title="📋 Whitelist",
                    description=f"**Whitelisted Users ({len(whitelist)}):**\n" + "\n".join(user_mentions),
                    color=discord.Color.blue()
                )
            await interaction.response.send_message(embed=embed)

        elif action == "check":
            if not user:
                await interaction.response.send_message(
                    "❌ Please specify a user to check."
                )
                return

            is_whitelisted_user = is_whitelisted(guild_id, user.id)
            status = "✅ Whitelisted" if is_whitelisted_user else "❌ Not Whitelisted"
            color = discord.Color.green() if is_whitelisted_user else discord.Color.red()

            embed = discord.Embed(
                title="🔍 Whitelist Status",
                description=f"{user.mention} is **{status.split(' ')[1].lower()}**.",
                color=color
            )
            await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=20)

    @app_commands.command(name="whitelistclear", description="Clear all users from whitelist")
    async def whitelistclear(self, interaction: discord.Interaction):
        # Check if user has administrator permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need Administrator permissions to manage whitelist."
            )
            return

        guild_id = interaction.guild_id
        whitelist = get_whitelist(guild_id)

        if not whitelist:
            await interaction.response.send_message(
                "❌ Whitelist is already empty."
            )
            return

        # Create confirmation view
        view = ConfirmClearView(guild_id)
        embed = discord.Embed(
            title="⚠️ Confirm Clear Whitelist",
            description=f"Are you sure you want to remove all **{len(whitelist)}** users from the whitelist?\n\n**This action cannot be undone!**",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ConfirmClearView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=30)
        self.guild_id = guild_id

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.danger)
    async def confirm_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        from .whitelist_utils import save_whitelist
        save_whitelist(self.guild_id, [])

        embed = discord.Embed(
            title="✅ Whitelist Cleared",
            description="All users have been removed from the whitelist.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Action Cancelled",
            description="Whitelist clear has been cancelled.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        # Disable all buttons when view times out
        for item in self.children:
            item.disabled = True

async def setup(bot):
    await bot.add_cog(WhitelistCommands(bot))