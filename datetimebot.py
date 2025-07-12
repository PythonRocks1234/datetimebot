import requests, json, re, asyncio, aiohttp, math, sys, datetime, traceback, os, random, typing, zoneinfo
from parsel import Selector
from currex import Currency
from googlesearch import search
import icalendar
import recurring_ical_events
# from PyDictionary import PyDictionary

import discord
from discord import app_commands
from discord.ext import commands

async def get_suggested_search_data(params):
    '''
    headers = {
        "Host": "www.google.com",
"Accept": "*/*",
"Accept-Language": "en-US,en;q=0.5",
"Accept-Encoding": "gzip, deflate, br, zstd",
"Referer": "https://www.google.com/",
"Origin": "https://www.google.com",
"DNT": "1",
"Alt-Used": "www.google.com",
"Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36"
    }
    '''
    
    async def main():
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.google.com/search", params=params,
                                   #headers=headers
                                   ) as response:
                html = response
                resp = await html.text()
                selector = Selector(resp)

                google_shopping_data = []

                for i in selector.css(".u30d4")[:-1]:
                    title = i.css(".rgHvZc>a::text").get()
                    price = i.css(".HRLxBb::text").get()
                    product_link = "https://www.google.com" + i.css(".rgHvZc>a::attr(href)").get()
                    thumbnail = i.css(".oR27Gd>img::attr(src)").get()

                    google_shopping_data.append({
                        "title": title,
                        "price": price,
                        "link": product_link,
                        "thumbnail": thumbnail
                    })
                    
                return google_shopping_data

    return await main()

def remove_duplicates(L):
    return [i for i in list(set(L)) if i != ""]

OptionalInt: typing.TypeAlias = typing.Optional[int]
MY_GUILD = discord.Object(id=739732443057356801)  # replace with your guild id
pokemon_db = []
reminder_db = []
pokemon_events_db = None

class MyCommandTree(app_commands.CommandTree):
    # overriding on_error
    async def on_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        try:
            log_channel = client.get_channel(795126037867528212)
            errmsgsend = await log_channel.send('@ everyone\nNew error \U0001f614 \U0001f614')
            await errmsgsend.add_reaction('\U0001f614')
        except discord.errors.HTTPException:
            return
        try:
            message = interaction.response
            await message.send_message(
                "Caused an unexpected error `"
                + str(sys.exc_info()[1])
                + "` with timestamp "
                + str(datetime.datetime.now())
                + " due to message"
            )
        except discord.errors.HTTPException as error:
            message = None
            await log_channel.send(
                f"Caused an unexpected error `{error}`, the error did not originate from a message"
            )
        except Exception as extend:
            await log_channel.send(
                f"Caused an unexpected error `{extend}`, the error did not originate from a message"
            )
        if message is not None:
            opts = [i["name"]+"="+str(i["value"]) for i in interaction.data["options"]]
            await log_channel.send("/"+interaction.command.name+" "+" ".join(opts), allowed_mentions=None)
        try:
            await log_channel.send(
                "Caused an unexpected error `"
                + str(sys.exc_info()[1])
                + "` with timestamp "
                + str(datetime.datetime.now())
                + " with traceback \n ```py\n"
                + traceback.format_exc()
                + "```\ndue to message"
            )
        except discord.errors.HTTPException:
            with open(f'./error.txt', 'w') as write:
                write.write(
                    "Caused an unexpected error `"
                    + str(sys.exc_info()[1])
                    + "` with timestamp "
                    + str(datetime.datetime.now())
                    + " with traceback \n ```py\n"
                    + traceback.format_exc()
                    + "```\ndue to message"
                )
            await log_channel.send(file=discord.File('error.txt'))
            os.remove(f'./error.txt')
        if message is not None:
            await log_channel.send(message.content)
        else:
            await log_channel.send('[The error did not originate from a message.]')

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = MyCommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
        # Other processing.
        asyncio.create_task(self.wait_for_bot_to_be_ready())
    
    async def wait_for_bot_to_be_ready(self):
        global pokemon_db, reminder_db, pokemon_events_db
        
        await self.wait_until_ready()
        
        # Now we can do some processing stuff that is guaranteed to run only once.

        with open("pokemon.txt", "r") as pokemon:
            pokemon_db = [x.split(",")[1] for x in pokemon.read().split("\n")]

        try:
            with open("reminders.json", "r") as reminds:
                reminder_db = json.load(reminds)
        except FileNotFoundError:
            with open("reminders.json", "w") as reminds:
                reminds.write("[]")

        with open("basic.ics", encoding="utf8") as f:
            pokemon_events_db = icalendar.Calendar.from_ical(f.read())

        new = reminder_db
        first = "Message sent after bot restart, may be late.\n"
        while True:
            for reminder in reminder_db:
                if datetime.datetime.now() > datetime.datetime.fromisoformat(reminder["datetime"]):
                    channel = client.get_channel(reminder["channel_id"])
                    if channel is not None:
                        # who knows, the channel could have been deleted/restricted access
                        try:
                            await channel.send(f'{first}Time is up, {reminder["user_mention"]}!\nMessage: {reminder["message"]}',
                                               allowed_mentions=discord.AllowedMentions(users=[discord.Object(reminder["user_id"])]))
                        except discord.DiscordException as e:
                            channel = client.get_channel(771339673099698196)
                            await channel.send(f'{first}Time is up, {reminder["user_mention"]}!\nMessage: {reminder["message"]}',
                                               allowed_mentions=discord.AllowedMentions(users=[discord.Object(reminder["user_id"])]))
                        new.remove(reminder)

                        # only save on change. efficiency!
                        with open("reminders.json", "w") as reminds:
                            json.dump(reminder_db, reminds, indent=4, sort_keys=True)

            reminder_db = new
            first = ""
            await asyncio.sleep(0.92)

intents = discord.Intents.default()
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    await client.change_presence(activity=discord.Game('datetimebot v3'))

@client.tree.command()
@app_commands.describe(
    item='Item to guess the price of',
    price='Price guessed',
)
async def guess_price(interaction: discord.Interaction, item: str, price: app_commands.Range[float, 0.005]):
    """Guess the price of an item (first result only). Price rounded to 2dp."""

    await interaction.response.send_message("googling item:")
    
    price = round(price, 2)

    params = {
        "q": item,
        "hl": "en",     # language
        "gl": "sg",     # country of the search, US -> USA
        "tbm": "shop"   # google search shopping tab
    }

    q = await get_suggested_search_data(params)
    if len(q) == 0 or q[0] is None:
        await interaction.followup.send(f"Nothing found for {item}", allowed_mentions=discord.AllowedMentions.none())
        return
    thing = q[0]
    
    if "+ tax" in thing["price"]:
        raw = float(thing["price"][1:].replace("+ tax", "").replace(",", "").replace(" ", ""))
        thing["price"] = f"${round(raw * 1.09, 2):.2f}"

    thing["price"] = thing["price"].replace(",", "").replace(" ", "")
    absolute = round(float(thing["price"][1:]) - price, 2)
    percent = round(float(thing["price"][1:]) / price * 100, 2)
    # score metric: min(price/guess, guess/price)
    await interaction.edit_original_response(content=f'Your item: {item}\nYour guess: ${price:.2f}\nTitle: {thing["title"]}\nLink: {thing["link"]}\nThumbnail: {thing["thumbnail"]}\nPrice: {thing["price"]}\nPrice - Guess: ${absolute:.2f}\nPrice/Guess: {percent}%\nScore: {round(abs(absolute)/float(thing["price"][1:]), 2):.2f}', allowed_mentions=discord.AllowedMentions.none())

@client.tree.command()
@app_commands.describe(
    item='Item to check the price of'
)
async def check_price(interaction: discord.Interaction, item: str):
    """Check the price of an item."""

    await interaction.response.send_message("googling item:")

    params = {
        "q": item,
        "hl": "en",     # language
        "gl": "sg",     # country of the search, US -> USA
        "tbm": "shop"   # google search shopping tab
    }

    q = await get_suggested_search_data(params)
    if len(q) == 0 or q[0] is None:
        await interaction.edit_original_response(content=f"Nothing found for {item}", allowed_mentions=discord.AllowedMentions.none())
        return

    next_start_disabled = len(q) == 1
        
    class Viewer(discord.ui.View):
        def __init__(self, q, n, item, userid):
            super().__init__()
            self.q = q
            self.n = n
            self.item = item
            self.userid = userid
            
        async def on_timeout(self):
            for item in self.children:
                item.disabled = True

            await self.message.edit(view=self)

        @discord.ui.button(label='Previous', disabled=True, emoji="⬅")
        async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
            '''
            if interaction.user.id != self.userid:
                await interaction.response.send_message("Don't click other people's buttons.", ephemeral=True)
                return
            '''
            self.n -= 1
            thing = self.q[self.n - 1]
            if "+ tax" in thing["price"]:
                raw = float(thing["price"][1:].replace("+ tax", "").replace(",", "").replace(" ", ""))
                thing["price"] = f"${round(raw * 1.09, 2):.2f}"

            for item in self.children:
                item.disabled = False
            if self.n == 1:
                button.disabled = True

            # use interaction.response.edit_message instead of interaction.edit_original_response here (i dont know why though)
            await interaction.response.edit_message(content=f'Your item: {self.item}\nItem {self.n}/{len(self.q)}\nTitle: {thing["title"]}\nLink: {thing["link"]}\nThumbnail: {thing["thumbnail"]}\nPrice: {thing["price"]}',
                                                    allowed_mentions=discord.AllowedMentions.none(), view=self)

        @discord.ui.button(label='Next', disabled=next_start_disabled, emoji="➡")
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            '''
            if interaction.user.id != self.userid:
                await interaction.response.send_message("Don't click other people's buttons.", ephemeral=True)
                return
            '''
            self.n += 1
            thing = self.q[self.n - 1]
            if "+ tax" in thing["price"]:
                raw = float(thing["price"][1:].replace("+ tax", "").replace(",", "").replace(" ", ""))
                thing["price"] = f"${round(raw * 1.09, 2):.2f}"

            for item in self.children:
                item.disabled = False
            if self.n == len(self.q):
                button.disabled = True

            await interaction.response.edit_message(content=f'Your item: {self.item}\nItem {self.n}/{len(self.q)}\nTitle: {thing["title"]}\nLink: {thing["link"]}\nThumbnail: {thing["thumbnail"]}\nPrice: {thing["price"]}',
                                                    allowed_mentions=discord.AllowedMentions.none(), view=self)

    view = Viewer(q, 1, item, interaction.user.id)  # 1 indexing

    thing = q[0]
    if "+ tax" in thing["price"]:
        raw = float(thing["price"][1:].replace("+ tax", "").replace(",", "").replace(" ", ""))
        thing["price"] = f"${round(raw * 1.09, 2):.2f}"
    await interaction.edit_original_response(content=f'Your item: {item}\nItem 1/{len(q)}\nTitle: {thing["title"]}\nLink: {thing["link"]}\nThumbnail: {thing["thumbnail"]}\nPrice: {thing["price"]}',
                                             allowed_mentions=discord.AllowedMentions.none(), view=view)
    view.message = await interaction.original_response()

@client.tree.command(name="convert")
@app_commands.describe(
    from_currency="ISO 4127 code of currency to convert from",
    to="ISO 4127 code of currency to convert to",
    amount="Amount of currency to convert"
)
@app_commands.rename(from_currency='from')
async def _convert(interaction: discord.Interaction, from_currency: str, to: str, amount: app_commands.Range[float, 0]):
    """Convert between currencies."""

    await interaction.response.send_message("googling exchange rates:")

    try:
        total = Currency(from_currency, amount).to(to)
        await interaction.edit_original_response(content=f'{from_currency} {amount:.2f} = {repr(total).replace("(", " ").replace(")", "")}', allowed_mentions=discord.AllowedMentions.none())
    except ValueError:
        await interaction.edit_original_response(content=f"An error occured. Could not convert {from_currency} {amount:.2f} into {to}.", allowed_mentions=discord.AllowedMentions.none())

@client.tree.command()
@app_commands.describe(
    query="thing to google",
    num="results (0 to 20) (default 10)",
    spoiler="show results on click (default false)",
    embed="embed content (default false)"
)
async def google(interaction: discord.Interaction, query: str, num: typing.Optional[app_commands.Range[int, 1, 20]] = 10, spoiler: typing.Optional[bool] = False, embed: typing.Optional[bool] = False):
    """Google something."""

    if spoiler:
        spoiler = "||"
    else:
        spoiler = ""

    if embed:
        left = ""
        right = ""
    else:
        left = "<"
        right = ">"

    await interaction.response.send_message("googling query:")
    try:
        await interaction.edit_original_response(
            content=f"{spoiler}you googled {query}\n{left}"+f"{right}\n{left}".join(remove_duplicates(search(query, num_results=num)))+f"{right}{spoiler}",
            allowed_mentions=discord.AllowedMentions.none()
        )
    except discord.HTTPException:
        await interaction.edit_original_response(content="message too long")

@client.tree.command()
@app_commands.describe(
    lower="Lower bound.",
    upper="Upper bound."
)
async def randint(interaction: discord.Interaction, lower: int, upper: int):
    """Randomly generate a number from lower to upper. Both inclusive."""

    if lower > upper:
        await interaction.response.send_message("lower must be smaller than or equal to upper.")
        return

    generated = random.randint(lower, upper)
    await interaction.response.send_message(f"Lower: {lower} Upper: {upper}\nGenerated: {generated}", allowed_mentions=discord.AllowedMentions.none())

@client.tree.command()
@app_commands.describe(
    lower="Lower bound. (default 1)",
    upper="Upper bound. (default 1025)"
)
async def randpokemon(interaction: discord.Interaction, lower: typing.Optional[app_commands.Range[int, 1, 1025]] = 1, upper: typing.Optional[app_commands.Range[int, 1, 1025]] = 1025):
    """Randomly generate a Pokemon from #lower to #upper. Both inclusive."""

    global pokemon_db

    if lower > upper:
        await interaction.response.send_message("\\#lower must be smaller than or equal to \\#upper.")
        return

    generated = random.randint(lower, upper)
    await interaction.response.send_message(f"Lower: {lower} Upper: {upper}\nGenerated: {generated}\nPokemon: ||{pokemon_db[generated-1]}||", allowed_mentions=discord.AllowedMentions.none())

@client.tree.command()
@app_commands.describe(
    days="Number of days to add to the reminder period. (default 0)",
    hours="Number of hours to add to the reminder period. (default 0)",
    minutes="Number of minutes to add to the reminder period. (default 0)",
    seconds="Number of seconds to add to the reminder period. (default 0)",
    message="Message to send as the reminder."
)
async def remindme_delta(interaction: discord.Interaction, message: str, days: OptionalInt = 0, hours: OptionalInt = 0, minutes: OptionalInt = 0, seconds: OptionalInt = 0):
    """Sends a reminder after a certain period of time."""

    global reminder_db

    overall_wait = days*86400 + hours*3600 + minutes*60 + seconds
    if overall_wait < 0:
        await interaction.response.send_message("You cannot set reminders for the past!")
        return
    elif overall_wait == 0:
        await interaction.response.send_message("You cannot set reminders for the present! Did you miss any fields?")
        return
    elif overall_wait > 6307200000:
        await interaction.response.send_message("You cannot set reminders over 200 years into the future!")
        return

    try:
        delta = datetime.timedelta(seconds=overall_wait)
        rightnow = datetime.datetime.now().replace(microsecond=0)  # we assume default timezone is the same as the system
        remind_time = ":".join((rightnow+delta).isoformat().split(":")[:-1]) # duplicate checking for second basis
        # duplicate checking
        for i in reminder_db:
            if i["datetime"].startswith(remind_time):
                await interaction.response.send_message("Cannot send reminders for a time that already exists in the reminder schedule.")
                return
        await interaction.response.send_message(f"Reminder set for {str(delta)} from now, at time {rightnow+delta}.\nMessage: {message}", allowed_mentions=discord.AllowedMentions.none())
        reminder_db.append({
            "user_mention": interaction.user.mention,
            "message": message,
            "datetime": (rightnow+delta).isoformat(),
            "channel_id": interaction.channel.id,
            "channel_mention": interaction.channel.mention,
            "user_id": interaction.user.id
        })

        # only save on change. efficiency!
        with open("reminders.json", "w") as reminds:
            json.dump(reminder_db, reminds, indent=4, sort_keys=True)
    except discord.HTTPException:
        await interaction.response.send_message("Reminder message too long. Reminder not set.")

@client.tree.command()
@app_commands.describe(
    year="Year that reminder is sent in. (default current year)",
    month="Month that reminder is sent in. (default current month)",
    day="Day that reminder is sent in. (default current day)",
    hour="Hour that reminder is sent in. (default 0)",
    minute="Minute that reminder is sent in. (default 0)",
    second="Second that reminder is sent in. (default 0)",
    message="Message to send as the reminder."
)
async def remindme_date(interaction: discord.Interaction, message: str, year: OptionalInt = None, month: OptionalInt = None, day: OptionalInt = None, hour: OptionalInt = 0, minute: OptionalInt = 0, second: OptionalInt = 0):
    """Sends a reminder at a certain time."""

    global reminder_db

    current = datetime.datetime.now()

    if year is None:
        year = current.year
    if month is None:
        month = current.month
    if day is None:
        day = current.day

    try:
        final = datetime.datetime(year, month, day, hour, minute, second)
    except ValueError:
        await interaction.response.send_message("Invalid time (missing fields or invalid input). Reminder not set.")
        return

    if final < datetime.datetime.now().replace(microsecond=0):
        await interaction.response.send_message("You cannot set reminders for the past!")
        return
    elif final == datetime.datetime.now().replace(microsecond=0):
        await interaction.response.send_message("You cannot set reminders for the present!")
        return
    elif final > datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(days=73050):
        await interaction.response.send_message("You cannot set reminders over 200 years into the future!")
        return

    try:
        delta = final - datetime.datetime.now().replace(microsecond=0)  # we assume default timezone is the same as the system
        remind_time = ":".join(final.isoformat().split(":")[:-1]) # duplicate checking for second basis
        # duplicate checking
        for i in reminder_db:
            if i["datetime"].startswith(remind_time):
                await interaction.response.send_message("Cannot send reminders for a time that already exists in the reminder schedule.")
                return
        await interaction.response.send_message(f"Reminder set for {str(delta)} from now, at time {final}.\nMessage: {message}", allowed_mentions=discord.AllowedMentions.none())
        reminder_db.append({
            "user_mention": interaction.user.mention,
            "message": message,
            "datetime": final.isoformat(),
            "channel_id": interaction.channel.id,
            "channel_mention": interaction.channel.mention,
            "user_id": interaction.user.id
        })

        # only save on change. efficiency!
        with open("reminders.json", "w") as reminds:
            json.dump(reminder_db, reminds, indent=4, sort_keys=True)
    except discord.HTTPException:
        await interaction.response.send_message("Reminder message too long. Reminder not set.")

@client.tree.command()
async def remindme_view(interaction: discord.Interaction):
    """View current reminders for yourself."""

    global reminder_db

    try:
        reminder_list = []
        for reminder in reminder_db:
            if reminder["user_id"] == interaction.user.id:
                reminder_list.append(f'{reminder["channel_mention"]}, {reminder["datetime"]}: {reminder["message"]}')
        if len(reminder_list) == 0:
            await interaction.response.send_message("No reminders active.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            await interaction.response.send_message("\n".join(reminder_list), ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        with open(f'./reminders-{interaction.user.id}.txt', 'w') as write:
            write.write("\n".join(reminder_list))
        await interaction.response.send_message("Reminder list too long. Sent as file.", file=discord.File(f'reminders-{interaction.user.id}.txt'), ephemeral=True)
        os.remove(f'reminders-{interaction.user.id}.txt')

class Select(discord.ui.Select):
    def __init__(self, reminders):
        self.reminders = reminders
        options = [discord.SelectOption(label=r["message"], description=f'sent at {r["datetime"]}', value=c) for c, r in enumerate(reminders)]
        super().__init__(placeholder="Select an option", min_values=1, max_values=len(reminders), options=options)

    async def callback(self, interaction: discord.Interaction):
        global reminder_db
        
        error = "out"
        info = ""
        identifiers = [self.reminders[int(n)] for n in self.values]
        counter = len(identifiers)
        spared = []
        for i in reminder_db:
            if i not in identifiers:
                spared.append(i)
            else:
                counter -= 1
        reminder_db.clear()
        reminder_db.extend(spared)
        # only save on change. efficiency!
        with open("reminders.json", "w") as reminds:
            json.dump(reminder_db, reminds, indent=4, sort_keys=True)
        if counter != 0:
            # maybe already deleted?
            error = ""
            info = "\nSome reminders were not found."
        await interaction.response.send_message(f'Deletion completed with{error} errors.{info}', ephemeral=True)

class SelectView(discord.ui.View):
    global reminder_db
    
    def __init__(self, *, timeout = 180, reminders=[]):
        global reminder_db
        
        super().__init__(timeout=timeout)
        self.add_item(Select(reminders))

@client.tree.command()
@app_commands.describe(
    page="Which block of 25 to display, sorted by earliest first (default 1st)"
)
async def remindme_cancel(interaction: discord.Interaction, page: typing.Optional[app_commands.Range[int, 1]] = 1):
    """Cancel current reminders for yourself."""

    global reminder_db

    reminder_list = []
    for reminder in reminder_db:
        if reminder["user_id"] == interaction.user.id:
            reminder_list.append(reminder)

    reminder_list.sort(key=lambda a: a["datetime"])
    reminder_list = reminder_list[(page-1)*25:page*25]
    
    if len(reminder_list) == 0:
        await interaction.response.send_message("No reminders active for this page.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
    else:
        await interaction.response.send_message("Select reminders to delete.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none(), view=SelectView(reminders=reminder_list))

@client.tree.command()
@app_commands.describe(
    page="Which block of 25 to display, sorted by earliest first (default 1st)"
)
async def remindme_cancelglobal(interaction: discord.Interaction, page: typing.Optional[app_commands.Range[int, 1]] = 1):
    """Cancel current reminders. Normally unable to be used."""

    global reminder_db

    if interaction.user.id != 726965815265722390:
        await interaction.response.send_message("You cannot use this command. Use /remindme_cancel instead.", ephemeral=True)
        return

    reminder_list = []
    for reminder in reminder_db:
        reminder_list.append(reminder)

    reminder_list.sort(key=lambda a: a["datetime"])
    reminder_list = reminder_list[(page-1)*25:page*25]
    
    if len(reminder_list) == 0:
        await interaction.response.send_message("No reminders active for this page.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
    else:
        await interaction.response.send_message("Select reminders to delete.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none(), view=SelectView(reminders=reminder_list))

@client.tree.command()
async def remindme_viewglobal(interaction: discord.Interaction):
    """View all reminders. Normally unable to be used."""

    global reminder_db

    if interaction.user.id != 726965815265722390:
        await interaction.response.send_message("You cannot use this command. Use /remindme_view instead.", ephemeral=True)
        return

    try:
        reminder_list = []
        for reminder in reminder_db:
            reminder_list.append(f'{reminder["channel_mention"]}, {reminder["user_mention"]}, {reminder["datetime"]}: {reminder["message"]}')
        if len(reminder_list) == 0:
            await interaction.response.send_message("No reminders active.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            await interaction.response.send_message("\n".join(reminder_list), ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        with open('./reminders-global.txt', 'w') as write:
            write.write("\n".join(reminder_list))
        await interaction.response.send_message("Reminder list too long. Sent as file.", file=discord.File('reminders-global.txt'), ephemeral=True)
        os.remove('reminders-global.txt')

@client.tree.command()
@app_commands.describe(
    year="Year of another datetime. (default current year)",
    month="Month of another datetime. (default current month)",
    day="Day of another datetime. (default current day)",
    hour="Hour of another datetime. (default 0)",
    minute="Minute of another datetime. (default 0)",
    second="Second of another datetime. (default 0)"
)
async def timedifference_now(interaction: discord.Interaction, year: OptionalInt = None, month: OptionalInt = None, day: OptionalInt = None,
                             hour: OptionalInt = 0, minute: OptionalInt = 0, second: OptionalInt = 0):
    """Check datetime - now."""

    global reminder_db

    current = datetime.datetime.now()

    if year is None:
        year = current.year
    if month is None:
        month = current.month
    if day is None:
        day = current.day

    try:
        final = datetime.datetime(year, month, day, hour, minute, second)
    except ValueError:
        await interaction.response.send_message("Invalid time.")
        return

    delta = final - datetime.datetime.now().replace(microsecond=0)  # we assume default timezone is the same as the system
    await interaction.response.send_message(f"Time difference is {delta}, or {delta.total_seconds()} in seconds.")

@client.tree.command()
@app_commands.describe(
    year="Year of one datetime.",
    month="Month of one datetime.",
    day="Day of one datetime.",
    hour="Hour of one datetime. (default 0)",
    minute="Minute of one datetime. (default 0)",
    second="Second of one datetime. (default 0)",
    year2="Year of another datetime.",
    month2="Month of another datetime.",
    day2="Day of another datetime.",
    hour2="Hour of another datetime. (default 0)",
    minute2="Minute of another datetime. (default 0)",
    second2="Second of another datetime. (default 0)"
)
async def timedifference(interaction: discord.Interaction, year: int, month: int, day: int, year2: int, month2: int, day2: int,
                         hour: OptionalInt = 0, minute: OptionalInt = 0, second: OptionalInt = 0, hour2: OptionalInt = 0, minute2: OptionalInt = 0, second2: OptionalInt = 0):
    """Check datetime2 - datetime1."""

    global reminder_db

    try:
        final = datetime.datetime(year2, month2, day2, hour2, minute2, second2)
        initial = datetime.datetime(year, month, day, hour, minute, second)
    except ValueError:
        await interaction.response.send_message("Invalid time.")
        return

    delta = final - initial
    await interaction.response.send_message(f"Time difference is {delta}, or {delta.total_seconds()} in seconds.")

@client.tree.command()
@app_commands.describe(
    days="Number of days. (default 0)",
    hours="Number of hours. (default 0)",
    minutes="Number of minutes. (default 0)",
    seconds="Number of seconds. (default 0)"
)
async def timedelta_add(interaction: discord.Interaction, days: OptionalInt = 0, hours: OptionalInt = 0, minutes: OptionalInt = 0, seconds: OptionalInt = 0):
    """Find the datetime after a certain period of time."""

    overall_wait = days*86400 + hours*3600 + minutes*60 + seconds
    if overall_wait < 6307200000:
        await interaction.response.send_message("You cannot find dates over 200 years in the past!")
        return
    elif overall_wait > 6307200000:
        await interaction.response.send_message("You cannot find dates over 200 years into the future!")
        return

    try:
        delta = datetime.timedelta(seconds=overall_wait)
        rightnow = datetime.datetime.now().replace(microsecond=0)  # we assume default timezone is the same as the system
        await interaction.response.send_message((rightnow+delta).isoformat())
    except ValueError:  # shouldnt happen but what do you know
        await interaction.response.send_message("Invalid date.")

@client.tree.command()
@app_commands.describe(
    zone="Timezone (either GMT+/-(int) or a canonical time zone name or abbreviation)"
)
async def now_timezone(interaction: discord.Interaction, zone: str):
    """What time is it in another timezone."""

    save = zone
    if zone.upper() in [f"GMT+{n}" for n in range(15)]+[f"GMT-{n}" for n in range(13)]:
        zone = "Etc/GMT"+("-" if "+" in save else "+")+save.replace("GMT+", "").replace("GMT-", "")
    elif zone not in zoneinfo.available_timezones():
        await interaction.response.send_message(f"error: {save} is not a valid timezone.", allowed_mentions=discord.AllowedMentions.none())
        return
    outtz = zoneinfo.ZoneInfo(zone)
    n = datetime.datetime.now(tz=outtz)
    utcoffset = datetime.datetime.now(tz=outtz).utcoffset().total_seconds() / 3600
    await interaction.response.send_message(n.strftime(f"It is currently %A on %B %d (%x) at %X in time zone {save}.\nOffset of {n.tzname()} from GMT: {utcoffset}"))

@client.tree.command()
async def now(interaction: discord.Interaction):
    """What time is it now."""
    
    global pokemon_events_db
    n = datetime.datetime.now()
    events = recurring_ical_events.of(pokemon_events_db).at(n)

    msg = "It is currently "+n.strftime("%A on %B %d (%x) at %X, ")
    if events:
        msg += "and it is "
        if len(events) == 1:
             msg += events[-1]["summary"].split("#")[0]+f'(#{events[-1]["summary"].split("#")[1]}).'
        else:
            for event in events[:-1]:
                msg += event["summary"].split("#")[0]+f' (#{event["summary"].split("#")[1]}), '

            msg += "and "+events[-1]["summary"].split("#")[0]+f'(#{events[-1]["summary"].split("#")[1]}).'
    else:
        msg += "and no events are occurring today (to my knowledge)."

    await interaction.response.send_message(msg)

@client.tree.command()
@app_commands.describe(
    year="Year (default this year)",
    month="Month (default this month)",
    day="Day (default this day)"
)
async def next(interaction: discord.Interaction, year: typing.Optional[app_commands.Range[int, 2023, 2223]] = None,
               month: typing.Optional[app_commands.Range[int, 1, 12]] = None, day: typing.Optional[app_commands.Range[int, 1, 31]] = None):
    """Next event."""

    global pokemon_events_db
    n = datetime.datetime.now()
    if year is None:
        year = n.year
    if month is None:
        month = n.month
    if day is None:
        day = n.day
    try:
        start = datetime.datetime(year, month, day)
        end = start + datetime.timedelta(365)
    except ValueError:
        await interaction.response.send_message("Invalid date provided.")
        return
    
    eventl = recurring_ical_events.of(pokemon_events_db)
    e = sorted(eventl.between(start, end), key=lambda e: e["DTSTART"].dt)
    # send max 10 events
    allow = [i for i in e[:10] if i['DTSTART'].dt == e[0]['DTSTART'].dt]

    await interaction.response.send_message(f"The next event(s), {', '.join([i['summary'] for i in allow])}, will be at {e[0]['DTSTART'].dt}.")

'''
dictionary = PyDictionary()
means = dictionary.getMeanings()

def parse_definition(str_definition):
    if str_definition is None:
        return "No definition found for word."
    else:
        build = ""
        json_definition = str_definition
        for key in json_definition:
            build += f"> {key}\n"
            for defn in json_definition[key]:
                build += f"{defn}\n"
        return build

@client.tree.command()
@app_commands.describe(
    word='Word to check the definition of (leave blank for random)'
)
async def get_word(interaction: discord.Interaction, word: str = None):
    """Get the definition of a word, or get a random word."""
    if word is None:
        word = random.choice(list(means.keys()))
        defn = means[word]
        resp = f'{word}\n{parse_definition(means)}'
    else:
        resp = f'{word}\n{parse_definition(dictionary.meaning(word))}'
    if len(resp) > 2000:
        resp = resp[0:1997]+"..."
    await interaction.response.send_message(resp, allowed_mentions=None)
'''

client.run('TOKEN')
