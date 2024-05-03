import random
from discord import Intents
from discord.ext import commands
import os
import aiosqlite
import riotgames
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import discord
import requests

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
@commands.is_owner()
async def force(ctx):
    await ctx.bot.logout()


@bot.command()
async def play(ctx, *exclude):
    if ctx.author.voice is None:
        await ctx.send("You must be in a voice channel to use this command.")
        return
    else:
        voice_channel = ctx.author.voice.channel
        members = voice_channel.members

        """
        if len(members) < 10:
            return await ctx.send(
                "Not enough members in voice channel after exclusions."
            )
        """

        for member in members:
            print(member)
            print(member.name)

        members = [
            member
            for member in members
            if member.name.lower() not in [name.lower() for name in exclude]
        ]

        word_dict = {
            "Fruits": [
                "apple",
                "banana",
                "cherry",
                "date",
                "fig",
                "grape",
                "kiwi",
                "lemon",
                "mango",
                "orange",
                "papaya",
                "peach",
                "pear",
                "plum",
                "raspberry",
                "strawberry",
                "tangerine",
                "watermelon",
                "blueberry",
                "melon",
                "avocado",
                "blackberry",
                "coconut",
                "grapefruit",
                "guava",
                "lime",
                "lychee",
                "mandarin",
                "nectarine",
                "passion fruit",
                "pineapple",
                "pomegranate",
            ],
            "Countries": [
                "Argentina",
                "Australia",
                "Brazil",
                "Canada",
                "China",
                "Egypt",
                "France",
                "Germany",
                "India",
                "Italy",
                "Japan",
                "Mexico",
                "Nigeria",
                "Russia",
                "South Africa",
                "Spain",
                "Thailand",
                "United Kingdom",
                "USA",
                "Vietnam",
                "Greece",
                "Sweden",
                "Norway",
                "Finland",
                "Denmark",
                "Poland",
                "Ukraine",
                "Turkey",
                "Iran",
                "Iraq",
                "Saudi Arabia",
                "Pakistan",
                "Bangladesh",
                "Indonesia",
                "Philippines",
                "South Korea",
                "Netherlands",
                "Switzerland",
                "Belgium",
            ],
            "Animals": [
                "ant",
                "bear",
                "cat",
                "dog",
                "elephant",
                "fox",
                "giraffe",
                "horse",
                "iguana",
                "jaguar",
                "kangaroo",
                "lion",
                "monkey",
                "octopus",
                "penguin",
                "rabbit",
                "snake",
                "tiger",
                "wolf",
                "zebra",
                "bird",
                "fish",
                "insect",
                "reptile",
                "mammal",
                "shark",
                "whale",
                "dolphin",
                "butterfly",
                "bee",
                "spider",
                "owl",
                "eagle",
                "chicken",
                "cow",
                "deer",
                "duck",
                "goat",
                "pig",
                "sheep",
                "squirrel",
                "turkey",
            ],
            "Professions": [
                "accountant",
                "baker",
                "chef",
                "dentist",
                "doctor",
                "engineer",
                "farmer",
                "firefighter",
                "hairdresser",
                "journalist",
                "lawyer",
                "nurse",
                "photographer",
                "pilot",
                "plumber",
                "police officer",
                "scientist",
                "teacher",
                "veterinarian",
                "writer",
                "actor",
                "artist",
                "athlete",
                "businessman",
                "carpenter",
                "cashier",
                "cook",
                "designer",
                "developer",
                "dietician",
                "economist",
                "electrician",
                "manager",
                "mechanic",
                "musician",
                "pharmacist",
                "psychologist",
                "receptionist",
                "salesperson",
                "social worker",
                "surgeon",
                "translator",
            ],
            "Sports": [
                "basketball",
                "cricket",
                "football",
                "golf",
                "hockey",
                "rugby",
                "soccer",
                "tennis",
                "volleyball",
                "baseball",
                "boxing",
                "cycling",
                "dancing",
                "running",
                "swimming",
                "badminton",
                "fishing",
                "judo",
                "karate",
                "wrestling",
                "skiing",
                "snowboarding",
                "surfing",
                "skating",
                "gymnastics",
                "archery",
                "fencing",
                "weightlifting",
                "diving",
                "horse racing",
                "table tennis",
                "bowling",
                "chess",
                "darts",
                "hiking",
                "paintball",
                "rock climbing",
                "skateboarding",
                "snorkeling",
            ],
            "Tools": [
                "hammer",
                "screwdriver",
                "wrench",
                "pliers",
                "saw",
                "drill",
                "tape measure",
                "level",
                "socket",
                "chisel",
                "sandpaper",
                "clamp",
                "vise",
                "multimeter",
                "flashlight",
                "jack",
                "crowbar",
                "ladder",
                "gloves",
                "wheelbarrow",
                "axe",
                "bolt cutter",
                "brush",
                "file",
                "hacksaw",
                "mallet",
                "nail gun",
                "nut driver",
                "paint brush",
                "pickaxe",
                "plane",
                "power drill",
                "putty knife",
                "rake",
                "router",
                "sander",
                "shovel",
                "sledgehammer",
                "soldering iron",
                "staple gun",
                "trowel",
                "utility knife",
            ],
            "Vehicles": [
                "car",
                "bus",
                "truck",
                "bicycle",
                "motorcycle",
                "scooter",
                "airplane",
                "helicopter",
                "submarine",
                "train",
                "tram",
                "ship",
                "yacht",
                "canoe",
                "kayak",
                "skateboard",
                "segway",
                "hot air balloon",
                "hoverboard",
                "tank",
                "tractor",
                "van",
                "taxi",
                "ambulance",
                "ferry",
                "jet ski",
                "motorboat",
                "rickshaw",
                "sailboat",
                "snowmobile",
                "spaceship",
                "subway",
                "tractor trailer",
                "tricycle",
                "unicycle",
                "wagon",
                "wheelbarrow",
            ],
            "Household Items": [
                "sofa",
                "chair",
                "table",
                "bed",
                "lamp",
                "cushion",
                "mirror",
                "carpet",
                "clock",
                "curtain",
                "bowl",
                "plate",
                "cup",
                "spoon",
                "fork",
                "knife",
                "pot",
                "pan",
                "microwave",
                "toaster",
                "blender",
                "coffee maker",
                "dishwasher",
                "fridge",
                "kettle",
                "oven",
                "stove",
                "vacuum cleaner",
                "washing machine",
                "iron",
                "broom",
                "mop",
                "bucket",
                "dustpan",
                "garbage can",
                "laundry basket",
                "picture frame",
                "plant pot",
                "rug",
                "trash bag",
                "vase",
                "magazine rack",
                "coat hanger",
                "drying rack",
                "ironing board",
                "light bulb",
                "toilet brush",
                "shower curtain",
                "soap dispenser",
                "trash can",
            ],
            "Electronics": [
                "smartphone",
                "tablet",
                "laptop",
                "desktop",
                "monitor",
                "printer",
                "router",
                "camera",
                "headphones",
                "speaker",
                "television",
                "remote",
                "game console",
                "smartwatch",
                "drone",
                "VR headset",
                "projector",
                "calculator",
                "e-reader",
                "fitness tracker",
                "digital camera",
                "external hard drive",
                "flash drive",
                "gaming mouse",
                "keyboard",
                "microphone",
                "modem",
                "power bank",
                "scanner",
                "security camera",
                "smart home device",
                "sound bar",
                "streaming device",
                "universal remote",
                "video doorbell",
                "wireless charger",
                "3D printer",
                "audio interface",
                "digital photo frame",
                "dash cam",
                "label maker",
                "laminator",
                "paper shredder",
            ],
        }

        # Select a random category and word from the dictionary
        category, word_list = random.choice(list(word_dict.items()))
        random_word = random.choice(word_list)

        # Select a random member from the members list
        random_member = random.choice(members)

        # Send the same random word to everyone except the randomly selected member and excluded members
        for member in members:
            if member != random_member:
                await member.send(f"The selected word is: {random_word}")
            else:
                await member.send("You are the imposter!")

        # Generate a random order of members
        random_order = random.sample(members, len(members))

        # Format the random order as a numbered list
        order_list = "\n".join(
            f"{i}. {member.name}" for i, member in enumerate(random_order, start=1)
        )

        # Send the random order and category to the specified channel
        # channel = bot.get_channel(777679870632919050)
        channel = bot.get_channel(1223402815955931297)
        await channel.send(
            f"Random order of members:\n{order_list}\n\nCategory: {category}"
        )


@bot.command()
@commands.is_owner()
async def split(ctx, mode="balanced", *exclude):
    if ctx.author.voice is None:
        await ctx.send("You must be in a voice channel to use this command.")
        return
    else:
        voice_channel = ctx.author.voice.channel
        members = voice_channel.members

        """ if len(members) < 10:
            return await ctx.send(
                "Not enough members in voice channel after exclusions."
            ) """

        for member in members:
            print(member)
            print(member.name)

        members = [
            member
            for member in members
            if member.name.lower() not in [name.lower() for name in exclude]
        ]

        if len(members) > 10:
            return await ctx.send("too many members")

        if mode.lower() == "random":
            random.shuffle(members)
            team1 = members[:5]
            team2 = members[5:]
            teams[voice_channel.id] = {"team1": team1, "team2": team2}
            image_width = 600
            image_height = 500
            image = Image.new("RGB", (image_width, image_height), color="white")
            draw = ImageDraw.Draw(image)

            # Load fonts for the text
            title_font = ImageFont.truetype("arial.ttf", 16)
            name_font = ImageFont.truetype("arial.ttf", 12)

            # Draw the team names and average MMRs
            draw.text((20, 20), f"Team 1", font=title_font, fill="black")
            draw.text((20, 270), f"Team 2", font=title_font, fill="black")

            # Download and draw the avatars and names for each team
            avatar_size = 80
            avatar_spacing = 10
            team1_x = 20
            team1_y = 50
            for member in team1:
                avatar_url = str(member.display_avatar.url)
                response = requests.get(avatar_url)
                avatar_image = Image.open(BytesIO(response.content))
                avatar_image = avatar_image.resize((avatar_size, avatar_size))
                image.paste(avatar_image, (team1_x, team1_y))

                name_bbox = name_font.getbbox(member.name[:11], anchor="lt")
                name_width = name_bbox[2] - name_bbox[0]
                name_x = team1_x + (avatar_size - name_width) // 2
                name_y = team1_y + avatar_size + 5
                draw.text((name_x, name_y), member.name, font=name_font, fill="black")

                team1_x += avatar_size + avatar_spacing

            team2_x = 20
            team2_y = 300
            for member in team2:
                avatar_url = str(member.display_avatar.url)
                response = requests.get(avatar_url)
                avatar_image = Image.open(BytesIO(response.content))
                avatar_image = avatar_image.resize((avatar_size, avatar_size))
                image.paste(avatar_image, (team2_x, team2_y))

                name_bbox = name_font.getbbox(member.name[:11], anchor="lt")
                name_width = name_bbox[2] - name_bbox[0]
                name_x = team2_x + (avatar_size - name_width) // 2
                name_y = team2_y + avatar_size + 5
                draw.text((name_x, name_y), member.name, font=name_font, fill="black")

                team2_x += avatar_size + avatar_spacing

            # Save the image to a BytesIO object
            image_buffer = BytesIO()
            image.save(image_buffer, format="PNG")
            image_buffer.seek(0)

            # Send the image
            await ctx.send(file=discord.File(image_buffer, filename="teams.png"))

        else:
            rank_mapping = {}
            for member in members:
                user_id = str(member.id)
                async with db.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT username FROM usernames WHERE user_id = ?
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
                try:
                    name, tag = username.split("#")
                except ValueError:
                    await ctx.send(
                        f"{member.mention}, please set your League of Legends username with the `!setusername` command. please include # with no spaces between username and tag"
                    )
                    return
                puuid = riotgames.get_summoner_puuid(name, tag)
                riot_id = riotgames.get_summoner_id(puuid)
                rank = riotgames.get_summoner_rank(riot_id)
                rank_mapping[member] = rank

            team1, team2, avg_mmr_team1, avg_mmr_team2 = riotgames.create_fair_teams(
                rank_mapping
            )
            teams[voice_channel.id] = {"team1": team1, "team2": team2}
            team1_names = ", ".join([member.name for member in team1])
            team2_names = ", ".join([member.name for member in team2])
            print(teams)
            await ctx.send(
                f"Team 1: {team1_names}\nTeam 2: {team2_names}\nAverage MMR Team 1: {avg_mmr_team1}\nAverage MMR Team 2: {avg_mmr_team2}"
            )


@bot.command()
@commands.is_owner()
async def cancel(ctx):
    voice_channel = ctx.author.voice.channel
    if voice_channel.id in teams:
        del teams[voice_channel.id]
        await ctx.send("Game has been canceled.")
    else:
        await ctx.send("No ongoing game to cancel.")


@bot.command()
@commands.is_owner()
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


@bot.command()
async def leaderboard2(ctx):
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

    # Create a new image
    image_width = 600
    image_height = 400
    image = Image.new("RGB", (image_width, image_height), color="white")
    draw = ImageDraw.Draw(image)

    # Load fonts for the text
    title_font = ImageFont.truetype("arial.ttf", 24)
    header_font = ImageFont.truetype("arial.ttf", 18)
    data_font = ImageFont.truetype("arial.ttf", 16)

    # Draw the leaderboard title
    title_text = "Leaderboard"
    title_width = title_font.getsize(title_text)[0]
    draw.text(
        ((image_width - title_width) // 2, 20),
        title_text,
        font=title_font,
        fill="black",
    )

    # Draw the leaderboard header
    header_text = "Rank   Name                Games   Wins   Win %"
    draw.text((20, 60), header_text, font=header_font, fill="black")
    draw.line((20, 85, image_width - 20, 85), fill="black", width=1)

    # Draw the leaderboard data
    y_offset = 100
    for i, row in enumerate(leaderboard_rows, start=1):
        user_id, games, wins, win_percentage = row
        user = await bot.fetch_user(user_id)
        leaderboard_text = f"{i:<5}   {user.display_name[:16]:<16}   {games:<5}   {wins:<4}   {win_percentage:.2f}%"
        draw.text((20, y_offset), leaderboard_text, font=data_font, fill="black")
        y_offset += 30

    # Save the image to a BytesIO object
    image_buffer = BytesIO()
    image.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    # Send the image
    await ctx.send(file=discord.File(image_buffer, filename="leaderboard.png"))


if __name__ == "__main__":
    bot.run(TOKEN)
