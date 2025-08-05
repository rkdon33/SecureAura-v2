import discord
from discord.ext import commands
from discord import app_commands
from database import db
import re

def parse_color(color_str):
    """Parse color from various formats"""
    if not color_str:
        return 0x3498db

    color_str = color_str.strip().lower()

    # Named colors
    colors = {
        'red': 0xff0000, 'green': 0x00ff00, 'blue': 0x0000ff,
        'yellow': 0xffff00, 'orange': 0xffa500, 'purple': 0x800080,
        'pink': 0xffc0cb, 'black': 0x000000, 'white': 0xffffff,
        'gray': 0x808080, 'grey': 0x808080, 'blurple': 0x5865f2
    }

    if color_str in colors:
        return colors[color_str]

    # Hex colors
    if color_str.startswith('#'):
        try:
            return int(color_str[1:], 16)
        except:
            return 0x3498db

    if color_str.startswith('0x'):
        try:
            return int(color_str, 16)
        except:
            return 0x3498db

    # Try as direct number
    try:
        return int(color_str)
    except:
        return 0x3498db

def is_valid_image_url(url):
    """Enhanced URL validation supporting Discord CDN and various sources"""
    if not url:
        return True

    url = url.strip()

    # Check for valid URL format
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(url):
        return False

    # Supported domains and patterns
    supported_patterns = [
        # Discord CDN
        r'cdn\.discordapp\.com',
        r'media\.discordapp\.net',
        # Popular image hosts
        r'imgur\.com',
        r'i\.imgur\.com',
        r'gyazo\.com',
        r'i\.gyazo\.com',
        r'prnt\.sc',
        r'lightshot\.com',
        # Generic image extensions
        r'.*\.(png|jpg|jpeg|gif|webp|bmp|svg)(\?.*)?$'
    ]

    # Check if URL matches any supported pattern
    for pattern in supported_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True

    return False

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            embed = discord.Embed(
                description="❌ **Access Denied** - Only the command user can interact with these buttons.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Confirm Delete', style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        db.remove_greet_settings(str(interaction.guild.id))
        embed = discord.Embed(
            title="<a:Verified:1402341882352111709> Welcome Settings Deleted",
            description=f"Welcome message settings have been permanently removed by {interaction.user.mention}.",
            color=0x27ae60
        )
        embed.set_footer(text="All configuration data has been cleared")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="<:Unverified:1402342155489640521> Action Cancelled",
            description="Operation cancelled - Welcome settings deletion was aborted and no changes were made.",
            color=0x3498db
        )
        embed.set_footer(text="Your settings remain unchanged")
        await interaction.response.edit_message(embed=embed, view=None)

class ConfirmEditView(discord.ui.View):
    def __init__(self, user_id, edit_type, current_data):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.edit_type = edit_type
        self.current_data = current_data

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            embed = discord.Embed(
                description="❌ **Access Denied** - Only the command user can interact with these buttons.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Proceed', style=discord.ButtonStyle.primary)
    async def confirm_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.edit_type == 'text':
            modal = WelcomeEditModal(self.current_data)
        else:
            modal = ImageEditModal(self.current_data)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary)
    async def cancel_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="<:Unverified:1402342155489640521> Edit Cancelled",
            description="Operation cancelled - Welcome message editing was aborted and no changes were made.",
            color=0x3498db
        )
        embed.set_footer(text="Your current settings remain active")
        await interaction.response.edit_message(embed=embed, view=None)

class WelcomeSetupModal(discord.ui.Modal, title='🎉 Welcome Message Setup'):
    def __init__(self, setup_type='normal'):
        super().__init__(timeout=300)
        self.setup_type = setup_type

        self.channel_input = discord.ui.TextInput(
            label='📝 Channel (name or ID)',
            placeholder='Example: general, welcome, or 123456789012345678',
            required=True,
            max_length=100
        )
        self.add_item(self.channel_input)

        if setup_type == 'normal':
            self.message_input = discord.ui.TextInput(
                label='💬 Welcome Message',
                placeholder='Welcome {user} to {server}! Hope you enjoy your stay here.',
                required=True,
                max_length=2000,
                style=discord.TextStyle.long
            )
            self.add_item(self.message_input)
        else:
            self.title_input = discord.ui.TextInput(
                label='📋 Embed Title',
                placeholder='🎉 Welcome to {server}!',
                required=True,
                max_length=256
            )
            self.add_item(self.title_input)

            self.description_input = discord.ui.TextInput(
                label='📄 Embed Description',
                placeholder='Hello {user}! Welcome to our amazing server. We hope you have a great time here!',
                required=True,
                max_length=2000,
                style=discord.TextStyle.long
            )
            self.add_item(self.description_input)

            self.color_input = discord.ui.TextInput(
                label='🎨 Color (optional)',
                placeholder='blue, #3498db, 0x3498db, or leave empty for default blue',
                required=False,
                max_length=50
            )
            self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            # Find channel
            channel_str = self.channel_input.value.strip()
            channel = None

            if channel_str.isdigit():
                channel = interaction.guild.get_channel(int(channel_str))
            else:
                channel = discord.utils.get(interaction.guild.text_channels, name=channel_str)

            if not channel:
                embed = discord.Embed(
                    title="❌ Channel Not Found",
                    description=f"**Error:** The specified channel `{channel_str}` could not be found.\n\n**Tip:** Make sure you use the exact channel name or a valid channel ID.",
                    color=0xe74c3c
                )
                embed.set_footer(text="Double-check the channel name and try again")
                await interaction.followup.send(embed=embed)
                return

            # Save settings
            if self.setup_type == 'normal':
                data = {
                    'type': 'normal',
                    'message': self.message_input.value,
                    'channel_id': channel.id
                }
                db.set_greet_settings(str(interaction.guild.id), data)

                embed = discord.Embed(
                    title="✅ Welcome Message Configured",
                    description=f"🎉 **Success!** Normal welcome message has been set up by {interaction.user.mention} for {channel.mention}!\n\n**Preview:** {self.message_input.value[:100]}{'...' if len(self.message_input.value) > 100 else ''}",
                    color=0x27ae60
                )
                embed.set_footer(text="New members will now receive this welcome message", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
                await interaction.followup.send(embed=embed)
            else:
                # For embed, continue to image/footer setup
                color = parse_color(self.color_input.value) if self.color_input.value else 0x3498db
                temp_data = {
                    'type': 'embed',
                    'title': self.title_input.value,
                    'description': self.description_input.value,
                    'color': color,
                    'channel_id': channel.id
                }

                # Send image setup modal
                modal = EmbedImageSetupModal(temp_data)
                embed = discord.Embed(
                    title="⚙️ Continue Setup - Step 2/2",
                    description=f"🎯 **Great progress!** Basic embed settings saved by {interaction.user.mention}!\n\n**Next Step:** Configure images, thumbnails, and footer for your welcome embed to make it even more appealing.",
                    color=0x3498db
                )
                embed.add_field(name="📋 Current Settings", value=f"**Title:** {self.title_input.value[:50]}...\n**Channel:** {channel.mention}", inline=False)
                embed.set_footer(text="Click the button below to continue with visual customization")
                view = ContinueSetupView(interaction.user.id, modal)
                await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Setup Error",
                description=f"**Error occurred:** {str(e)}\n\nPlease try again or contact support if the issue persists.",
                color=0xe74c3c
            )
            embed.set_footer(text="Setup failed - please retry")
            await interaction.followup.send(embed=embed)

class EmbedImageSetupModal(discord.ui.Modal, title='🖼️ Embed Images & Footer Setup'):
    def __init__(self, temp_data):
        super().__init__(timeout=300)
        self.temp_data = temp_data

        self.thumbnail_input = discord.ui.TextInput(
            label='🖼️ Thumbnail URL (optional)',
            placeholder='https://cdn.discordapp.com/attachments/.../image.png or any image URL',
            required=False,
            max_length=500
        )
        self.add_item(self.thumbnail_input)

        self.image_input = discord.ui.TextInput(
            label='🎨 Bottom Image URL (optional)',
            placeholder='https://i.imgur.com/example.png - Supports Discord, Imgur, Gyazo, etc.',
            required=False,
            max_length=500
        )
        self.add_item(self.image_input)

        self.avatar_toggle = discord.ui.TextInput(
            label='👤 Use User Avatar as Thumbnail?',
            placeholder='yes/no (yes = user avatar, no = custom thumbnail only)',
            required=True,
            max_length=3,
            default='yes'
        )
        self.add_item(self.avatar_toggle)

        self.footer_input = discord.ui.TextInput(
            label='📝 Footer Text (optional)',
            placeholder='Welcome to {server} • Enjoy your stay! (or leave empty for auto)',
            required=False,
            max_length=100
        )
        self.add_item(self.footer_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            thumbnail_url = self.thumbnail_input.value.strip()
            image_url = self.image_input.value.strip()
            use_avatar = self.avatar_toggle.value.strip().lower() in ['yes', 'y', 'true', '1']
            footer_text = self.footer_input.value.strip()

            # Validate image URLs
            if thumbnail_url and not is_valid_image_url(thumbnail_url):
                embed = discord.Embed(
                    title="❌ Invalid Thumbnail URL",
                    description=f"**Error:** The thumbnail URL provided is not valid or supported.\n\n**Supported sources:**\n• Discord CDN links\n• Imgur, Gyazo, Lightshot\n• Direct image URLs (.png, .jpg, .gif, etc.)\n\n**Your URL:** `{thumbnail_url[:100]}...`",
                    color=0xe74c3c
                )
                embed.set_footer(text="Please provide a valid image URL")
                await interaction.followup.send(embed=embed)
                return

            if image_url and not is_valid_image_url(image_url):
                embed = discord.Embed(
                    title="❌ Invalid Image URL",
                    description=f"**Error:** The bottom image URL provided is not valid or supported.\n\n**Supported sources:**\n• Discord CDN links\n• Imgur, Gyazo, Lightshot\n• Direct image URLs (.png, .jpg, .gif, etc.)\n\n**Your URL:** `{image_url[:100]}...`",
                    color=0xe74c3c
                )
                embed.set_footer(text="Please provide a valid image URL")
                await interaction.followup.send(embed=embed)
                return

            # Complete the data
            self.temp_data.update({
                'thumbnail_url': thumbnail_url,
                'image_url': image_url,
                'use_user_avatar': use_avatar,
                'footer_text': footer_text,
                'auto_footer': not footer_text  # If no custom footer, use auto
            })

            db.set_greet_settings(str(interaction.guild.id), self.temp_data)

            channel = interaction.guild.get_channel(self.temp_data['channel_id'])

            # Build detailed settings info
            settings_info = []
            settings_info.append(f"**📝 Channel:** {channel.mention}")
            settings_info.append(f"**📋 Title:** {self.temp_data['title'][:50]}...")
            settings_info.append(f"**👤 User Avatar:** {'✅ Enabled' if use_avatar else '❌ Disabled'}")
            if thumbnail_url and not use_avatar:
                settings_info.append("**🖼️ Thumbnail:** ✅ Custom URL provided")
            elif not use_avatar:
                settings_info.append("**🖼️ Thumbnail:** ❌ None")
            settings_info.append(f"**🎨 Bottom Image:** {'✅ Enabled' if image_url else '❌ None'}")
            settings_info.append(f"**📝 Footer:** {'🎯 Custom' if footer_text else '🔄 Auto-generated'}")

            embed = discord.Embed(
                title="✅ Embed Welcome Message Configured",
                description=f"🎉 **Fantastic!** Embed welcome message has been fully configured by {interaction.user.mention}!\n\n**Configuration Summary:**\n" + "\n".join(settings_info),
                color=0x27ae60
            )
            embed.set_footer(text="Your welcome message is now active for new members!", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Configuration Error",
                description=f"**Error occurred:** {str(e)}\n\nPlease try again or contact support if the issue persists.",
                color=0xe74c3c
            )
            embed.set_footer(text="Configuration failed - please retry")
            await interaction.followup.send(embed=embed)

class ContinueSetupView(discord.ui.View):
    def __init__(self, user_id, modal):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.modal = modal

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            embed = discord.Embed(
                description="❌ **Access Denied** - Only the command user can continue this setup process.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Continue Setup', style=discord.ButtonStyle.primary)
    async def continue_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.modal)

class WelcomeEditModal(discord.ui.Modal, title='✏️ Edit Welcome Message'):
    def __init__(self, current_data):
        super().__init__(timeout=300)
        self.current_data = current_data

        # Find current channel name
        channel_name = str(current_data.get('channel_id', ''))

        self.channel_input = discord.ui.TextInput(
            label='📝 Channel (name or ID)',
            placeholder='general, welcome, or channel ID',
            default=channel_name,
            required=True,
            max_length=100
        )
        self.add_item(self.channel_input)

        if current_data['type'] == 'normal':
            self.message_input = discord.ui.TextInput(
                label='💬 Welcome Message',
                placeholder='Welcome {user} to {server}!',
                default=current_data.get('message', ''),
                required=True,
                max_length=2000,
                style=discord.TextStyle.long
            )
            self.add_item(self.message_input)
        else:
            self.title_input = discord.ui.TextInput(
                label='📋 Embed Title',
                placeholder='Welcome to {server}!',
                default=current_data.get('title', ''),
                required=True,
                max_length=256
            )
            self.add_item(self.title_input)

            self.description_input = discord.ui.TextInput(
                label='📄 Embed Description',
                placeholder='Hello {user}, welcome!',
                default=current_data.get('description', ''),
                required=True,
                max_length=2000,
                style=discord.TextStyle.long
            )
            self.add_item(self.description_input)

            color_hex = f"#{current_data.get('color', 0x3498db):06x}"
            self.color_input = discord.ui.TextInput(
                label='🎨 Color',
                placeholder='blue, #3498db, or 0x3498db',
                default=color_hex,
                required=False,
                max_length=50
            )
            self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            # Find channel
            channel_str = self.channel_input.value.strip()
            channel = None

            if channel_str.isdigit():
                channel = interaction.guild.get_channel(int(channel_str))
            else:
                channel = discord.utils.get(interaction.guild.text_channels, name=channel_str)

            if not channel:
                embed = discord.Embed(
                    title="❌ Channel Not Found",
                    description=f"**Error:** The specified channel `{channel_str}` could not be found.\n\n**Tip:** Make sure you use the exact channel name or a valid channel ID.",
                    color=0xe74c3c
                )
                embed.set_footer(text="Double-check the channel name and try again")
                await interaction.followup.send(embed=embed)
                return

            # Update settings
            if self.current_data['type'] == 'normal':
                data = {
                    'type': 'normal',
                    'message': self.message_input.value,
                    'channel_id': channel.id
                }
            else:
                color = parse_color(self.color_input.value) if self.color_input.value else 0x3498db
                data = {
                    'type': 'embed',
                    'title': self.title_input.value,
                    'description': self.description_input.value,
                    'color': color,
                    'channel_id': channel.id,
                    'thumbnail_url': self.current_data.get('thumbnail_url', ''),
                    'image_url': self.current_data.get('image_url', ''),
                    'use_user_avatar': self.current_data.get('use_user_avatar', True),
                    'footer_text': self.current_data.get('footer_text', ''),
                    'auto_footer': self.current_data.get('auto_footer', True)
                }

            db.set_greet_settings(str(interaction.guild.id), data)

            embed = discord.Embed(
                title="✅ Welcome Message Updated",
                description=f"🎉 **Success!** Welcome message has been updated by {interaction.user.mention} for {channel.mention}!",
                color=0x27ae60
            )
            embed.set_footer(text="Changes applied successfully", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Update Error",
                description=f"**Error occurred:** {str(e)}\n\nPlease try again or contact support if the issue persists.",
                color=0xe74c3c
            )
            embed.set_footer(text="Update failed - please retry")
            await interaction.followup.send(embed=embed)

class ImageEditModal(discord.ui.Modal, title='🖼️ Edit Images & Footer'):
    def __init__(self, current_data):
        super().__init__(timeout=300)
        self.current_data = current_data

        self.thumbnail_input = discord.ui.TextInput(
            label='🖼️ Thumbnail URL (optional)',
            placeholder='Discord CDN, Imgur, Gyazo, or any image hosting service',
            default=current_data.get('thumbnail_url', ''),
            required=False,
            max_length=500
        )
        self.add_item(self.thumbnail_input)

        self.image_input = discord.ui.TextInput(
            label='🎨 Bottom Image URL (optional)',
            placeholder='Supports all major image hosting platforms',
            default=current_data.get('image_url', ''),
            required=False,
            max_length=500
        )
        self.add_item(self.image_input)

        self.avatar_toggle = discord.ui.TextInput(
            label='👤 Use User Avatar as Thumbnail?',
            placeholder='yes/no (overrides custom thumbnail if yes)',
            default='yes' if current_data.get('use_user_avatar', True) else 'no',
            required=True,
            max_length=3
        )
        self.add_item(self.avatar_toggle)

        self.footer_input = discord.ui.TextInput(
            label='📝 Footer Text (optional)',
            placeholder='Custom footer text or leave empty for auto-generated',
            default=current_data.get('footer_text', ''),
            required=False,
            max_length=100
        )
        self.add_item(self.footer_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            thumbnail_url = self.thumbnail_input.value.strip()
            image_url = self.image_input.value.strip()
            use_avatar = self.avatar_toggle.value.strip().lower() in ['yes', 'y', 'true', '1']
            footer_text = self.footer_input.value.strip()

            # Validate image URLs
            if thumbnail_url and not is_valid_image_url(thumbnail_url):
                embed = discord.Embed(
                    title="❌ Invalid Thumbnail URL",
                    description=f"**Error:** The thumbnail URL provided is not valid or supported.\n\n**Supported sources:**\n• Discord CDN links\n• Imgur, Gyazo, Lightshot\n• Direct image URLs (.png, .jpg, .gif, etc.)\n\n**Your URL:** `{thumbnail_url[:100]}...`",
                    color=0xe74c3c
                )
                embed.set_footer(text="Please provide a valid image URL")
                await interaction.followup.send(embed=embed)
                return

            if image_url and not is_valid_image_url(image_url):
                embed = discord.Embed(
                    title="❌ Invalid Image URL",
                    description=f"**Error:** The bottom image URL provided is not valid or supported.\n\n**Supported sources:**\n• Discord CDN links\n• Imgur, Gyazo, Lightshot\n• Direct image URLs (.png, .jpg, .gif, etc.)\n\n**Your URL:** `{image_url[:100]}...`",
                    color=0xe74c3c
                )
                embed.set_footer(text="Please provide a valid image URL")
                await interaction.followup.send(embed=embed)
                return

            # Update data
            self.current_data['thumbnail_url'] = thumbnail_url
            self.current_data['image_url'] = image_url
            self.current_data['use_user_avatar'] = use_avatar
            self.current_data['footer_text'] = footer_text
            self.current_data['auto_footer'] = not footer_text

            db.set_greet_settings(str(interaction.guild.id), self.current_data)

            embed = discord.Embed(
                title="✅ Images & Footer Updated",
                description=f"🎉 **Success!** Image and footer settings have been updated by {interaction.user.mention}!",
                color=0x27ae60
            )
            embed.set_footer(text="Visual changes applied successfully", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Update Error",
                description=f"**Error occurred:** {str(e)}\n\nPlease try again or contact support if the issue persists.",
                color=0xe74c3c
            )
            embed.set_footer(text="Update failed - please retry")
            await interaction.followup.send(embed=embed)

class WelcomeSetupView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            embed = discord.Embed(
                description="❌ **Access Denied** - Only the command user can use these buttons.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Normal Message', style=discord.ButtonStyle.secondary, emoji='<:94598supporthexagon:1402349436931408135>')
    async def normal_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = WelcomeSetupModal('normal')
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Embed Message', style=discord.ButtonStyle.primary, emoji='<:18275viphexagon:1402349510385991711>')
    async def embed_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = WelcomeSetupModal('embed')
        await interaction.response.send_modal(modal)

class WelcomeManageView(discord.ui.View):
    def __init__(self, user_id, current_data):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.current_data = current_data

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            embed = discord.Embed(
                description="❌ **Access Denied** - Only the command user can use these buttons.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Edit Text', style=discord.ButtonStyle.primary, emoji='<:Red_Owner:1402348812416319660>')
    async def edit_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚠️ Confirm Edit - Text Settings",
            description=f"**{interaction.user.mention}** wants to edit the welcome message text and basic settings.\n\n**What will be modified:**\n• Message content or embed title/description\n• Target channel\n• Color settings (for embeds)\n\n**Continue with editing?**",
            color=0x3498db
        )
        embed.set_footer(text="This will modify your current text configuration")
        view = ConfirmEditView(self.user_id, 'text', self.current_data)
        await interaction.response.send_message(embed=embed, view=view)

    @discord.ui.button(label='Edit Images & Footer', style=discord.ButtonStyle.secondary, emoji='<:IconRoleYellow:1402349104134098994>')
    async def setup_images(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_data['type'] != 'embed':
            embed = discord.Embed(
                title="Feature Not Available",
                description="**Images and footer customization** are only available for embed messages.\n\n**Tip:** Create a new embed message to access these features.",
                color=0xe74c3c
            )
            embed.set_footer(text="Switch to embed type for full customization")
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title="⚠️ Confirm Edit - Visual Settings",
            description=f"**{interaction.user.mention}** wants to edit the embed visual elements.\n\n**What will be modified:**\n• Thumbnail settings and custom images\n• Bottom banner image\n• Footer text and auto-generation\n• User avatar display preferences\n\n**Continue with editing?**",
            color=0x3498db
        )
        embed.set_footer(text="This will modify your current visual configuration")
        view = ConfirmEditView(self.user_id, 'images', self.current_data)
        await interaction.response.send_message(embed=embed, view=view)

    @discord.ui.button(label='Test Message', style=discord.ButtonStyle.success, emoji='<:98800developerhexagon:1402349319754878996>')
    async def test_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()

            # Send test message to current channel
            await self.send_welcome_message(interaction.user, interaction.channel, self.current_data)

            embed = discord.Embed(
                title="<a:Verified:1402341882352111709> Test Message Sent",
                description=f"Test welcome message sent by {interaction.user.mention} in this channel.\n\nThis is exactly how new members will see your welcome message.",
                color=0x27ae60
            )
            embed.set_footer(text="Check the message above to see how it looks!")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="<:Unverified:1402342155489640521> Test Failed",
                description=f"Error testing message: {str(e)}\n\nThis might be due to missing permissions or invalid image URLs.",
                color=0xe74c3c
            )
            embed.set_footer(text="Please check your settings and try again")
            await interaction.followup.send(embed=embed)

    @discord.ui.button(label='Delete Config', style=discord.ButtonStyle.danger, emoji='<:14605delete:1402349214381375618>')
    async def delete_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚠️ Confirm Deletion - PERMANENT ACTION",
            description=f"**{interaction.user.mention}** wants to delete **ALL** welcome message settings.\n\n**⚠️ WARNING:** This action is **irreversible**!\n\n**What will be removed:**\n• Complete welcome message configuration\n• All custom images and settings\n• Channel assignments\n• All saved preferences\n\n**Are you absolutely sure?**",
            color=0xe74c3c
        )
        embed.set_footer(text="⚠️ This cannot be undone - all data will be permanently lost!")
        view = ConfirmDeleteView(self.user_id)
        await interaction.response.send_message(embed=embed, view=view)

    async def send_welcome_message(self, member, channel, data):
        """Send the welcome message"""
        try:
            if data['type'] == 'normal':
                message = data['message'].replace('{user}', member.mention).replace('{server}', member.guild.name)
                await channel.send(message)
            else:
                embed = discord.Embed(
                    title=data['title'].replace('{user}', member.display_name).replace('{server}', member.guild.name),
                    description=data['description'].replace('{user}', member.mention).replace('{server}', member.guild.name),
                    color=data.get('color', 0x3498db)
                )

                # Set thumbnail - user avatar takes priority
                if data.get('use_user_avatar', True):
                    embed.set_thumbnail(url=member.display_avatar.url)
                elif data.get('thumbnail_url'):
                    embed.set_thumbnail(url=data['thumbnail_url'])

                # Set bottom image
                if data.get('image_url'):
                    embed.set_image(url=data['image_url'])

                # Set footer
                if data.get('footer_text'):
                    # Custom footer
                    footer_text = data['footer_text'].replace('{user}', member.display_name).replace('{server}', member.guild.name)
                    embed.set_footer(
                        text=footer_text,
                        icon_url=member.guild.icon.url if member.guild.icon else None
                    )
                elif data.get('auto_footer', True):
                    # Auto footer only if enabled
                    embed.set_footer(
                        text=f"Welcome to {member.guild.name}",
                        icon_url=member.guild.icon.url if member.guild.icon else None
                    )

                await channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending welcome message: {e}")

class GreetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when member joins"""
        try:
            data = db.get_greet_settings(str(member.guild.id))
            if not data:
                return

            channel = member.guild.get_channel(data['channel_id'])
            if not channel:
                return

            await self.send_welcome_message(member, channel, data)

        except Exception as e:
            print(f"Welcome message error: {e}")

    @app_commands.command(name="setup_greet", description="Configure welcome messages for new members")
    async def setup_greet(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="**Access Restricted:** You need **Manage Server** permission to configure welcome messages.\n\n**Required Permission:** `Manage Server`\n**Your Permissions:** Missing required permission",
                color=0xe74c3c
            )
            embed.set_footer(text="Contact a server administrator for assistance")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        existing_data = db.get_greet_settings(str(interaction.guild.id))

        if existing_data:
            channel = interaction.guild.get_channel(existing_data['channel_id'])
            channel_text = channel.mention if channel else "<:Unverified:1402342155489640521> Unknown Channel"

            if existing_data['type'] == 'normal':
                msg_preview = existing_data['message'][:100] + ("..." if len(existing_data['message']) > 100 else "")
                desc = f"**Type:** Normal Message\n**Channel:** {channel_text}\n**Message Preview:** {msg_preview}"
            else:
                title_preview = existing_data['title'][:50] + ("..." if len(existing_data['title']) > 50 else "")
                desc = f"**Type:** Embed Message\n**Channel:** {channel_text}\n**Title Preview:** {title_preview}"

                # Add detailed image and footer info
                desc += "\n\n**Visual Settings:**"
                if existing_data.get('use_user_avatar', True):
                    desc += "\n• **Thumbnail:** <a:Verified:1402341882352111709> User Avatar"
                elif existing_data.get('thumbnail_url'):
                    desc += "\n• **Thumbnail:** <a:Verified:1402341882352111709> Custom Image"
                else:
                    desc += "\n• **Thumbnail:** <:Unverified:1402342155489640521> None"

                if existing_data.get('image_url'):
                    desc += "\n• **Bottom Image:** <a:Verified:1402341882352111709> Enabled"
                else:
                    desc += "\n• **Bottom Image:** <:Unverified:1402342155489640521> None"

                if existing_data.get('footer_text'):
                    desc += f"\n• **Footer:** <a:Verified:1402341882352111709> Custom - {existing_data['footer_text'][:30]}..."
                elif existing_data.get('auto_footer', True):
                    desc += "\n• **Footer:** <a:Verified:1402341882352111709> Auto-generated"
                else:
                    desc += "\n• **Footer:** <:Unverified:1402342155489640521> None"

            embed = discord.Embed(
                title="<a:Verified:1402341882352111709> Current Welcome Configuration",
                description=desc,
                color=0x3498db
            )
            embed.set_footer(text="Use the buttons below to manage your welcome message")

            view = WelcomeManageView(interaction.user.id, existing_data)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            embed = discord.Embed(
                title="<a:Verified:1402341882352111709> Welcome Message Setup",
                description="**Choose your welcome message style:**\n\n**Normal Message**\n• Simple text-based welcome\n• Quick and easy setup\n• Lightweight and fast\n\n**Embed Message**\n• Rich visual experience\n• Full customization options\n• Images, colors, and advanced formatting\n• User avatars and custom thumbnails\n• Professional appearance",
                color=0x3498db
            )
            embed.add_field(
                name="Recommended",
                value="**Embed Message** for the best visual impact and member engagement!",
                inline=False
            )
            embed.set_footer(text="Select an option below to get started")

            view = WelcomeSetupView(interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="greettest", description="Test your welcome message configuration")
    async def greettest(self, interaction: discord.Interaction):
        data = db.get_greet_settings(str(interaction.guild.id))
        if not data:
            embed = discord.Embed(
                title="❌ No Configuration Found",
                description="**Welcome message not configured** for this server.\n\n**Next Step:** Use `/setup_greet` to create your welcome message configuration.",
                color=0xe74c3c
            )
            embed.add_field(name="🎯 Quick Setup", value="Run `/setup_greet` to get started!", inline=False)
            embed.set_footer(text="Configure your welcome message first")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            await interaction.response.defer()

            # Send test message to current channel
            await self.send_welcome_message(interaction.user, interaction.channel, data)

            embed = discord.Embed(
                title="🧪 Test Message Sent Successfully",
                description=f"**Perfect!** Test welcome message sent by {interaction.user.mention} in this channel.\n\n**📝 Note:** This is exactly how new members will see your welcome message when they join the server.",
                color=0x27ae60
            )
            embed.add_field(name="✅ Test Complete", value="Check the message above to see how it looks!", inline=False)
            embed.set_footer(text="Your welcome message is working correctly!", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Test Failed",
                description=f"**Error testing message:** {str(e)}\n\n**Possible causes:**\n• Missing bot permissions in this channel\n• Invalid image URLs in configuration\n• Network connectivity issues\n\n**Solution:** Check your settings and try again.",
                color=0xe74c3c
            )
            embed.set_footer(text="Please check your configuration and try again")
            await interaction.followup.send(embed=embed)

    async def send_welcome_message(self, member, channel, data):
        """Send the welcome message"""
        try:
            if data['type'] == 'normal':
                message = data['message'].replace('{user}', member.mention).replace('{server}', member.guild.name)
                await channel.send(message)
            else:
                embed = discord.Embed(
                    title=data['title'].replace('{user}', member.display_name).replace('{server}', member.guild.name),
                    description=data['description'].replace('{user}', member.mention).replace('{server}', member.guild.name),
                    color=data.get('color', 0x3498db)
                )

                # Set thumbnail - user avatar takes priority
                if data.get('use_user_avatar', True):
                    embed.set_thumbnail(url=member.display_avatar.url)
                elif data.get('thumbnail_url'):
                    embed.set_thumbnail(url=data['thumbnail_url'])

                # Set bottom image
                if data.get('image_url'):
                    embed.set_image(url=data['image_url'])

                # Set footer based on settings
                if data.get('footer_text'):
                    # Custom footer
                    footer_text = data['footer_text'].replace('{user}', member.display_name).replace('{server}', member.guild.name)
                    embed.set_footer(
                        text=footer_text,
                        icon_url=member.guild.icon.url if member.guild.icon else None
                    )
                elif data.get('auto_footer', True):
                    # Auto footer only if enabled
                    embed.set_footer(
                        text=f"Welcome to {member.guild.name}",
                        icon_url=member.guild.icon.url if member.guild.icon else None
                    )

                await channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending welcome message: {e}")

async def setup(bot):
    await bot.add_cog(GreetCog(bot))