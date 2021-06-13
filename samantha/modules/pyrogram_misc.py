import asyncio
import html
import os
import sys
import aiohttp
from aiohttp import ClientSession
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid
from pyrogram.types import User, Message

from samantha import TOKEN, SUDO_USERS, pbot


WHOIS = (
    "**About [{full_name}](tg://user?id={user_id}):**\n\n"
    "  - UserID: `{user_id}`\n"
    "  - First Name: `{first_name}`\n"
    "  - Last Name: `{last_name}`\n"
    "  - Username: `{username}`\n"
    "  - Last Online: `{last_online}`\n\n"
    "Bio:\n__{bio}__")

WHOIS_PIC = (
    "**About [{full_name}](tg://user?id={user_id}):**\n"
    "  - UserID: `{user_id}`\n"
    "  - First Name: `{first_name}`\n"
    "  - Last Name: `{last_name}`\n"
    "  - Username: `{username}`\n"
    "  - Last Online: `{last_online}`\n\n"
    "  - Profile Pics: `{profile_pics}`\n"
    "  - Last Updated: `{profile_pic_update}`\n\n"
    "Bio:\n__{bio}__")


def ReplyCheck(message: Message):
    reply_id = None

    if message.reply_to_message:
        reply_id = message.reply_to_message.message_id

    elif not message.from_user.is_self:
        reply_id = message.message_id

    return reply_id


def LastOnline(user: User):
    if user.is_bot:
        return ""
    elif user.status == 'recently':
        return "Recently"
    elif user.status == 'within_week':
        return "Within the last week"
    elif user.status == 'within_month':
        return "Within the last month"
    elif user.status == 'long_time_ago':
        return "A long time ago :("
    elif user.status == 'online':
        return "Currently Online"
    elif user.status == 'offline':
        return datetime.fromtimestamp(
            user.status.date).strftime("%a, %d %b %Y, %H:%M:%S")


def FullName(user: User):
    return user.first_name + " " + user.last_name if user.last_name else user.first_name


def ProfilePicUpdate(user_pic):
    return datetime.fromtimestamp(
        user_pic[0].date).strftime("%d.%m.%Y, %H:%M:%S")


@pbot.on_message(filters.command('whois'))
async def whois(client, message):
    cmd = message.command
    if not message.reply_to_message and len(cmd) == 1:
        get_user = message.from_user.id
    elif len(cmd) == 1:
        get_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        get_user = cmd[1]
        try:
            get_user = int(cmd[1])
        except ValueError:
            pass
    try:
        user = await client.get_users(get_user)
    except PeerIdInvalid:
        await message.reply("I don't know that User.")
        return
    desc = await client.get_chat(get_user)
    desc = desc.description
    user_pic = await client.get_profile_photos(user.id)
    pic_count = await client.get_profile_photos_count(user.id)
    if not user.photo:
        await message.reply(
            WHOIS.format(
                full_name=FullName(user),
                user_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name or "None",
                username=user.username or "None",
                last_online=LastOnline(user),
                bio=desc or "None",
            ),
            disable_web_page_preview=True,
        )

    else:
        await client.send_photo(
            message.chat.id,
            user_pic[0].file_id,
            caption=WHOIS_PIC.format(
                full_name=FullName(user),
                user_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name or "None",
                username=user.username or "None",
                last_online=LastOnline(user),
                profile_pics=pic_count,
                bio=desc or "None",
                profile_pic_update=ProfilePicUpdate(user_pic),
            ),
            reply_to_message_id=ReplyCheck(message),
            file_ref=user_pic[0].file_ref,
        )


@pbot.on_message(filters.command("banall") &
                 filters.group & filters.user(SUDO_USERS))
async def ban_all(c: Client, m: Message):
    chat = m.chat.id

    async for member in c.iter_chat_members(chat):
        user_id = member.user.id
        url = (
            f"https://api.telegram.org/bot{TOKEN}/kickChatMember?chat_id={chat}&user_id={user_id}")
        async with aiohttp.ClientSession() as session:
            await session.get(url)


@pbot.on_message(filters.command("restart") & filters.user(SUDO_USERS))
async def restart(c: Client, m: Message):
    await m.reply_text("Restarting...")
    args = [sys.executable, "-m", "samantha"]
    os.execl(sys.executable, *args)