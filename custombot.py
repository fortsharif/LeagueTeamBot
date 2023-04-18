from discord import Intents
from discord.ext import commands
import os
import aiosqlite
import riotgames

intents = Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")

teams = {}


async def init_db():
    db = await aiosqlite.connect("leaderboard.db")
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            server_id INTEGER,
            games INTEGER,
            wins INTEGER,
            UNIQUE(user_id, server_id)
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS usernames (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            UNIQUE(user_id)
        )
        """
    )
    await db.commit()
    return db


async def update_stats(user_id, server_id, won=False):
    print(user_id, server_id, won)

    async with db.cursor() as cursor:
        # Check if the user exists in the database
        await cursor.execute(
            """
            SELECT COUNT(*)
            FROM user_stats
            WHERE user_id = ? AND server_id = ?
            """,
            (user_id, server_id),
        )
        user_exists = await cursor.fetchone()

        if user_exists[0] == 0:
            # If the user does not exist, create a new row for them
            await cursor.execute(
                """
                INSERT INTO user_stats (user_id, server_id, games, wins)
                VALUES (?, ?, 1, ?)
                """,
                (user_id, server_id, int(won)),
            )
        else:
            # If the user exists, update their stats
            await cursor.execute(
                """
                UPDATE user_stats
                SET games = games + 1, wins = wins + ?
                WHERE user_id = ? AND server_id = ?
                """,
                (int(won), user_id, server_id),
            )

        await db.commit()


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    global db
    db = await init_db()


@bot.command()
async def setusername(ctx, username):
    async with db.cursor() as cursor:
        await cursor.execute(
            """
            INSERT OR REPLACE INTO usernames (user_id, username)
            VALUES (?, ?)
            """,
            (ctx.author.id, username),
        )
        await db.commit()

    await ctx.send(
        f"{ctx.author.mention}, your League of Legends username has been set to {username}."
    )


@bot.command()
async def split(ctx, *exclude):
    if ctx.author.voice is None:
        await ctx.send("You must be in a voice channel to use this command.")
        return
    else:
        voice_channel = ctx.author.voice.channel

    members = voice_channel.members
    if len(members) != 10:
        members = [
            member
            for member in members
            if member.display_name.lower() not in [name.lower() for name in exclude]
        ]
        if len(members) < 10:
            return await ctx.send(
                "Not enough members in voice channel after exclusions."
            )
        elif len(members) > 10:
            members = members[:10]

    rank_mapping = {}

    for member in members:
        user_id = str(member.id)
        async with db.cursor() as cursor:
            await cursor.execute(
                """
                SELECT username
                FROM usernames
                WHERE user_id = ?
                """,
                (user_id,),
            )
            row = await cursor.fetchone()
        if row is not None:
            username = row[0]
        else:
            await ctx.send(
                f"{member.mention}, please set your League of Legends username with the `!setusername` command."
            )
            return
        rank = riotgames.get_summoner_rank(riotgames.get_summoner_id(username))
        rank_mapping[member] = rank

    team1, team2, avg_mmr_team1, avg_mmr_team2 = riotgames.create_fair_teams(
        rank_mapping
    )

    teams[voice_channel.id] = {"team1": team1, "team2": team2}

    team1_names = ", ".join([member.display_name for member in team1])
    team2_names = ", ".join([member.display_name for member in team2])

    print(teams)

    await ctx.send(
        f"Team 1: {team1_names}\nTeam 2: {team2_names}\nAverage MMR Team 1: {avg_mmr_team1}\nAverage MMR Team 2: {avg_mmr_team2}"
    )


@bot.command()
async def cancel(ctx):
    voice_channel = ctx.author.voice.channel
    if voice_channel.id in teams:
        del teams[voice_channel.id]
        await ctx.send("Game has been canceled.")
    else:
        await ctx.send("No ongoing game to cancel.")


@bot.command()
async def win(ctx, team_number: int):
    voice_channel = ctx.author.voice.channel
    if voice_channel.id not in teams:
        await ctx.send("No ongoing game.")
        return

    if team_number not in [1, 2]:
        await ctx.send("Invalid team number. Choose 1 or 2.")
        return

    winning_team = teams[voice_channel.id][f"team{team_number}"]
    for member in winning_team:
        await update_stats(member.id, ctx.guild.id, won=True)
    losing_team = teams[voice_channel.id][f"team{(3 - team_number)}"]
    for member in losing_team:
        await update_stats(member.id, ctx.guild.id, won=False)

    del teams[voice_channel.id]
    await ctx.send(f"Team {team_number} wins!")


@bot.command()
async def leaderboard(ctx):
    async with db.cursor() as cursor:
        await cursor.execute(
            """
            SELECT user_id, games, wins, CAST(wins AS FLOAT) / games * 100 AS win_percentage
            FROM user_stats
            WHERE server_id = ?
            ORDER BY win_percentage DESC, wins DESC, games DESC
        """,
            (ctx.guild.id,),
        )
        leaderboard_rows = await cursor.fetchall()

    if not leaderboard_rows:
        await ctx.send("No leaderboard data available.")
        return

    leaderboard_text = "```"
    leaderboard_text += "Rank | Name             | Games | Wins | Win %\n"
    leaderboard_text += "-----+------------------+-------+------+-------\n"

    for i, row in enumerate(leaderboard_rows, start=1):
        user_id, games, wins, win_percentage = row
        user = await bot.fetch_user(user_id)
        leaderboard_text += f"{i:<5}| {user.display_name[:16]:<16} | {games:<5} | {wins:<4} | {win_percentage:.2f}%\n"

    leaderboard_text += "```"

    await ctx.send(leaderboard_text)


if __name__ == "__main__":
    bot.run(TOKEN)
