import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show SecureAura Bot commands and info")
    async def help(self, ctx):
        embed = discord.Embed(
            title="SecureAura Bot Commands",
            description=(
                "**Moderation Commands:**\n"

                "`/kick` or `?kick`\n"
                "- To kick member from server\n"
                "`/ban` or `?ban`\n"
                "- To ban member from server\n"
                "`mute` or `?mute`\n"
                "- To mute (timeout) member\n"
                "`/clear` or `?clear`\n"
                "- To clear chats from text channels\n\n"
                "**AntiNuke Features**\n"
                "`/antinall enable/disable`\n"
               "- To enable/disable all anti features\n"
                "`/antinuke enable/disable`\n"
                "- To enable/disable anti nuke features\n"
                "`/antibotadd enable/disable`\n"
                "- To enable/disable anti bot add features\n"
                "`/antiraid enable/disable`\n"
                "- To enable/disable anti raid features\n\n"
                "**Log Channel Command:**\n"
                "`/logschannel create`\n"
                "- To create logs channel\n\n"
                "**Extra Features Commands:**\n"
                "`/setup_greet`\n"
                "- To setup welcome message\n"
                "`/greettest` or `?greettest`\n"
                "- To check how welcome message looks like\n"
                "`/msg`\n"
                "- To send message using bot\n\n"
                "**Games Commands:**\n"
                "`/tictactoe` or `?tictactoe`\n"
                "- Play Tic Tac Toe against bot or other users\n"
                "`/tictactoelb` or `?tictactoelb`\n"
                "- View Tic Tac Toe leaderboard\n"
                "`/mytictactoe` or `?mytictactoe`\n"
                "- View your Tic Tac Toe statistics"
            ),
            color=discord.Color.blue()
        )

        view = discord.ui.View()
        button = discord.ui.Button(
            label="Support Server",
            emoji="<:Home:1402346986182676491>",
            url="https://discord.gg/ERYMCnhWjG",
            style=discord.ButtonStyle.link
        )
        view.add_item(button)
        await ctx.reply(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))