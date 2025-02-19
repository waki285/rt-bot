# RT - Database Manager

from discord.ext import commands
from ujson import loads

from data import is_admin


class DatabaseManager(commands.Cog):
    def __init__(self, bot):
        self.bot, self.rt = bot, bot.data

    @commands.Cog.listener()
    async def on_ready(self):
        self.db = await self.rt["mysql"].get_database()
        # テスト用のテーブルを作る。
        async with self.db.get_cursor() as cursor:
            columns = {
                "c1": "TEXT",
                "c2": "TEXT",
                "c3": "TEXT",
                "json": "TEXT"
            }
            await cursor.create_table("test", columns)

    @commands.group(aliases=("db",),
                    extras={
                        "headding": {"ja": "データベース管理用コマンドです。",
                                     "en": "Database management commands"},
                        "parent": "Admin"
                    })
    async def database(self, cursor, ctx):
        """!lang ja
        --------
        データベースを操作するための管理者用のコマンドです。
        
        !lang en
        -------
        This can edit database, It's can use only admin."""
        if not ctx.invoked_subcommand:
            await ctx.reply("使い方が間違っています。")

    @database.command()
    @is_admin()
    async def create_table(self, ctx, table, columns, ine: bool = True, commit: bool = True):
        """
        !lang ja
        --------
        データベースに新しくテーブルを追加します。

        Parameters
        ----------
        table : str
            追加するテーブルの名前です。
        columns : dict
            追加するテーブルのコラムです。
            `"`ではなく`'`を使用してください。
            型と一緒に書きます。
        ine : bool, default True
            もしないなら作りもし既にテーブルが存在するなら何もしないようにするかどうかです。
            これをFalseにした場合は既にテーブルがあった際にエラーが発生します。
        commit : bool, default True
            コマンドの実行後に自動でcommitをするかどうかです。

        Examples
        --------
        IDは整数で名前が文字列のテーブルを作成します。
        `rt!database create_table credit "{'id':'INTEGER','name':'TEXT'}"`
        !lang en
        --------
        add to database.
        
        Parameters
        ----------
        table : str
            add to table name
        columns : dict
            add to table column
            please use `'`
            write with type
        ine : bool, default True
            if table is not at database it create new table.
            if table is at database ignore
            If this is set to False, an error will occur when the table already exists.
        commit : bool, default True
            if command use, It can do auto commit. 
        """
        columns = loads(columns)
        async with self.db.get_cursor() as cursor:
            await cursor.create_table(
                table, colunms.replace("'", '"'), ine, commit)
        await ctx.reply("Ok")

    @database.command()
    @is_admin()
    async def drop_table(self, ctx, table, commit: bool = True):
        """!lang ja
        --------
        データベースからテーブルを削除します。

        Parameters
        ----------
        table : str
            削除するテーブルの名前です。
        commit : bool, defualt True
            削除後に自動でcommitをするかどうかです。"""
        async with self.db.get_cursor() as cursor:
            await cursor.drop_table(table, commit)
        await ctx.reply("Ok")

    @database.command()
    @is_admin()
    async def insert_data(self, ctx, table, values, commit: bool = True):
        """!lang ja
        --------
        データベースに新しくデータを追加します。
        存在するしない関係なく追加されます。
        もしデータの更新を行うのなら`rt!database update_data`の方を使用しましょう。

        Parameters
        ----------
        table : str
            どのテーブルにデータを追加するかです。
        values : dict
            コラム名とそのコラムに何を追加するかです。
            `{'コラム名':'追加内容'}`
        commit : bool, default True
            データの追加後に自動でcommitを行うかどうかです。

        Examples
        --------
        IDと名前を設定してデータを登録します。
        `rt!database insert_data credit "{'id':634763612535390209,'name':'tasuren'}"`"""
        async with self.db.get_cursor() as cursor:
            await cursor.insert_data(table, loads(values.replace("'", '"')), commit)
        await ctx.reply("Ok")

    @database.command()
    @is_admin()
    async def update_data(self, ctx, table, values, targets, commit: bool = True):
        """!lang ja
        --------
        データベースにあるデータの更新をします。

        Parameters
        ----------
        table : str
            更新したいデータのあるテーブル名です。
        values : dict
            更新するもののコラム名と値です。
        targets : dict
            更新するものにあるコラムのコラム名と値です。
        commit : bool, defualt True
            更新後に自動でcommitをするかどうかです。

        Examples
        --------
        特定のIDにあるnameのコラムを`tasurenはアイワナ`に変更します。
        `rt!database update_data credit "{'id':634763612535390209}" "{'name':'tasurenはアイワナ'}"`"""
        async with self.db.get_cursor() as cursor:
            await cursor.update_data(
                table, loads(values.replace("'", '"')),
                loads(targets.replace("'", '"')), commit)
        await ctx.reply("Ok")

    @database.command()
    @is_admin()
    async def exists(self, ctx, table, targets):
        """!lang ja
        --------
        データベースに指定した条件に一致するデータが存在するかどうかを調べます。

        Parameters
        ----------
        table : str
            調べたいデータがあるテーブル名です。
        targets : dict
            調べたいデータのわかっている条件です。

        Examples
        --------
        Takkunが開発者に含まれているか確認している様子。
        `rt!database exists credit "{'id':667319675176091659}"`"""
        async with self.db.get_cursor() as cursor:
            b = await cursor.exists(table, loads(targets.replace("'", '"')))
        await ctx.reply("Ok `" + str(b) + "`")

    @database.command()
    @is_admin()
    async def delete(self, ctx, table, targets, commit: bool = True):
        """!lang ja
        --------
        データベースにあるデータを削除します。

        Parameters
        ----------
        table : str
            削除するデータがあるテーブル名です。
        targets : dict
            削除するデータの情報です。
        commit : bool, default True
            削除後にcommitを行うかどうかです。

        Examples
        --------
        開発者からとある人を削除する様子。
        `rt!database delete credit "{'id':693025129806037003}"`"""
        async with self.db.get_cursor() as cursor:
            await cursor.delete(table, loads(targets.replace("'", '"')), commit)
        await ctx.reply("Ok")

    @database.command()
    @is_admin()
    async def get_data(self, ctx, table, targets, fetchall: bool = False):
        """!lang ja
        --------
        データベースからデータを取得します。

        Parameters
        ----------
        table : str
            取得するデータがあるテーブル名。
        tarets : dict
            取得するデータの条件です。
        fetchall : bool, default False
            取得するデータを全て取得するかどうかです。
            デフォルトのFalseだと一つしか取得しません。

        Examples
        --------
        名前を忘れた開発者の名前を取得しようとしている様子。
        `rt!database get_data credit "{'id':266988527915368448}"`"""
        async with self.db.get_cursor() as cursor:
            targets = loads(targets.replace("'", '"'))
            if fetchall:
                rows = [row async for row in cursor.get_datas(table, targets)]
            else:
                rows = await cursor.get_data(table, targets)
        await ctx.reply("Ok\n```\n" + str(rows) + "\n```")
        del rows

    @database.command()
    @is_admin()
    async def execute(self, ctx, *, cmd):
        """!lang ja
        --------
        データベースで任意のコマンドを実行します。

        Parameters
        ----------
        cmd : str
            実行するコードです。"""
        commit, fetch = False, False
        if "--commit " in cmd:
            cmd = cmd.replace("--commit ", "")
            commit = True
        if "--fetch " in cmd:
            cmd = cmd.replace("--fetch ", "")
            fetch = True
        async with self.db.get_cursor() as cursor:
            await cursor.cursor.execute(cmd)
            if commit:
                await self.db.commit()
                rows = "..."
            if fetch:
                rows = await cursor.fetchall()
        await ctx.reply(f"Ok\n```\n{rows}\n```")


def setup(bot):
    bot.add_cog(DatabaseManager(bot))
