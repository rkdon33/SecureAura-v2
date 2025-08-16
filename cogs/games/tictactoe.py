import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

class PlayAgainButton(discord.ui.Button):
    def __init__(self, original_view):
        super().__init__(style=discord.ButtonStyle.green, label="🔄 Play Again", emoji="🔄")
        self.original_view = original_view

    async def callback(self, interaction: discord.Interaction):
        # Create a new game with the same settings
        new_view = TicTacToeView(
            self.original_view.player,
            self.original_view.opponent,
            self.original_view.difficulty
        )
        embed = new_view.create_game_embed()

        if self.original_view.opponent:
            content = f"{self.original_view.opponent.mention}, rematch time! 🎮"
        else:
            content = "Starting a new game! 🎮"

        # Send a new message instead of editing the current one
        await interaction.response.send_message(content=content, embed=embed, view=new_view)

class GameOverView(discord.ui.View):
    def __init__(self, original_view):
        super().__init__(timeout=300)
        self.add_item(PlayAgainButton(original_view))

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToeView = self.view

        # Check if it's the correct player's turn
        if view.opponent:  # PvP mode
            if (view.current_player == 1 and interaction.user.id != view.player.id) or \
               (view.current_player == 2 and interaction.user.id != view.opponent.id):
                embed = discord.Embed(
                    description="❌ It's not your turn!",
                    color=0xe74c3c
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        else:  # Bot mode
            if view.current_player != 1 or interaction.user.id != view.player.id:
                embed = discord.Embed(
                    description="❌ It's not your turn!",
                    color=0xe74c3c
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Check if position is already taken
        if view.board[self.y][self.x] != 0:
            embed = discord.Embed(
                description="❌ That position is already taken!",
                color=0xe74c3c
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Make the move
        view.board[self.y][self.x] = view.current_player
        self.label = view.X if view.current_player == 1 else view.O
        self.style = discord.ButtonStyle.danger if view.current_player == 1 else discord.ButtonStyle.primary
        self.disabled = True

        # Check for winner
        winner = view.check_winner()
        if winner:
            embed, game_over_view = await view.handle_game_end(winner, interaction.client.db)
            await interaction.response.edit_message(embed=embed, view=game_over_view)
            return

        # Check for draw
        if view.is_board_full():
            embed, game_over_view = await view.handle_game_end(0, interaction.client.db)  # 0 = draw
            await interaction.response.edit_message(embed=embed, view=game_over_view)
            return

        # Switch turns
        view.current_player = 3 - view.current_player

        # Update embed
        embed = view.create_game_embed()
        await interaction.response.edit_message(embed=embed, view=view)

        # Bot's turn if playing against bot
        if not view.opponent and view.current_player == 2:
            await asyncio.sleep(1)  # Small delay for realism
            await view.bot_move(interaction)

class TicTacToeView(discord.ui.View):
    X = '❌'
    O = '⭕'

    def __init__(self, player: discord.Member, opponent: discord.Member = None, difficulty: str = "Easy"):
        super().__init__(timeout=300)
        self.player = player
        self.opponent = opponent
        self.difficulty = difficulty
        self.current_player = 1  # 1 = X (player), 2 = O (opponent/bot)
        self.board = [[0 for _ in range(3)] for _ in range(3)]

        # Create buttons
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    def create_game_embed(self):
        if self.opponent:
            turn_text = f"**{self.player.display_name}**'s turn" if self.current_player == 1 else f"**{self.opponent.display_name}**'s turn"
            description = f"**{self.player.display_name}** {self.X} vs **{self.opponent.display_name}** {self.O}\n\n{turn_text}"
        else:
            turn_text = f"**{self.player.display_name}**'s turn" if self.current_player == 1 else "**Bot**'s turn"
            description = f"**{self.player.display_name}** {self.X} vs **Bot** {self.O}\n**Difficulty:** {self.difficulty}\n\n{turn_text}"

        embed = discord.Embed(
            title="🎮 Tic Tac Toe",
            description=description,
            color=0x3498db
        )
        embed.set_footer(text="Click a button to make your move!")
        return embed

    async def handle_game_end(self, winner, db):
        """Handle game end, update stats, and create game over embed"""
        self.disable_all_buttons()

        # Create match format display
        if self.opponent:
            match_format = f"**Match Format:** {self.player.display_name} vs {self.opponent.display_name} (PvP)"
        else:
            match_format = f"**Match Format:** {self.player.display_name} vs Bot ({self.difficulty} difficulty)"

        # Update statistics
        if winner == 1:  # Player 1 wins
            if self.opponent:  # PvP
                embed = discord.Embed(
                    title="🎉 Game Over!",
                    description=f"**{self.player.display_name}** wins! 🏆\n\n{match_format}",
                    color=0x00ff00
                )
                db.update_tictactoe_stats(self.player.id, 'win')
                db.update_tictactoe_stats(self.opponent.id, 'loss')

                # Add stats to embed
                player_stats = db.get_tictactoe_stats(self.player.id)
                opponent_stats = db.get_tictactoe_stats(self.opponent.id)

                embed.add_field(
                    name=f"📊 {self.player.display_name}'s Stats",
                    value=f"🏆 Wins: {player_stats['wins']}\n🤝 Draws: {player_stats['draws']}\n💔 Losses: {player_stats['losses']}",
                    inline=True
                )
                embed.add_field(
                    name=f"📊 {self.opponent.display_name}'s Stats",
                    value=f"🏆 Wins: {opponent_stats['wins']}\n🤝 Draws: {opponent_stats['draws']}\n💔 Losses: {opponent_stats['losses']}",
                    inline=True
                )
            else:  # vs Bot
                embed = discord.Embed(
                    title="🎉 Game Over!",
                    description=f"**{self.player.display_name}** wins! 🏆\n\n{match_format}",
                    color=0x00ff00
                )
                db.update_tictactoe_stats(self.player.id, 'win')

                player_stats = db.get_tictactoe_stats(self.player.id)
                embed.add_field(
                    name=f"📊 {self.player.display_name}'s Stats",
                    value=f"🏆 Wins: {player_stats['wins']}\n🤝 Draws: {player_stats['draws']}\n💔 Losses: {player_stats['losses']}",
                    inline=False
                )

        elif winner == 2:  # Player 2/Bot wins
            if self.opponent:  # PvP
                embed = discord.Embed(
                    title="🎉 Game Over!",
                    description=f"**{self.opponent.display_name}** wins! 🏆\n\n{match_format}",
                    color=0x00ff00
                )
                db.update_tictactoe_stats(self.opponent.id, 'win')
                db.update_tictactoe_stats(self.player.id, 'loss')

                player_stats = db.get_tictactoe_stats(self.player.id)
                opponent_stats = db.get_tictactoe_stats(self.opponent.id)

                embed.add_field(
                    name=f"📊 {self.player.display_name}'s Stats",
                    value=f"🏆 Wins: {player_stats['wins']}\n🤝 Draws: {player_stats['draws']}\n💔 Losses: {player_stats['losses']}",
                    inline=True
                )
                embed.add_field(
                    name=f"📊 {self.opponent.display_name}'s Stats",
                    value=f"🏆 Wins: {opponent_stats['wins']}\n🤝 Draws: {opponent_stats['draws']}\n💔 Losses: {opponent_stats['losses']}",
                    inline=True
                )
            else:  # Bot wins
                embed = discord.Embed(
                    title="🤖 Game Over!",
                    description=f"**Bot** wins! Better luck next time! 🤖\n\n{match_format}",
                    color=0xff9900
                )
                db.update_tictactoe_stats(self.player.id, 'loss')

                player_stats = db.get_tictactoe_stats(self.player.id)
                embed.add_field(
                    name=f"📊 {self.player.display_name}'s Stats",
                    value=f"🏆 Wins: {player_stats['wins']}\n🤝 Draws: {player_stats['draws']}\n💔 Losses: {player_stats['losses']}",
                    inline=False
                )
        else:  # Draw (winner == 0)
            embed = discord.Embed(
                title="🤝 Game Over!",
                description=f"It's a draw! Good game! 🤝\n\n{match_format}",
                color=0xffff00
            )
            db.update_tictactoe_stats(self.player.id, 'draw')
            if self.opponent:
                db.update_tictactoe_stats(self.opponent.id, 'draw')

                player_stats = db.get_tictactoe_stats(self.player.id)
                opponent_stats = db.get_tictactoe_stats(self.opponent.id)

                embed.add_field(
                    name=f"📊 {self.player.display_name}'s Stats",
                    value=f"🏆 Wins: {player_stats['wins']}\n🤝 Draws: {player_stats['draws']}\n💔 Losses: {player_stats['losses']}",
                    inline=True
                )
                embed.add_field(
                    name=f"📊 {self.opponent.display_name}'s Stats",
                    value=f"🏆 Wins: {opponent_stats['wins']}\n🤝 Draws: {opponent_stats['draws']}\n💔 Losses: {opponent_stats['losses']}",
                    inline=True
                )
            else:
                player_stats = db.get_tictactoe_stats(self.player.id)
                embed.add_field(
                    name=f"📊 {self.player.display_name}'s Stats",
                    value=f"🏆 Wins: {player_stats['wins']}\n🤝 Draws: {player_stats['draws']}\n💔 Losses: {player_stats['losses']}",
                    inline=False
                )

        game_over_view = GameOverView(self)
        return embed, game_over_view

    def check_winner(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]

        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != 0:
                return self.board[0][col]

        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]

        return None

    def is_board_full(self):
        for row in self.board:
            if 0 in row:
                return False
        return True

    def get_available_moves(self):
        moves = []
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    moves.append((x, y))
        return moves

    def minimax(self, depth, is_maximizing):
        winner = self.check_winner()
        if winner == 2:  # Bot wins
            return 1
        elif winner == 1:  # Player wins
            return -1
        elif self.is_board_full():  # Draw
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for x, y in self.get_available_moves():
                self.board[y][x] = 2
                score = self.minimax(depth + 1, False)
                self.board[y][x] = 0
                best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for x, y in self.get_available_moves():
                self.board[y][x] = 1
                score = self.minimax(depth + 1, True)
                self.board[y][x] = 0
                best_score = min(score, best_score)
            return best_score

    def get_best_move(self):
        best_score = -float('inf')
        best_move = None
        for x, y in self.get_available_moves():
            self.board[y][x] = 2
            score = self.minimax(0, False)
            self.board[y][x] = 0
            if score > best_score:
                best_score = score
                best_move = (x, y)
        return best_move

    async def bot_move(self, interaction):
        if self.difficulty == "Easy":
            # Random move
            available_moves = self.get_available_moves()
            if available_moves:
                x, y = random.choice(available_moves)
        else:  # Impossible
            # Perfect play using minimax
            move = self.get_best_move()
            if move:
                x, y = move
            else:
                return

        # Make the move
        self.board[y][x] = 2

        # Find and update the button
        for item in self.children:
            if isinstance(item, TicTacToeButton) and item.x == x and item.y == y:
                item.label = self.O
                item.style = discord.ButtonStyle.primary
                item.disabled = True
                break

        # Check for winner
        winner = self.check_winner()
        if winner:
            embed, game_over_view = await self.handle_game_end(winner, interaction.client.db)
            await interaction.edit_original_response(embed=embed, view=game_over_view)
            return

        # Check for draw
        if self.is_board_full():
            embed, game_over_view = await self.handle_game_end(0, interaction.client.db)  # 0 = draw
            await interaction.edit_original_response(embed=embed, view=game_over_view)
            return

        # Switch back to player
        self.current_player = 1
        embed = self.create_game_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    def disable_all_buttons(self):
        for item in self.children:
            if isinstance(item, TicTacToeButton):
                item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.opponent:
            # PvP mode - only the two players can interact
            if interaction.user.id not in [self.player.id, self.opponent.id]:
                embed = discord.Embed(
                    description="❌ You're not part of this game!",
                    color=0xe74c3c
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
        else:
            # Bot mode - only the player can interact
            if interaction.user.id != self.player.id:
                embed = discord.Embed(
                    description="❌ This is not your game!",
                    color=0xe74c3c
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
        return True

    async def on_timeout(self):
        embed = discord.Embed(
            title="⏰ Game Timeout",
            description="The game has timed out due to inactivity.",
            color=0x95a5a6
        )
        self.disable_all_buttons()

class DifficultySelect(discord.ui.Select):
    def __init__(self, player):
        self.player = player
        options = [
            discord.SelectOption(label="Easy", description="Bot makes random moves", emoji="😊"),
            discord.SelectOption(label="Impossible", description="Bot plays perfectly", emoji="🤖")
        ]
        super().__init__(placeholder="Choose difficulty...", options=options)

    async def callback(self, interaction: discord.Interaction):
        difficulty = self.values[0]
        view = TicTacToeView(self.player, difficulty=difficulty)
        embed = view.create_game_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class DifficultyView(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=60)
        self.add_item(DifficultySelect(player))

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tictactoe", description="Play Tic Tac Toe!")
    @app_commands.describe(
        user="The user you want to play against (leave empty to play against bot)",
        difficulty="Difficulty when playing against bot"
    )
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="Easy"),
        app_commands.Choice(name="Impossible", value="Impossible")
    ])
    async def tictactoe_slash(self, interaction: discord.Interaction, user: discord.Member = None, difficulty: str = "Easy"):
        if user:
            if user.id == interaction.user.id:
                embed = discord.Embed(
                    description="❌ You can't play against yourself!",
                    color=0xe74c3c
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            if user.bot:
                embed = discord.Embed(
                    description="❌ You can't play against bots! (Except me 😉)",
                    color=0xe74c3c
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            # PvP mode
            view = TicTacToeView(interaction.user, user)
            embed = view.create_game_embed()
            await interaction.response.send_message(f"{user.mention}, you've been challenged to Tic Tac Toe!", embed=embed, view=view)
        else:
            # Bot mode
            view = TicTacToeView(interaction.user, difficulty=difficulty)
            embed = view.create_game_embed()
            await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="tictactoelb", description="View Tic Tac Toe leaderboard")
    async def tictactoe_leaderboard_slash(self, interaction: discord.Interaction):
        leaderboard_data = self.bot.db.get_tictactoe_leaderboard(10)

        if not leaderboard_data:
            embed = discord.Embed(
                title="🏆 Tic Tac Toe Leaderboard",
                description="No games have been played yet! Be the first to play!",
                color=0x3498db
            )
            return await interaction.response.send_message(embed=embed)

        embed = discord.Embed(
            title="🏆 Tic Tac Toe Leaderboard",
            description="Top players by wins:",
            color=0x3498db
        )

        leaderboard_text = ""
        for i, player_data in enumerate(leaderboard_data):
            try:
                user = self.bot.get_user(int(player_data['user_id']))
                username = user.display_name if user else "Unknown User"
            except:
                username = "Unknown User"

            wins = player_data['wins']

            leaderboard_text += f"`{username} | WIN {wins}`\n"

        embed.description += f"\n\n{leaderboard_text}"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mytictactoe", description="View your Tic Tac Toe statistics")
    async def my_tictactoe_slash(self, interaction: discord.Interaction):
        stats = self.bot.db.get_tictactoe_stats(interaction.user.id)

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Tic Tac Toe Stats",
            color=0x3498db
        )

        if stats['total_games'] == 0:
            embed.description = "You haven't played any games yet! Use `/tictactoe` to start playing!"
        else:
            embed.add_field(name="🏆 Wins", value=str(stats['wins']), inline=True)
            embed.add_field(name="🤝 Draws", value=str(stats['draws']), inline=True)
            embed.add_field(name="💔 Losses", value=str(stats['losses']), inline=True)
            embed.add_field(name="📊 Total Games", value=str(stats['total_games']), inline=True)

            # Calculate win rate
            win_rate = (stats['wins'] / stats['total_games']) * 100 if stats['total_games'] > 0 else 0
            embed.add_field(name="📈 Win Rate", value=f"{win_rate:.1f}%", inline=True)

        await interaction.response.send_message(embed=embed)

    @commands.command(name="tictactoe", aliases=["ttt"])
    async def tictactoe_prefix(self, ctx):
        embed = discord.Embed(
            title="🎮 Tic Tac Toe Setup",
            description="Who would you like to play against?\n\n"
                       "🔸 **Mention a user** to play against them\n"
                       "🔸 **Mention me** or type 'bot' to play against me",
            color=0x3498db
        )
        embed.set_footer(text="Please reply with your choice...")

        setup_msg = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)

            # Check if user wants to play against bot
            if msg.content.lower() in ['bot', 'b'] or self.bot.user in msg.mentions:
                # Ask for difficulty
                embed = discord.Embed(
                    title="🤖 Playing Against Bot",
                    description="Choose your difficulty level:",
                    color=0x3498db
                )
                view = DifficultyView(ctx.author)
                await setup_msg.edit(embed=embed, view=view)

            elif msg.mentions:
                # PvP mode
                opponent = msg.mentions[0]

                if opponent.id == ctx.author.id:
                    embed = discord.Embed(
                        description="❌ You can't play against yourself!",
                        color=0xe74c3c
                    )
                    return await setup_msg.edit(embed=embed, view=None)

                if opponent.bot and opponent.id != self.bot.user.id:
                    embed = discord.Embed(
                        description="❌ You can't play against other bots!",
                        color=0xe74c3c
                    )
                    return await setup_msg.edit(embed=embed, view=None)

                view = TicTacToeView(ctx.author, opponent)
                embed = view.create_game_embed()
                await setup_msg.edit(content=f"{opponent.mention}, you've been challenged to Tic Tac Toe!", embed=embed, view=view)
            else:
                embed = discord.Embed(
                    description="❌ Invalid choice! Please mention a user or type 'bot'.",
                    color=0xe74c3c
                )
                await setup_msg.edit(embed=embed, view=None)

        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Setup Timeout",
                description="Game setup timed out. Please try again!",
                color=0x95a5a6
            )
            await setup_msg.edit(embed=embed, view=None)

    @commands.command(name="tictactoelb", aliases=["tttlb"])
    async def tictactoe_leaderboard_prefix(self, ctx):
        leaderboard_data = self.bot.db.get_tictactoe_leaderboard(10)

        if not leaderboard_data:
            embed = discord.Embed(
                title="🏆 Tic Tac Toe Leaderboard",
                description="No games have been played yet! Be the first to play!",
                color=0x3498db
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="🏆 Tic Tac Toe Leaderboard",
            description="Top players by wins:",
            color=0x3498db
        )

        leaderboard_text = ""
        for i, player_data in enumerate(leaderboard_data):
            try:
                user = self.bot.get_user(int(player_data['user_id']))
                username = user.display_name if user else "Unknown User"
            except:
                username = "Unknown User"

            wins = player_data['wins']

            leaderboard_text += f"`{username} | WIN {wins}`\n"

        embed.description += f"\n\n{leaderboard_text}"
        await ctx.send(embed=embed)

    @commands.command(name="mytictactoe", aliases=["myttt"])
    async def my_tictactoe_prefix(self, ctx):
        stats = self.bot.db.get_tictactoe_stats(ctx.author.id)

        embed = discord.Embed(
            title=f"📊 {ctx.author.display_name}'s Tic Tac Toe Stats",
            color=0x3498db
        )

        if stats['total_games'] == 0:
            embed.description = "You haven't played any games yet! Use `?tictactoe` to start playing!"
        else:
            embed.add_field(name="🏆 Wins", value=str(stats['wins']), inline=True)
            embed.add_field(name="🤝 Draws", value=str(stats['draws']), inline=True)
            embed.add_field(name="💔 Losses", value=str(stats['losses']), inline=True)
            embed.add_field(name="📊 Total Games", value=str(stats['total_games']), inline=True)

            # Calculate win rate
            win_rate = (stats['wins'] / stats['total_games']) * 100 if stats['total_games'] > 0 else 0
            embed.add_field(name="📈 Win Rate", value=f"{win_rate:.1f}%", inline=True)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))