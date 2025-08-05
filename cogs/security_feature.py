import discord
from discord.ext import commands
from .whitelist_utils import is_whitelisted, get_whitelist
from discord import app_commands
from collections import defaultdict
from datetime import datetime
import random
import json
import os

SUPPORT_LINK = "https://discord.gg/ERYMCnhWjG"
def get_status_emoji(val):
    return '☑️' if val else '❎'

class SecurityFeature(commands.Cog):
    antinuke_group = app_commands.Group(name="antinuke", description="Enable/disable anti-nuke features")
    antibotadd_group = app_commands.Group(name="antibotadd", description="Enable/disable anti-bot-add features")
    antiraid_group = app_commands.Group(name="antiraid", description="Enable/disable anti-raid features")
    antiall_group = app_commands.Group(name="antiall", description="Enable/disable all anti features")


    def __init__(self, bot):
        self.bot = bot
        self.warn_counts = defaultdict(int)  # (guild_id, user_id, type): warning count
        self.settings = defaultdict(lambda: {
            "antinuke": True,
            "antibotadd": True,
            "antiraid": True
        })

        self.recent_joins = defaultdict(list)
        self.raid_threshold = 5
        self.raid_interval = 10

    # ------------- SLASH COMMANDS (ANTINUKE/ANTIBOTADD/ANTIRAID/ANTIALL/WHITELIST) -------------
    # /antinuke enable/disable
    @antinuke_group.command(name="enable", description="Enable anti-nuke protections")
    async def antinuke_enable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antinuke"] = True
        embed = self._status_embed(g, "AntiNuke enabled.")
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=15)

    @antinuke_group.command(name="disable", description="Disable anti-nuke protections")
    async def antinuke_disable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antinuke"] = False
        embed = self._status_embed(g, "AntiNuke disabled.")
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=15)

    # /antibotadd enable/disable
    @antibotadd_group.command(name="enable", description="Enable anti-bot-add protections")
    async def antibotadd_enable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antibotadd"] = True
        embed = self._status_embed(g, "AntiBotAdd enabled.")
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=15)

    @antibotadd_group.command(name="disable", description="Disable anti-bot-add protections")
    async def antibotadd_disable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antibotadd"] = False
        embed = self._status_embed(g, "AntiBotAdd disabled.")
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=15)

    # /antiraid enable/disable
    @antiraid_group.command(name="enable", description="Enable anti-raid protections")
    async def antiraid_enable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antiraid"] = True
        embed = self._status_embed(g, "AntiRaid enabled.")
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=15)

    @antiraid_group.command(name="disable", description="Disable anti-raid protections")
    async def antiraid_disable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g]["antiraid"] = False
        embed = self._status_embed(g, "AntiRaid disabled.")
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=15)

    # /antiall enable/disable
    @antiall_group.command(name="enable", description="Enable all anti features")
    async def antiall_enable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g] = {
            "antinuke": True,
            "antibotadd": True,
            "antiraid": True
        }
        embed = self._status_embed(g, "All anti features enabled.")
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=15)

    @antiall_group.command(name="disable", description="Disable all anti features")
    async def antiall_disable(self, interaction: discord.Interaction):
        g = interaction.guild_id
        self.settings[g] = {
            "antinuke": False,
            "antibotadd": False,
            "antiraid": False
        }
        embed = self._status_embed(g, "All anti features disabled.")
        await interaction.response.send_message(embed=embed, ephemeral=False, delete_after=15)



    def _is_whitelisted(self, guild_id, user_id):
        return is_whitelisted(guild_id, user_id)[guild_id]

    def _status_embed(self, guild_id, msg):
        st = self.settings[guild_id]
        status_line = (
            f"AntiNuke {get_status_emoji(st.get('antinuke', False))} | "
            f"AntiBotAdd {get_status_emoji(st.get('antibotadd', False))} | "
            f"AntiRaid {get_status_emoji(st.get('antiraid', False))}"
        )
        embed = discord.Embed(
            title="SecureAura Anti Features Status",
            description=f"{msg}\n\n{status_line}",
            color=discord.Color.blue()
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Support Server", url=SUPPORT_LINK, style=discord.ButtonStyle.link))
        embed.set_footer(text="Use the slash commands to manage features.")
        return embed

    # ------------ GUILD JOIN WELCOME ------------
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        adder = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                adder = entry.user
        except Exception:
            adder = guild.owner

        embed = discord.Embed(
            title="AntiNuke Features Enabled ☑️",
            description=(
                f"Hey, {adder.mention if adder else 'there'}, thanks for using our bot.\n"
                "SecureAura is an intelligent Discord security bot designed to safeguard your server with real-time protection, automated moderation, and advanced anti-raid features-ensuring a safe and peaceful community.\n\n"
                "**NOTE:**\n"
                "- AntiNuke System has been enabled by default, so if you want to add bot or do any activities like channel create/delete, role create/delete, etc. then you need to whitelist yourself or any other user by using `/whitelist add` command otherwise you or bot may get kicked or banned."
            ),
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Support Server", url=SUPPORT_LINK, style=discord.ButtonStyle.link))

        if adder:
            try:
                await adder.send(embed=embed, view=view)
            except Exception:
                pass

        text_channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages]
        if text_channels:
            channel = random.choice(text_channels)
            try:
                await channel.send(embed=embed, view=view)
            except Exception:
                pass

    # ------------ ANTI-NUKE: CHANNEL/ROLE CREATE/DELETE ------------
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self._handle_channel_event(channel, "create")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self._handle_channel_event(channel, "delete")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self._handle_role_event(role, "create")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self._handle_role_event(role, "delete")

    async def _handle_channel_event(self, channel, action):
        guild = channel.guild
        if not self.settings[guild.id]["antinuke"]:
            return
        entry = None
        try:
            async for e in guild.audit_logs(limit=1, action=getattr(discord.AuditLogAction, f"channel_{action}")):
                entry = e
                break
        except Exception:
            return
        if entry is None:
            return
        user = entry.user
        bot_member = guild.me
        # Only punish users below the bot's top role and not whitelisted
        if user is None or user.bot or user.top_role >= bot_member.top_role or self._is_whitelisted(guild.id, user.id):
            return

        key = (guild.id, user.id, "channel")
        self.warn_counts[key] += 1

        embed = discord.Embed(
            title="Channel Security Alert",
            description=f"{user.mention} tried to {action} a channel: {getattr(channel, 'mention', channel.name)}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Count", value=str(self.warn_counts[key]))
        embed.set_footer(text=f"User ID: {user.id}")

        if self.warn_counts[key] < 3:
            await self._log_or_owner_dm(guild, embed, user.mention)
        else:
            try:
                await guild.ban(user, reason=f"Exceeded channel {action} limit by SecureAura", delete_message_days=0)
                embed.title = "User Banned"
                embed.color = discord.Color.red()
                embed.description += f"\nUser has been banned after 3 warnings for channel {action}."
                await self._log_or_owner_dm(guild, embed, user.mention)
            except Exception:
                pass
            self.warn_counts[key] = 0

    async def _handle_role_event(self, role, action):
        guild = role.guild
        if not self.settings[guild.id]["antinuke"]:
            return
        entry = None
        try:
            async for e in guild.audit_logs(limit=1, action=getattr(discord.AuditLogAction, f"role_{action}")):
                entry = e
                break
        except Exception:
            return
        if entry is None:
            return
        user = entry.user
        bot_member = guild.me
        # Only punish users below the bot's top role and not whitelisted
        if user is None or user.bot or user.top_role >= bot_member.top_role or self._is_whitelisted(guild.id, user.id):
            return

        key = (guild.id, user.id, "role")
        self.warn_counts[key] += 1

        embed = discord.Embed(
            title="Role Security Alert",
            description=f"{user.mention} tried to {action} a role: {getattr(role, 'name', '')}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Count", value=str(self.warn_counts[key]))
        embed.set_footer(text=f"User ID: {user.id}")

        if self.warn_counts[key] < 3:
            await self._log_or_owner_dm(guild, embed, user.mention)
        else:
            try:
                await guild.ban(user, reason=f"Exceeded role {action} limit by SecureAura", delete_message_days=0)
                embed.title = "User Banned"
                embed.color = discord.Color.red()
                embed.description += f"\nUser has been banned after 3 warnings for role {action}."
                await self._log_or_owner_dm(guild, embed, user.mention)
            except Exception:
                pass
            self.warn_counts[key] = 0

    # ------------ ANTI-BOT-ADD (KICK MEMBER WHO ADDED BOT) ------------
    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        guild = entry.guild
        if not self.settings[guild.id]["antibotadd"]:
            return
        if entry.action == discord.AuditLogAction.bot_add:
            user = entry.user
            bot_added = entry.target
            bot_member = guild.me
            # Only punish users below the bot's top role and not whitelisted
            if (user is not None and not user.bot and user.top_role < bot_member.top_role
                and not self._is_whitelisted(guild.id, user.id)):
                try:
                    await guild.kick(user, reason="Unauthorized bot add by SecureAura")
                except Exception:
                    pass
                embed = discord.Embed(
                    title="AntiBotAdd Triggered",
                    description=f"{user.mention} was kicked for adding bot {getattr(bot_added, 'mention', bot_added)}.",
                    color=discord.Color.red()
                )
                await self._log_or_owner_dm(guild, embed)
            # Ban the newly added bot unless whitelisted
            if (bot_added is not None and getattr(bot_added, "bot", False) and not self._is_whitelisted(guild.id, bot_added.id)):
                try:
                    await guild.ban(bot_added, reason="Unauthorized bot added by SecureAura")
                except Exception:
                    pass

    # ------------ ANTI-RAID (RAID JOIN) ------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        if not self.settings[guild.id]["antiraid"]:
            return
        now = datetime.utcnow()
        if not member.bot:
            self.recent_joins[guild.id] = [t for t in self.recent_joins[guild.id] if (now - t).total_seconds() < self.raid_interval]
            self.recent_joins[guild.id].append(now)
            if len(self.recent_joins[guild.id]) >= self.raid_threshold:
                to_ban = []
                for m in guild.members:
                    if not m.bot and m.joined_at and (now - m.joined_at).total_seconds() < self.raid_interval:
                        to_ban.append(m)
                for m in to_ban:
                    try:
                        await guild.ban(m, reason="Anti-raid triggered: suspected raid join.")
                    except Exception:
                        pass
                embed = discord.Embed(
                    title="Anti-Raid Triggered",
                    description=f"Banned {len(to_ban)} members for suspected raid join.",
                    color=discord.Color.red()
                )
                await self._log_or_owner_dm(guild, embed)
                self.recent_joins[guild.id] = []

    # ------------ LOG CHANNEL HELPERS ------------
    def _get_log_channel(self, guild):
        log_channels = getattr(self.bot, "log_channels", {})
        if guild.id in log_channels:
            return guild.get_channel(log_channels[guild.id])
        channel = discord.utils.get(guild.text_channels, name="logs")
        if channel and hasattr(self.bot, "log_channels"):
            self.bot.log_channels[guild.id] = channel.id
        return channel

    async def _log_or_owner_dm(self, guild, embed, mention=None):
        log_channel = self._get_log_channel(guild)
        if log_channel:
            try:
                await log_channel.send(embed=embed, content=mention or None)
            except Exception:
                pass
        else:
            try:
                await guild.owner.send(embed=embed, content=mention or None)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(SecurityFeature(bot))