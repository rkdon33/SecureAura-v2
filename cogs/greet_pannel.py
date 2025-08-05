
import discord
from discord.ext import commands
from discord import app_commands
from database import db

def parse_color(text):
    text = text.strip().lower()
    # Accept formats: "blue", "0x3498db", "#3498db", "3447003", "rgb(52,152,219)"
    named_colors = {
        "blue": 0x3498db,
        "blurple": 0x5865F2,
        "red": 0xe74c3c,
        "green": 0x2ecc71,
        "yellow": 0xf1c40f,
        "orange": 0xe67e22,
        "purple": 0x9b59b6,
        "white": 0xffffff,
        "black": 0x000000,
    }
    if text in named_colors:
        return named_colors[text]
    if text.startswith("0x"):
        try:
            return int(text, 16)
        except:
            return None
    if text.startswith("#"):
        try:
            return int(text[1:], 16)
        except:
            return None
    if text.startswith("rgb"):
        try:
            parts = text.replace("rgb(", "").replace(")", "").split(",")
            r, g, b = [int(x.strip()) for x in parts]
            return (r << 16) + (g << 8) + b
        except:
            return None
    try:
        return int(text)
    except:
        return None

class WelcomeEmbedModal(discord.ui.Modal, title="Welcome Embed Setup"):
    def __init__(self, cog, edit_data=None):
        super().__init__()
        self.cog = cog
        self.edit_data = edit_data
        
        # Pre-fill data if editing
        if edit_data:
            self.title_input.default = edit_data.get("title", "")
            self.description_input.default = edit_data.get("description", "")
            self.color_input.default = self._color_to_string(edit_data.get("color", 0x3498db))
            self.big_thumbnail_input.default = edit_data.get("big_thumbnail", "")
            self.small_thumbnail_input.default = edit_data.get("small_thumbnail", "")

    def _color_to_string(self, color_int):
        """Convert color integer back to hex string"""
        if isinstance(color_int, int):
            return f"#{color_int:06x}"
        return str(color_int)

    title_input = discord.ui.TextInput(
        label="Embed Title (Required)",
        placeholder="Welcome to {server}!",
        max_length=256,
        required=True
    )

    description_input = discord.ui.TextInput(
        label="Embed Description (Required)",
        placeholder="Hello {user}, welcome to our amazing server!",
        style=discord.TextStyle.paragraph,
        max_length=4000,
        required=True
    )

    color_input = discord.ui.TextInput(
        label="Embed Color (Required)",
        placeholder="blue, #3498db, or rgb(52,152,219)",
        max_length=50,
        required=True
    )

    big_thumbnail_input = discord.ui.TextInput(
        label="Big Thumbnail Link (Optional)",
        placeholder="https://example.com/image.png",
        max_length=500,
        required=False
    )

    small_thumbnail_input = discord.ui.TextInput(
        label="Small Thumbnail Link (Optional)",
        placeholder="https://example.com/small_image.png",
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse color
            color_value = parse_color(self.color_input.value)
            if color_value is None:
                await interaction.response.send_message(
                    embed=discord.Embed(description="❌ Invalid color format. Please use color names (blue), hex codes (#3498db), or rgb values (rgb(52,152,219)).", color=discord.Color.red()),
                    ephemeral=True
                )
                return

            # Store data temporarily and ask for footer/channel
            self.cog.temp_embed_data = {
                "title": self.title_input.value,
                "description": self.description_input.value,
                "color": color_value,
                "big_thumbnail": self.big_thumbnail_input.value if self.big_thumbnail_input.value else None,
                "small_thumbnail": self.small_thumbnail_input.value if self.small_thumbnail_input.value else None,
                "is_edit": self.edit_data is not None,
                "original_channel": self.edit_data.get("channel_id") if self.edit_data else None
            }

            # Show footer modal
            footer_modal = WelcomeFooterModal(self.cog, self.edit_data)
            await interaction.response.send_modal(footer_modal)
            
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(description=f"❌ Error processing form: {str(e)}", color=discord.Color.red()),
                ephemeral=True
            )

class WelcomeFooterModal(discord.ui.Modal, title="Footer & Channel Setup"):
    def __init__(self, cog, edit_data=None):
        super().__init__()
        self.cog = cog
        self.edit_data = edit_data
        
        # Pre-fill data if editing
        if edit_data:
            self.footer_text_input.default = edit_data.get("footer_text", "")
            self.footer_icon_input.default = edit_data.get("footer_icon", "")
            # Get channel name for editing
            if edit_data.get("channel_id"):
                try:
                    channel = self.cog.bot.get_channel(edit_data["channel_id"])
                    if channel:
                        self.channel_input.default = channel.name
                except:
                    pass

    footer_text_input = discord.ui.TextInput(
        label="Footer Text (Optional)",
        placeholder="Thanks for joining us!",
        max_length=2048,
        required=False
    )

    footer_icon_input = discord.ui.TextInput(
        label="Footer Icon Link (Optional)",
        placeholder="https://example.com/footer_icon.png",
        max_length=500,
        required=False
    )

    channel_input = discord.ui.TextInput(
        label="Channel ID or Name (Required)",
        placeholder="general or 1234567890123456789",
        max_length=100,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Find channel
            channel = None
            channel_input = self.channel_input.value.strip()

            # Try to find by ID first
            if channel_input.isdigit():
                channel = interaction.guild.get_channel(int(channel_input))

            # If not found, try by name
            if not channel:
                channel = discord.utils.get(interaction.guild.text_channels, name=channel_input.lower())

            if not channel:
                await interaction.response.send_message(
                    embed=discord.Embed(description="❌ Channel not found. Please provide a valid channel name or ID.", color=discord.Color.red()),
                    ephemeral=True
                )
                return

            # Get stored data and complete setup
            embed_data = self.cog.temp_embed_data

            greet_data = {
                "type": "embed",
                "title": embed_data["title"],
                "description": embed_data["description"],
                "color": embed_data["color"],
                "big_thumbnail": embed_data["big_thumbnail"],
                "small_thumbnail": embed_data["small_thumbnail"],
                "footer_text": self.footer_text_input.value if self.footer_text_input.value else None,
                "footer_icon": self.footer_icon_input.value if self.footer_icon_input.value else None,
                "channel_id": channel.id
            }

            # Save to database
            db.set_greet_settings(str(interaction.guild_id), greet_data)

            # Clean up temp data
            self.cog.temp_embed_data = None

            action_text = "updated" if embed_data.get("is_edit") else "configured"
            await interaction.response.send_message(
                embed=discord.Embed(description=f"✅ Embed welcome message {action_text} for {channel.mention}!", color=discord.Color.green()),
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(description=f"❌ Error saving settings: {str(e)}", color=discord.Color.red()),
                ephemeral=True
            )

class EditNormalModal(discord.ui.Modal, title="Edit Normal Welcome Message"):
    def __init__(self, cog, current_data):
        super().__init__()
        self.cog = cog
        self.current_data = current_data
        
        # Pre-fill current data
        self.message_input.default = current_data.get("message", "")
        # Get channel name
        try:
            channel = self.cog.bot.get_channel(current_data["channel_id"])
            if channel:
                self.channel_input.default = channel.name
        except:
            pass

    message_input = discord.ui.TextInput(
        label="Welcome Message",
        placeholder="Welcome {user} to {server}!",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )

    channel_input = discord.ui.TextInput(
        label="Channel ID or Name",
        placeholder="general or 1234567890123456789",
        max_length=100,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Find channel
            channel = None
            channel_input = self.channel_input.value.strip()

            if channel_input.isdigit():
                channel = interaction.guild.get_channel(int(channel_input))

            if not channel:
                channel = discord.utils.get(interaction.guild.text_channels, name=channel_input.lower())

            if not channel:
                await interaction.response.send_message(
                    embed=discord.Embed(description="❌ Channel not found.", color=discord.Color.red()),
                    ephemeral=True
                )
                return

            greet_data = {
                "type": "normal",
                "message": self.message_input.value,
                "channel_id": channel.id
            }

            db.set_greet_settings(str(interaction.guild_id), greet_data)
            
            await interaction.response.send_message(
                embed=discord.Embed(description=f"✅ Normal welcome message updated for {channel.mention}!", color=discord.Color.green()),
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(description=f"❌ Error updating settings: {str(e)}", color=discord.Color.red()),
                ephemeral=True
            )

class EmbedModalView(discord.ui.View):
    def __init__(self, cog, edit_data=None):
        super().__init__(timeout=120)
        self.cog = cog
        self.edit_data = edit_data

    @discord.ui.button(label="Open Embed Form", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = WelcomeEmbedModal(self.cog, self.edit_data)
        await interaction.response.send_modal(modal)

class GreetSetupView(discord.ui.View):
    def __init__(self, cog, author_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.author_id = author_id
        self.value = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        self.value = None

    @discord.ui.button(label="NORMAL", style=discord.ButtonStyle.secondary)
    async def normal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=discord.Embed(description="❌ You are not the setup initiator.", color=discord.Color.red()), ephemeral=True)
            return
        
        await interaction.response.defer()
        self.value = "normal"
        self.stop()

    @discord.ui.button(label="EMBED", style=discord.ButtonStyle.secondary)
    async def embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=discord.Embed(description="❌ You are not the setup initiator.", color=discord.Color.red()), ephemeral=True)
            return
        
        await interaction.response.defer()
        self.value = "embed"
        self.stop()

class GreetEditView(discord.ui.View):
    def __init__(self, cog, author_id, current_data):
        super().__init__(timeout=60)
        self.cog = cog
        self.author_id = author_id
        self.current_data = current_data

    @discord.ui.button(label="Edit Settings", style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=discord.Embed(description="❌ You are not authorized to edit.", color=discord.Color.red()), ephemeral=True)
            return

        if self.current_data["type"] == "normal":
            modal = EditNormalModal(self.cog, self.current_data)
            await interaction.response.send_modal(modal)
        elif self.current_data["type"] == "embed":
            view = EmbedModalView(self.cog, self.current_data)
            embed = discord.Embed(
                title="Edit Embed Setup", 
                description="Click the button below to edit your embed welcome message.", 
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Remove Settings", style=discord.ButtonStyle.danger)
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=discord.Embed(description="❌ You are not authorized to remove.", color=discord.Color.red()), ephemeral=True)
            return

        db.remove_greet_settings(str(interaction.guild_id))
        await interaction.response.send_message(
            embed=discord.Embed(description="✅ Welcome message settings removed!", color=discord.Color.green()),
            ephemeral=True
        )

class GreetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_embed_data = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send greet message when a member joins"""
        try:
            data = db.get_greet_settings(str(member.guild.id))
            if not data:
                return

            channel = member.guild.get_channel(data["channel_id"])
            if not channel:
                return

            await self.send_greet(member.guild, member, channel)
        except Exception as e:
            print(f"Error sending greet message: {e}")

    @app_commands.command(name="setup_greet", description="Set up the welcome/greet panel")
    async def setup_greet(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(embed=discord.Embed(description="❌ You need Manage Server permission.", color=discord.Color.red()), ephemeral=True)
            return

        # Check if greet settings already exist
        existing_data = db.get_greet_settings(str(interaction.guild_id))
        
        if existing_data:
            # Show current settings with edit option
            channel = interaction.guild.get_channel(existing_data["channel_id"])
            channel_mention = channel.mention if channel else "Unknown Channel"
            
            if existing_data["type"] == "normal":
                description = f"**Current Type:** Normal Message\n**Channel:** {channel_mention}\n**Message:** {existing_data['message'][:100]}{'...' if len(existing_data['message']) > 100 else ''}"
            else:
                description = f"**Current Type:** Embed Message\n**Channel:** {channel_mention}\n**Title:** {existing_data['title']}\n**Description:** {existing_data['description'][:100]}{'...' if len(existing_data['description']) > 100 else ''}"
            
            embed = discord.Embed(
                title="Welcome Settings Already Configured",
                description=description,
                color=discord.Color.orange()
            )
            view = GreetEditView(self, interaction.user.id, existing_data)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True, delete_after=60)
            return

        # Show setup options for new configuration
        view = GreetSetupView(self, interaction.user.id)
        embed = discord.Embed(
            title="Welcome Panel Setup",
            description="Choose your welcome message style:\n\n**NORMAL**: Simple text message\n**EMBED**: Rich embed message with customization",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True, delete_after=60)
        await view.wait()

        if view.value == "normal":
            await self.normal_flow(interaction)
        elif view.value == "embed":
            await self.embed_flow(interaction)
        else:
            try:
                await interaction.followup.send(embed=discord.Embed(description="⏰ Setup cancelled or timed out.", color=discord.Color.orange()), ephemeral=True)
            except:
                pass

    async def normal_flow(self, interaction):
        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel
        
        try:
            # Step 1: Ask for message
            embed = discord.Embed(title="Step 1: Welcome Message", description="Please type your welcome message (use `{user}` for mention and `{server}` for server name):", color=discord.Color.blue())
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            msg_normal = await self.bot.wait_for('message', timeout=120, check=check)
            await msg_normal.delete()  # Clean up user message
            
            # Step 2: Ask for channel
            embed = discord.Embed(title="Step 2: Channel", description="Please mention the channel for welcome messages (e.g., #general):", color=discord.Color.blue())
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            msg_chan = await self.bot.wait_for('message', timeout=60, check=check)
            await msg_chan.delete()  # Clean up user message
            
            if not msg_chan.channel_mentions:
                await interaction.followup.send(embed=discord.Embed(description="❌ Please mention a valid channel. Setup cancelled.", color=discord.Color.red()), ephemeral=True)
                return
                
            channel = msg_chan.channel_mentions[0]
            
            greet_data = {
                "type": "normal",
                "message": msg_normal.content,
                "channel_id": channel.id
            }
            db.set_greet_settings(str(interaction.guild_id), greet_data)
            await interaction.followup.send(embed=discord.Embed(description=f"✅ Normal welcome message set in {channel.mention}!", color=discord.Color.green()), ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description="❌ Setup timed out or failed. Please try again.", color=discord.Color.red()), ephemeral=True)

    async def embed_flow(self, interaction):
        view = EmbedModalView(self)
        embed = discord.Embed(
            title="Embed Setup", 
            description="Click the button below to open the embed setup form.", 
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="greettest", description="Test your current welcome/greet message")
    async def greettest_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.send_greet(interaction.guild, interaction.user, interaction.channel)
        await interaction.followup.send(embed=discord.Embed(description="✅ Test greet message sent above!", color=discord.Color.green()), ephemeral=True)

    @commands.command(name="greettest")
    async def greettest_prefix(self, ctx):
        await self.send_greet(ctx.guild, ctx.author, ctx.channel)

    async def send_greet(self, guild, member, target_channel):
        try:
            data = db.get_greet_settings(str(guild.id))
            if not data:
                embed = discord.Embed(description="❌ No greet message is set up for this server. Use `/setup_greet` to configure one.", color=discord.Color.orange())
                await target_channel.send(embed=embed, delete_after=10)
                return

            if data["type"] == "normal":
                msg = data["message"].replace("{user}", member.mention).replace("{server}", guild.name)
                await target_channel.send(msg)
            elif data["type"] == "embed":
                embed = discord.Embed(
                    title=data["title"].replace("{user}", member.display_name).replace("{server}", guild.name),
                    description=data["description"].replace("{user}", member.mention).replace("{server}", guild.name),
                    color=data.get("color", 0x3498db)
                )

                if data.get("big_thumbnail"):
                    embed.set_image(url=data["big_thumbnail"])

                if data.get("small_thumbnail"):
                    embed.set_thumbnail(url=data["small_thumbnail"])

                if data.get("footer_text"):
                    footer_text = data["footer_text"].replace("{user}", member.display_name).replace("{server}", guild.name)
                    if data.get("footer_icon"):
                        embed.set_footer(text=footer_text, icon_url=data["footer_icon"])
                    else:
                        embed.set_footer(text=footer_text)

                await target_channel.send(embed=embed)
        except Exception as e:
            print(f"Error in send_greet: {e}")

async def setup(bot):
    await bot.add_cog(GreetCog(bot))
