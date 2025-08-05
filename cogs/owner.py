
import discord
from discord.ext import commands
from discord import app_commands

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 748814695825277002
        self.support_link = "https://discord.gg/ERYMCnhWjG"

    @commands.hybrid_command(name="owner", description="Display bot owner information")
    async def owner(self, ctx):
        """Show owner details with profile picture, name, and Discord ID"""
        try:
            # Get owner user object
            owner = await self.bot.fetch_user(self.owner_id)
            
            # Create embed with cyan color
            embed = discord.Embed(
                title="<:Owner_Founder:1402341594601881703> Bot Owner Information",
                color=0x00FFFF  # Cyan color
            )
            
            # Add owner details
            embed.add_field(
                name="👤 Owner Name",
                value=f"**{owner.display_name}**",
                inline=False
            )
            
            embed.add_field(
                name="🆔 Discord ID",
                value=f"`{self.owner_id}`",
                inline=False
            )
            
            embed.add_field(
                name="💬 Support Server",
                value=f"[Join Support Server]({self.support_link})",
                inline=False
            )
            
            # Set owner's profile picture as thumbnail
            embed.set_thumbnail(url=owner.display_avatar.url)
            
            # Add footer
            embed.set_footer(
                text="SecureAura Bot Owner",
                icon_url=owner.display_avatar.url
            )
            
            # Create view with support server button
            view = discord.ui.View()
            support_button = discord.ui.Button(
                label="🔗 Support Server",
                url=self.support_link,
                style=discord.ButtonStyle.link,
                emoji="💬"
            )
            view.add_item(support_button)
            
            await ctx.send(embed=embed, view=view)
            
        except discord.NotFound:
            # Fallback if owner can't be fetched
            embed = discord.Embed(
                title="<:Owner_Founder:1402341594601881703> Bot Owner Information",
                color=0x00FFFF
            )
            
            embed.add_field(
                name="🆔 Owner Discord ID",
                value=f"`{self.owner_id}`",
                inline=False
            )
            
            embed.add_field(
                name="💬 Support Server",
                value=f"[Join Support Server]({self.support_link})",
                inline=False
            )
            
            embed.set_footer(text="SecureAura Bot Owner")
            
            view = discord.ui.View()
            support_button = discord.ui.Button(
                label="🔗 Support Server",
                url=self.support_link,
                style=discord.ButtonStyle.link,
                emoji="💬"
            )
            view.add_item(support_button)
            
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            await ctx.send(f"❌ An error occurred while fetching owner information: {e}")

async def setup(bot):
    await bot.add_cog(Owner(bot))
