
import discord
from discord.ext import commands
from discord import app_commands
from database import db

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
    """Check if URL is a valid image URL"""
    if not url:
        return True
    
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Check if it ends with common image extensions
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    return any(url.lower().endswith(ext) for ext in valid_extensions)

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            embed = discord.Embed(
                description="❌ Only the command user can use these buttons.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label='✅ Confirm Delete', style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        db.remove_greet_settings(str(interaction.guild.id))
        embed = discord.Embed(
            title="🗑️ Welcome Settings Deleted",
            description=f"✅ Welcome message settings have been removed by {interaction.user.mention}.",
            color=0x00ff00
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Action Cancelled",
            description="Welcome settings deletion was cancelled.",
            color=0xff0000
        )
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
                description="❌ Only the command user can use these buttons.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label='✅ Proceed', style=discord.ButtonStyle.primary)
    async def confirm_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.edit_type == 'text':
            modal = WelcomeEditModal(self.current_data)
        else:
            modal = ImageEditModal(self.current_data)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.secondary)
    async def cancel_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Edit Cancelled",
            description="Welcome message editing was cancelled.",
            color=0xff0000
        )
        await interaction.response.edit_message(embed=embed, view=None)

class WelcomeSetupModal(discord.ui.Modal, title='Welcome Message Setup'):
    def __init__(self, setup_type='normal'):
        super().__init__(timeout=300)
        self.setup_type = setup_type
        
        self.channel_input = discord.ui.TextInput(
            label='Channel (name or ID)',
            placeholder='general',
            required=True,
            max_length=100
        )
        self.add_item(self.channel_input)
        
        if setup_type == 'normal':
            self.message_input = discord.ui.TextInput(
                label='Welcome Message',
                placeholder='Welcome {user} to {server}!',
                required=True,
                max_length=2000,
                style=discord.TextStyle.long
            )
            self.add_item(self.message_input)
        else:
            self.title_input = discord.ui.TextInput(
                label='Embed Title',
                placeholder='Welcome to {server}!',
                required=True,
                max_length=256
            )
            self.add_item(self.title_input)
            
            self.description_input = discord.ui.TextInput(
                label='Embed Description',
                placeholder='Hello {user}, welcome to our server!',
                required=True,
                max_length=2000,
                style=discord.TextStyle.long
            )
            self.add_item(self.description_input)
            
            self.color_input = discord.ui.TextInput(
                label='Color (optional)',
                placeholder='blue, #3498db, or 0x3498db',
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
                    description="The specified channel could not be found. Please check the channel name or ID.",
                    color=0xff0000
                )
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
                    description=f"Normal welcome message has been set up by {interaction.user.mention} for {channel.mention}!\n\n**Preview:** {self.message_input.value[:100]}{'...' if len(self.message_input.value) > 100 else ''}",
                    color=0x00ff00
                )
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
                    title="⚙️ Continue Setup",
                    description=f"Basic embed settings saved by {interaction.user.mention}!\nNow let's configure images and footer for your embed:",
                    color=0x3498db
                )
                view = ContinueSetupView(interaction.user.id, modal)
                await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Setup Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

class EmbedImageSetupModal(discord.ui.Modal, title='Embed Images & Footer Setup'):
    def __init__(self, temp_data):
        super().__init__(timeout=300)
        self.temp_data = temp_data
        
        self.thumbnail_input = discord.ui.TextInput(
            label='Thumbnail URL (optional)',
            placeholder='https://example.com/image.png or leave empty',
            required=False,
            max_length=500
        )
        self.add_item(self.thumbnail_input)
        
        self.image_input = discord.ui.TextInput(
            label='Bottom Image URL (optional)',
            placeholder='https://example.com/banner.png or leave empty',
            required=False,
            max_length=500
        )
        self.add_item(self.image_input)
        
        self.avatar_toggle = discord.ui.TextInput(
            label='Use User Avatar as Thumbnail?',
            placeholder='yes/no (if yes, overrides thumbnail URL)',
            required=True,
            max_length=3,
            default='yes'
        )
        self.add_item(self.avatar_toggle)
        
        self.footer_input = discord.ui.TextInput(
            label='Footer Text (optional)',
            placeholder='Welcome to {server} or leave empty for auto',
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
                    description="Please provide a valid image URL for the thumbnail.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            if image_url and not is_valid_image_url(image_url):
                embed = discord.Embed(
                    title="❌ Invalid Image URL",
                    description="Please provide a valid image URL for the bottom image.",
                    color=0xff0000
                )
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
            settings_info.append(f"**Channel:** {channel.mention}")
            settings_info.append(f"**Title:** {self.temp_data['title']}")
            settings_info.append(f"**User Avatar:** {'Yes' if use_avatar else 'No'}")
            if thumbnail_url and not use_avatar:
                settings_info.append("**Thumbnail:** Custom URL")
            elif not use_avatar:
                settings_info.append("**Thumbnail:** None")
            settings_info.append(f"**Bottom Image:** {'Yes' if image_url else 'No'}")
            settings_info.append(f"**Footer:** {'Custom' if footer_text else 'Auto-generated'}")
            
            embed = discord.Embed(
                title="✅ Embed Welcome Message Configured",
                description=f"Embed welcome message has been fully configured by {interaction.user.mention}!\n\n" + "\n".join(settings_info),
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Configuration Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

class ContinueSetupView(discord.ui.View):
    def __init__(self, user_id, modal):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.modal = modal
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            embed = discord.Embed(
                description="❌ Only the command user can use this button.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label='Continue Setup', style=discord.ButtonStyle.primary, emoji='⚙️')
    async def continue_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.modal)

class WelcomeEditModal(discord.ui.Modal, title='Edit Welcome Message'):
    def __init__(self, current_data):
        super().__init__(timeout=300)
        self.current_data = current_data
        
        # Find current channel name
        channel_name = str(current_data.get('channel_id', ''))
        
        self.channel_input = discord.ui.TextInput(
            label='Channel (name or ID)',
            placeholder='general',
            default=channel_name,
            required=True,
            max_length=100
        )
        self.add_item(self.channel_input)
        
        if current_data['type'] == 'normal':
            self.message_input = discord.ui.TextInput(
                label='Welcome Message',
                placeholder='Welcome {user} to {server}!',
                default=current_data.get('message', ''),
                required=True,
                max_length=2000,
                style=discord.TextStyle.long
            )
            self.add_item(self.message_input)
        else:
            self.title_input = discord.ui.TextInput(
                label='Embed Title',
                placeholder='Welcome to {server}!',
                default=current_data.get('title', ''),
                required=True,
                max_length=256
            )
            self.add_item(self.title_input)
            
            self.description_input = discord.ui.TextInput(
                label='Embed Description',
                placeholder='Hello {user}, welcome!',
                default=current_data.get('description', ''),
                required=True,
                max_length=2000,
                style=discord.TextStyle.long
            )
            self.add_item(self.description_input)
            
            color_hex = f"#{current_data.get('color', 0x3498db):06x}"
            self.color_input = discord.ui.TextInput(
                label='Color',
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
                    description="The specified channel could not be found.",
                    color=0xff0000
                )
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
                description=f"Welcome message has been updated by {interaction.user.mention} for {channel.mention}!",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Update Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

class ImageEditModal(discord.ui.Modal, title='Edit Images & Footer'):
    def __init__(self, current_data):
        super().__init__(timeout=300)
        self.current_data = current_data
        
        self.thumbnail_input = discord.ui.TextInput(
            label='Thumbnail URL (optional)',
            placeholder='https://example.com/image.png',
            default=current_data.get('thumbnail_url', ''),
            required=False,
            max_length=500
        )
        self.add_item(self.thumbnail_input)
        
        self.image_input = discord.ui.TextInput(
            label='Bottom Image URL (optional)',
            placeholder='https://example.com/banner.png',
            default=current_data.get('image_url', ''),
            required=False,
            max_length=500
        )
        self.add_item(self.image_input)
        
        self.avatar_toggle = discord.ui.TextInput(
            label='Use User Avatar as Thumbnail?',
            placeholder='yes/no',
            default='yes' if current_data.get('use_user_avatar', True) else 'no',
            required=True,
            max_length=3
        )
        self.add_item(self.avatar_toggle)
        
        self.footer_input = discord.ui.TextInput(
            label='Footer Text (optional)',
            placeholder='Custom footer or leave empty for auto',
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
                    description="Please provide a valid image URL for the thumbnail.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            if image_url and not is_valid_image_url(image_url):
                embed = discord.Embed(
                    title="❌ Invalid Image URL",
                    description="Please provide a valid image URL for the bottom image.",
                    color=0xff0000
                )
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
                description=f"Image and footer settings have been updated by {interaction.user.mention}!",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Update Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

class WelcomeSetupView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            embed = discord.Embed(
                description="❌ Only the command user can use these buttons.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label='Normal Message', style=discord.ButtonStyle.secondary, emoji='📝')
    async def normal_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = WelcomeSetupModal('normal')
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Embed Message', style=discord.ButtonStyle.primary, emoji='📋')
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
                description="❌ Only the command user can use these buttons.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label='Edit Text', style=discord.ButtonStyle.primary, emoji='✏️')
    async def edit_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚠️ Confirm Edit",
            description=f"{interaction.user.mention} wants to edit the welcome message text and settings.\n\nThis will modify the current configuration. Continue?",
            color=0xffa500
        )
        view = ConfirmEditView(self.user_id, 'text', self.current_data)
        await interaction.response.send_message(embed=embed, view=view)
    
    @discord.ui.button(label='Edit Images & Footer', style=discord.ButtonStyle.secondary, emoji='🖼️')
    async def setup_images(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_data['type'] != 'embed':
            embed = discord.Embed(
                title="❌ Feature Not Available",
                description="Images and footer are only available for embed messages.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="⚠️ Confirm Edit",
            description=f"{interaction.user.mention} wants to edit the embed images and footer.\n\nThis will modify the current visual settings. Continue?",
            color=0xffa500
        )
        view = ConfirmEditView(self.user_id, 'images', self.current_data)
        await interaction.response.send_message(embed=embed, view=view)
    
    @discord.ui.button(label='Test Message', style=discord.ButtonStyle.success, emoji='🧪')
    async def test_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            
            # Send test message to current channel
            await self.send_welcome_message(interaction.user, interaction.channel, self.current_data)
            
            embed = discord.Embed(
                title="🧪 Test Message Sent",
                description=f"Test welcome message sent by {interaction.user.mention} above!",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Test Failed",
                description=f"Error testing message: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
    
    @discord.ui.button(label='Delete', style=discord.ButtonStyle.danger, emoji='🗑️')
    async def delete_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚠️ Confirm Deletion",
            description=f"{interaction.user.mention} wants to delete all welcome message settings.\n\n**This action cannot be undone!** All configuration will be permanently removed. Are you sure?",
            color=0xff0000
        )
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
                description="You need **Manage Server** permission to use this command.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        existing_data = db.get_greet_settings(str(interaction.guild.id))
        
        if existing_data:
            channel = interaction.guild.get_channel(existing_data['channel_id'])
            channel_text = channel.mention if channel else "Unknown Channel"
            
            if existing_data['type'] == 'normal':
                msg_preview = existing_data['message'][:100] + ("..." if len(existing_data['message']) > 100 else "")
                desc = f"**Type:** Normal Message\n**Channel:** {channel_text}\n**Message:** {msg_preview}"
            else:
                title_preview = existing_data['title'][:50] + ("..." if len(existing_data['title']) > 50 else "")
                desc = f"**Type:** Embed Message\n**Channel:** {channel_text}\n**Title:** {title_preview}"
                
                # Add detailed image and footer info
                if existing_data.get('use_user_avatar', True):
                    desc += "\n**Thumbnail:** User Avatar"
                elif existing_data.get('thumbnail_url'):
                    desc += "\n**Thumbnail:** Custom Image"
                else:
                    desc += "\n**Thumbnail:** None"
                
                if existing_data.get('image_url'):
                    desc += "\n**Bottom Image:** Yes"
                else:
                    desc += "\n**Bottom Image:** None"
                
                if existing_data.get('footer_text'):
                    desc += f"\n**Footer:** Custom - {existing_data['footer_text'][:30]}..."
                elif existing_data.get('auto_footer', True):
                    desc += "\n**Footer:** Auto-generated"
                else:
                    desc += "\n**Footer:** None"
            
            embed = discord.Embed(
                title="🔧 Current Welcome Settings",
                description=desc,
                color=0xffa500
            )
            
            view = WelcomeManageView(interaction.user.id, existing_data)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            embed = discord.Embed(
                title="🎉 Welcome Message Setup",
                description="Choose how you want to welcome new members:\n\n📝 **Normal Message** - Simple text message\n📋 **Embed Message** - Rich embed with full customization\n\n*Embed messages include colors, images, footers, and user avatars!*",
                color=0x3498db
            )
            
            view = WelcomeSetupView(interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="greettest", description="Test your welcome message")
    async def greettest(self, interaction: discord.Interaction):
        data = db.get_greet_settings(str(interaction.guild.id))
        if not data:
            embed = discord.Embed(
                title="❌ No Configuration Found",
                description="No welcome message configured. Use `/setup_greet` first.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            await interaction.response.defer()
            
            # Send test message to current channel
            await self.send_welcome_message(interaction.user, interaction.channel, data)
            
            embed = discord.Embed(
                title="🧪 Test Message Sent",
                description=f"Test welcome message sent by {interaction.user.mention} above!",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Test Failed",
                description=f"Error testing message: {str(e)}",
                color=0xff0000
            )
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
