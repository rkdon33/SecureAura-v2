import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import json
import os

PREMIUM_JOIN_LINK = "https://discord.gg/ERYMCnhWjG"
PREMIUM_ACTIVATION_CHANNEL_ID = 1388061112079224832  # Change if needed

PREMIUM_FEATURES = [
    ("server_rename", "Server Rename"),
    ("server_icon", "Server Icon"),
    ("role_rename", "Role Rename"),
    ("channel_rename", "Channel Rename"),
    ("emoji_delete", "Emoji Delete"),
    ("invite_delete", "Invite Delete"),
    ("ghost_ping", "Ghost Ping"),
    ("spam", "Anti Spam"),
]
PREMIUM_LABELS = {
    "server_rename": "Anti Server Rename",
    "server_icon": "Anti Server Icon Change",
    "role_rename": "Anti Role Rename",
    "channel_rename": "Anti Channel Rename",
    "emoji_delete": "Anti Emoji Delete",
    "invite_delete": "Anti Invite Delete",
    "ghost_ping": "Anti Ghost Ping",
    "spam": "Anti Spam"
}

def load_premium():
    from database import db
    return db.get_all_premium_servers()

def save_premium(data):
    from database import db
    for guild_id, guild_data in data.items():
        db.save_premium_server(guild_id, guild_data)

def is_premium(guild_id):
    data = load_premium()
    entry = data.get(str(guild_id))
    if not entry:
        return False
    try:
        expires = datetime.fromisoformat(entry["expires_on"])
    except Exception:
        return False
    return datetime.utcnow() < expires

async def get_or_create_premium_log_channel(guild):
    channel = discord.utils.get(guild.text_channels, name="premium-logs")
    if channel:
        return channel
    try:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel("premium-logs", overwrites=overwrites, reason="Premium logs channel created (private)")
        return channel
    except Exception:
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                return c
        return None

class PremiumPanelView(discord.ui.View):
    def __init__(self, cog, guild_id, timeout=30):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.guild_id = guild_id
        self.premium_data = load_premium()
        self.msg = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        features = self.premium_data[str(self.guild_id)]["features"]
        for key, label in PREMIUM_FEATURES:
            btn = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"premium_toggle_{key}"
            )
            btn.callback = self.make_toggle_callback(key)
            self.add_item(btn)

    def make_toggle_callback(self, feature_key):
        async def callback(interaction: discord.Interaction):
            # Only allow admins of this guild to use the panel
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "You must be an Administrator of this server to use the premium settings.", ephemeral=True
                )
                return
            self.premium_data = load_premium()
            features = self.premium_data[str(self.guild_id)]["features"]
            features[feature_key] = not features[feature_key]
            save_premium(self.premium_data)
            await interaction.response.edit_message(embed=self.cog.premium_panel_embed(self.guild_id), view=self)
        return callback

    async def on_timeout(self):
        if self.msg:
            for btn in self.children:
                btn.disabled = True
            await self.msg.edit(view=self)

class PremiumSecurity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_premium_expiry.start()
        self.bot.last_ghost_ping = {}

    def premium_panel_embed(self, guild_id):
        data = load_premium()
        features = data[str(guild_id)]["features"]
        lines = []
        for key, button_label in PREMIUM_FEATURES:
            state = "<a:Verified:1402341882352111709> Enabled" if features[key] else "<:Unverified:1402342155489640521> Disabled"
            full_label = PREMIUM_LABELS[key]
            lines.append(f"**{full_label}:** {state}")
        embed = discord.Embed(
            title="<a:Verified:1402341882352111709> Premium Feature Panel",
            description="\n".join(lines),
            color=discord.Color.purple()
        )
        embed.set_footer(text="Click buttons to toggle features - Panel expires in 30 seconds")
        return embed

    @app_commands.command(name="antipremium", description="Open the premium feature panel")
    async def antipremium(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if not is_premium(guild_id):
            embed = discord.Embed(
                title="<:Unverified:1402342155489640521> Premium Required",
                description="This feature is only available to premium servers. Join our premium server to activate premium",
                color=discord.Color.red()
            )
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="JOIN", url=PREMIUM_JOIN_LINK, style=discord.ButtonStyle.link))
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False, delete_after=25)
            return
        # Only allow admins of this guild to use the premium panel
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You must be an Administrator of this server to use the premium settings.",
                ephemeral=True
            )
            return
        view = PremiumPanelView(self, guild_id)
        embed = self.premium_panel_embed(guild_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False, delete_after=60)
        sent_msg = await interaction.original_response()
        view.msg = sent_msg

    @commands.command()
    @commands.is_owner()
    async def activatepremium(self, ctx, guild_id: int, duration: str, activated_by: discord.User):
        now = datetime.utcnow()
        duration = duration.strip().lower()
        if duration.endswith("d"):
            expires = now + timedelta(days=int(duration[:-1]))
        elif duration.endswith("m"):
            expires = now + timedelta(days=int(duration[:-1]) * 30)
        else:
            await ctx.send("Invalid duration. Use '30d' or '2m' etc.")
            return
        server = self.bot.get_guild(guild_id)
        premium_data = {
            "activated_by": activated_by.id,
            "activated_on": now.isoformat(),
            "duration": duration,
            "expires_on": expires.isoformat(),
            "features": {k: False for k, _ in PREMIUM_FEATURES}
        }
        try:
            self.bot.db.save_premium_server(guild_id, premium_data)
            await ctx.send(f"Premium activated for {server.name if server else guild_id}, expires on {expires.strftime('%Y-%m-%d')}")
        except Exception as e:
            await ctx.send(f"Error: {e}")

        embed = discord.Embed(
            title="<a:Verified:1402341882352111709> Premium Activated",
            description=f"**Server Name:** {server.name if server else guild_id}\n"
                        f"**Duration:** {duration}\n"
                        f"**Activated By:** <@{activated_by.id}>\n\n"
                        f"**Premium Features:**\n"
                        f"• Anti Server Rename\n"
                        f"• Anti Server Icon Change\n"
                        f"• Anti Role Rename\n"
                        f"• Anti Channel Rename\n"
                        f"• Anti Emoji Delete\n"
                        f"• Anti Invite Delete\n"
                        f"• Anti Ghost Ping\n"
                        f"• Anti Spam\n\n"
                        f"**Note:** Use `/antipremium` to setup premium features",
            color=discord.Color.gold()
        )

        if server:
            log_channel = await get_or_create_premium_log_channel(server)
            if log_channel:
                await log_channel.send(embed=embed)
            channel = self.bot.get_channel(PREMIUM_ACTIVATION_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"Premium activated for `{server.name if server else guild_id}` by {activated_by.mention}, duration: {duration}"
                )

    @tasks.loop(hours=12)
    async def check_premium_expiry(self):
        data = load_premium()
        now = datetime.utcnow()
        expired = []
        for gid, info in list(data.items()):
            try:
                if datetime.fromisoformat(info["expires_on"]) < now:
                    expired.append(gid)
            except Exception:
                continue
        for gid in expired:
            guild = self.bot.get_guild(int(gid))
            if guild:
                embed = discord.Embed(
                    title="Premium Expired",
                    description="Premium has expired for this server. Please re-activate to continue using premium features.",
                    color=discord.Color.red()
                )
                log_channel = await get_or_create_premium_log_channel(guild)
                if log_channel:
                    await log_channel.send(embed=embed)
            data.pop(gid)
        if expired:
            save_premium(data)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if not is_premium(after.id): return
        entry = load_premium().get(str(after.id))
        if not entry: return
        data = entry["features"]
        if data["server_rename"] and before.name != after.name:
            await self._punish_premium_action(after, "Server Rename", action="kick")
        if data["server_icon"] and before.icon != after.icon:
            await self._punish_premium_action(after, "Server Icon Change", action="kick")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if not is_premium(after.guild.id): return
        entry = load_premium().get(str(after.guild.id))
        if not entry: return
        data = entry["features"]
        if data["channel_rename"] and before.name != after.name:
            await self._punish_premium_action(after.guild, "Channel Rename", timeout_minutes=30, log=True)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if not is_premium(after.guild.id): return
        entry = load_premium().get(str(after.guild.id))
        if not entry: return
        data = entry["features"]
        if data["role_rename"] and before.name != after.name:
            await self._punish_premium_action(after.guild, "Role Rename", timeout_minutes=30, log=True)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        if not is_premium(guild.id): return
        entry = load_premium().get(str(guild.id))
        if not entry: return
        data = entry["features"]
        if data["emoji_delete"] and len(after) < len(before):
            await self._punish_premium_action(guild, "Emoji Delete", timeout_minutes=60, log=True)

    @commands.Cog.listener()
    async def on_guild_invites_update(self, guild, before, after):
        if not is_premium(guild.id): return
        entry = load_premium().get(str(guild.id))
        if not entry: return
        data = entry["features"]
        if data["invite_delete"] and len(after) < len(before):
            await self._punish_premium_action(guild, "Invite Delete", timeout_minutes=24*60, log=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or not is_premium(message.guild.id): return
        entry = load_premium().get(str(message.guild.id))
        if not entry: return
        data = entry["features"]
        if data["ghost_ping"] and message.mentions:
            self.bot.last_ghost_ping[message.id] = (message.author.id, datetime.utcnow(), message.channel.id)
        if data["spam"]:
            if not hasattr(self.bot, "msg_times"):
                self.bot.msg_times = {}
            user_times = self.bot.msg_times.setdefault(message.author.id, [])
            now = datetime.utcnow()
            user_times = [t for t in user_times if (now - t).total_seconds() < 3]
            user_times.append(now)
            self.bot.msg_times[message.author.id] = user_times
            if len(user_times) > 5:
                await self._punish_premium_action(message.guild, "Spam", user_id=message.author.id, action="kick")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or not is_premium(message.guild.id): return
        entry = load_premium().get(str(message.guild.id))
        if not entry: return
        data = entry["features"]
        if data["ghost_ping"]:
            ghost_data = self.bot.last_ghost_ping.get(message.id)
            if ghost_data:
                user_id, sent_time, channel_id = ghost_data
                if (datetime.utcnow() - sent_time).total_seconds() < 30:
                    await self._punish_premium_action(message.guild, "Ghost Ping", user_id=user_id, timeout_minutes=60, log=True)
                del self.bot.last_ghost_ping[message.id]

    async def _punish_premium_action(self, guild, action_name, user_id=None, timeout_minutes=None, log=False, action=None):
        member = None
        try:
            if user_id:
                member = guild.get_member(user_id)
            else:
                entry = None
                async for entry in guild.audit_logs(limit=3):
                    if entry.user and entry.user != guild.me:
                        member = entry.user
                        break
        except Exception:
            pass

        kicked = False
        timedout = False
        punishment = None

        if member and member != guild.me:
            try:
                if timeout_minutes:
                    until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                    await member.timeout(until, reason=f"Premium Security: {action_name}")
                    timedout = True
                    punishment = f"timed out for {timeout_minutes} minutes"
                elif action == "kick":
                    await guild.kick(member, reason=f"Premium Security: {action_name}")
                    kicked = True
                    punishment = "kicked"
            except discord.Forbidden:
                punishment = "could not punish (missing permissions)"
            except Exception:
                punishment = "could not punish (error)"
        else:
            punishment = "user not found"

        desc = f"{member.mention if member else 'A user'} was "
        if kicked:
            desc += f"kicked for triggering `{action_name}`."
        elif timedout:
            desc += f"timed out for {timeout_minutes} minutes for triggering `{action_name}`."
        else:
            desc += f"detected for triggering `{action_name}` ({punishment})."

        embed = discord.Embed(
            title="<:Unverified:1402342155489640521> Premium Security Triggered",
            description=desc,
            color=discord.Color.red() if (kicked or timedout) else discord.Color.orange()
        )
        log_channel = await get_or_create_premium_log_channel(guild)
        if log_channel:
            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumSecurity(bot))