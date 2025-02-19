# RT - Global Ban

from discord.ext import commands
import discord

from rtlib import mysql, DatabaseManager
from rtlib.ext import componesy, Embeds
from .bot_general import INFO_SS
from typing import Optional
from random import choice
from data import is_admin


class DataManager(DatabaseManager):
    def __init__(self, db):
        self.db: mysql.MySQLManager = db

    async def init_table(self, cursor):
        await cursor.create_table(
            "gban", {"UserID": "BIGINT", "Reason": "TEXT"}
        )
        await cursor.create_table(
            "gbanOff", {"GuildID": "BIGINT"}
        )

    async def add_user(self, cursor, user_id: int, reason: str) -> None:
        await cursor.insert_data(
            "gban", {"UserID": user_id, "Reason": reason}
        )

    async def remove_user(self, cursor, user_id: int) -> None:
        target = {"UserID": user_id}
        if await cursor.exists("gban", target):
            await cursor.delete("gban", target)
        else:
            raise ValueError("そのユーザーが見つかりませんでした。")

    async def getall(self, cursor) -> list:
        return [row async for row in cursor.get_datas("gban", {})]

    async def get(self, cursor, user_id: int) -> tuple:
        target = {"UserID": user_id}
        if await cursor.exists("gban", target):
            return await cursor.get_data("gban", target)
        else:
            return ()

    async def onoff_guild(self, cursor, guild_id: int, onoff: bool) -> None:
        target = {"GuildID": guild_id}
        if (exists := await cursor.exists("gbanOff", target)) and onoff:
            await cursor.delete("gbanOff", target)
        elif not exists and not onoff:
            await cursor.insert_data("gbanOff", target)

    async def get_onoff(self, cursor, guild_id: int) -> bool:
        return not await cursor.exists("gbanOff", {"GuildID": guild_id})


class GlobalBan(commands.Cog, DataManager):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.on_ready())

    async def on_ready(self):
        super(commands.Cog, self).__init__(
            self.bot.mysql
        )
        await self.init_table()

    def get_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        if guild.system_channel:
            return guild.system_channel
        else:
            return choice(guild.text_channels)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self.bot.is_ready() or await self.get_onoff(member.guild.id):
            return
        if (row := await self.get(member.id)):
            await member.ban(reason=row[1])

            if (channel := self.get_channel(member.guild)):
                await channel.send(
                    f"{member.name}をBANしました。\n理由：\n{row[1]}"
                )

    @commands.group(extras={
        "headding": {
            "ja": "グローバルBAN機能",
            "en": "Global Ban"
        }, "parent": "ServerSafety"
    })
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def gban(self, ctx):
        """!lang ja
        --------
        GBAN機能です。  
        これは危険人物が入ってきたら自動でBANする機能です。  
        危険人物を申請したい場合は対象の人物のIDと証拠と一緒にRTサーバーに問い合わせてください。  
        必要な証拠はパソコンで撮影する場合は再読み込みの動作をしている動画である必要があります。  
        (文字などを開発者ツールから編集し偽装することができるため。)  
        スマホまたはタブレットで撮影する場合はスクリーンショットで大丈夫です。  
        もし証拠を撮るのがめんどくさい場合で元のメッセージが削除されないであろうと考えられる場合は、RTの管理者に直接証拠を見てもらうことも可能です。

        !lang en
        --------
        GBAN function.  
        This is a function to automatically BAN when a dangerous person enters.  
        If you want to apply for a dangerous person, contact the RT server with the person's ID and evidence.  
        The evidence you need is that the video is being reloaded when you shoot with a computer.  
        (You can edit and impersonate text from developer tools.)  
        You can take a screenshot with your smartphone or tablet.  
        If taking evidence is cumbersome and you think the original message will not be deleted, you can have the RT administrator look at the evidence directly."""
        if not ctx.invoked_subcommand:
            view = componesy.View("GbanSSView", timeout=15)
            view.add_item(
                "link_button", style=discord.ButtonStyle.link,
                label="サポートサーバー / SupportServer", url=INFO_SS
            )
            await ctx.reply(
                {"ja": "RTのGBANをするにはサポートサーバーにて申請をする必要があります。",
                 "en": "You can apply user to RT's gban."},
                view=view
            )

    @gban.command()
    async def onoff(self, ctx):
        """!lang ja
        --------
        GBANのOnOffを切り替えます。

        !lang en
        --------
        Gban Enable/Disable Switch Command."""
        await ctx.trigger_typing()
        await self.onoff_guild(ctx.guild.id, not await self.get_onoff(ctx.guild.id))
        await ctx.reply("Ok")

    @gban.command("list")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def gban_list(self, ctx):
        """!lang ja
        --------
        Gbanされている人のリストを表示します。

        !lang en
        --------
        Show you gban list."""
        embeds = Embeds("GbanList", target=ctx.author.id)

        for i, row in enumerate(await self.getall()):
            if row:
                user = await self.bot.fetch_user(row[0])
                if user:
                    embeds.add_embed(
                        discord.Embed(
                            title=f"{i} {user.name}",
                            description=f"ID:{user.id}\n{row[1]}",
                            color=self.bot.colors["normal"]
                        )
                    )

        if embeds.embeds:
            await ctx.reply(embeds=embeds)
        else:
            await ctx.reply(
                {"ja": "gbanされた人はいません。らぶあんどぴーす",
                 "en": "GBanned user is not found."}
            )

    @gban.command("add")
    @is_admin()
    async def add_user_(self, ctx, user_id: int, *, reason):
        await ctx.trigger_typing()
        await self.add_user(user_id, reason)

        for guild in self.bot.guilds:
            if not self.get_onoff(guild.id):
                # オフに設定してるサーバーは無視する。
                continue
            for member in guild.members:
                if member.id == user_id:
                    try:
                        await member.ban(reason=reason)
                        if (channel := self.get_channel(guild)):
                            await channel.send(
                                f"{member.name}をBANしました。\n理由：\n{reason}"
                            )
                    except Exception as e:
                        print("Error on gban :", e)

        await ctx.reply("追加しました。")

    @gban.command("remove")
    @is_admin()
    async def remove_user_(self, ctx, user_id: int):
        await ctx.trigger_typing()
        await self.remove_user(user_id)

        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id == user_id:
                    try:
                        await member.unban()
                        if (channel := self.get_channel(guild)):
                            await channel.send(
                                f"{member.name}のBANを解除しました。"
                            )
                    except Exception as e:
                        print("Error on ungban :", e)

        await ctx.reply("削除しました。")


def setup(bot):
    bot.add_cog(GlobalBan(bot))
