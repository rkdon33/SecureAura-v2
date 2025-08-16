
import discord
from discord.ext import commands
from database import db
import asyncio

class UpdateSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 748814695825277002
        self.update_channel_name = "aura-update"

    async def create_update_channel(self, guild):
        """Create a locked update channel for the guild"""
        try:
            # Check if channel already exists
            existing_channel = discord.utils.get(guild.text_channels, name=self.update_channel_name)
            if existing_channel:
                # Save existing channel to database
                db.save_update_channel(guild.id, existing_channel.id)
                return existing_channel

            # Create permissions - only owner and bot can access
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # Create the channel
            channel = await guild.create_text_channel(
                self.update_channel_name,
                overwrites=overwrites,
                reason="SecureAura Bot private update channel"
            )

            # Save to database
            db.save_update_channel(guild.id, channel.id)

            # Send welcome message
            embed = discord.Embed(
                title="🔒 **Private Update Channel**",
                description=(
                    "This is a private channel that will receive important updates and announcements from SecureAura Bot.\n\n"
                    "⚠️ **Important:** \n"
                    "• This channel is private and locked - only the server owner and bot can access it\n"
                    "• Please don't rename, delete, or modify permissions of this channel\n"
                    "• It will be automatically recreated if removed or renamed"
                ),
                color=0x00FFFF
            )
            embed.set_footer(text="SecureAura Bot Update System")
            
            await channel.send(embed=embed)
            return channel

        except Exception as e:
            print(f"Error creating update channel in {guild.name}: {e}")
            return None

    @commands.command(name="auraupdate")
    async def send_update(self, ctx, *, message: str):
        """Send update message to all servers (Owner only)"""
        if ctx.author.id != self.owner_id:
            await ctx.send("❌ Only the bot owner can use this command.", delete_after=5)
            return

        try:
            await ctx.send("📡 Sending update to all servers...")
            
            successful_sends = 0
            failed_sends = 0
            created_channels = 0

            for guild in self.bot.guilds:
                try:
                    # Get update channel from database
                    channel_id = db.get_update_channel(guild.id)
                    update_channel = None

                    if channel_id:
                        update_channel = guild.get_channel(channel_id)
                    
                    # If channel doesn't exist or was deleted, create new one
                    if not update_channel:
                        update_channel = await self.create_update_channel(guild)
                        if update_channel:
                            created_channels += 1

                    if update_channel:
                        # Create update embed
                        embed = discord.Embed(
                            title="📢 SecureAura Update",
                            description=message,
                            color=0x00FFFF,
                            timestamp=discord.utils.utcnow()
                        )
                        embed.set_footer(text="SecureAura Bot Updates", icon_url=self.bot.user.display_avatar.url)
                        
                        await update_channel.send(embed=embed)
                        successful_sends += 1
                    else:
                        failed_sends += 1

                except Exception as e:
                    print(f"Failed to send update to {guild.name}: {e}")
                    failed_sends += 1

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)

            # Send summary
            summary_embed = discord.Embed(
                title="📊 Update Summary",
                color=0x00FF00 if failed_sends == 0 else 0xFFFF00
            )
            summary_embed.add_field(name="✅ Successful", value=str(successful_sends), inline=True)
            summary_embed.add_field(name="❌ Failed", value=str(failed_sends), inline=True)
            summary_embed.add_field(name="🆕 Channels Created", value=str(created_channels), inline=True)
            
            await ctx.send(embed=summary_embed)

        except Exception as e:
            await ctx.send(f"❌ Error sending update: {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Create update channel when bot joins a new server"""
        try:
            await asyncio.sleep(2)  # Wait a bit for the bot to settle
            await self.create_update_channel(guild)
        except Exception as e:
            print(f"Error creating update channel on guild join {guild.name}: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Recreate update channel if it gets deleted"""
        if channel.name == self.update_channel_name:
            try:
                # Remove from database
                db.remove_update_channel(channel.guild.id)
                
                # Wait a moment then recreate
                await asyncio.sleep(1)
                await self.create_update_channel(channel.guild)
            except Exception as e:
                print(f"Error recreating deleted update channel in {channel.guild.name}: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Handle channel rename - recreate if update channel is renamed"""
        if before.name == self.update_channel_name and after.name != self.update_channel_name:
            try:
                # Update channel was renamed, recreate it
                await self.create_update_channel(after.guild)
            except Exception as e:
                print(f"Error handling renamed update channel in {after.guild.name}: {e}")

async def setup(bot):
    await bot.add_cog(UpdateSystem(bot))
