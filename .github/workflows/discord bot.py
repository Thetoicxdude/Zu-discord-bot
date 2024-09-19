import os
import copy
import json
import math
import time
import uuid
import discord
import sqlite3
import tracemalloc
from collections import deque
from datetime import datetime, timedelta, timezone
import discord
import datetime
import datetime as dt
from discord.ext import commands
from discord.ext import tasks, commands
from matplotlib import pyplot as plt
from io import BytesIO
import asyncio
import logging
import random

#====================================================

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, command_prefix='!')


logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__) 

Database = "discord.db"

#sqlite生成---------------------------------------------------------------------------------------------------------
conn = sqlite3.connect(Database)
cursor = conn.cursor()
# 創建bag表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS bag (
        item_name TEXT ,
        quantity INTEGER ,
        item_type TEXT ,
        owner_id INTEGER 
    )
''')

# 創建equip_bag表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS equip_bag (
        equipment_id INTEGER PRIMARY KEY,
        item_name TEXT,
        item_type TEXT,
        level INTEGER,
        Rarity TEXT,
        attack INTEGER,
        main_job TEXT,
        defense INTEGER,
        Hp INTEGER,
        Mp INTEGER,
        Mp_cost INTEGER,
        owner_id INTEGER,
        equipped BOOLEAN DEFAULT 0, -- 新增是否穿戴的欄位，預設為未穿戴
        FOREIGN KEY (owner_id) REFERENCES player_info(user_id)
    )
''')

# 創建items表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        seller_id INTEGER ,
        item_name TEXT ,
        quantity INTEGER ,
        rarity TEXT ,
        level INTEGER ,
        attack INTEGER ,
        defense INTEGER ,
        Hp INTEGER ,
        Mp INTEGER ,
        Mp_cost INTEGER ,
        item_type TEXT NOT NULL,
        price INTEGER NOT NULL,
        shop TEXT NOT NULL,
        player_id INTEGER NOT NULL,
        FOREIGN KEY (seller_id) REFERENCES player_info (user_id),
        FOREIGN KEY (player_id) REFERENCES player_info (user_id)
        FOREIGN KEY (seller_id) REFERENCES bag(owner_id)
    )
''')


# 創建monster_info表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS monster_info (
        monster_name TEXT ,
        HP INTEGER ,
        max_HP INTEGER ,
        attack INTEGER ,
        defense INTEGER ,
        strength INTEGER ,
        intelligence INTEGER 
    )
''')

# 創建farmers表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER ,
        planting_time INTEGER ,
        planting_item TEXT ,
        FOREIGN KEY (player_id) REFERENCES player_info(id)
    )
''')

# 創建player_info表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_info (
        user_id INTEGER ,
        main_job TEXT ,
        sub_job TEXT,
        level INTEGER ,
        HP INTEGER ,
        max_HP INTEGER ,
        attack INTEGER ,
        defense INTEGER ,
        strength INTEGER ,
        intelligence INTEGER ,
        money INTEGER ,
        player_id INTEGER ,
        satiation INTEGER ,
        MP INTEGER ,
        max_MP INTEGER ,
        last_checkin TEXT,
        Main_story TEXT,
        experience INTEGER,
        max_experience INTEGER,
        Ability_points INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (player_id) REFERENCES farmers(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS map (
        user_id INTEGER ,
        world TEXT,
        region TEXT,
        x INTEGER,
        y INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS guilds (
        guild_id INTEGER PRIMARY KEY,
        guild_name TEXT,
        guild_leader_id INTEGER,
        approval_required BOOLEAN DEFAULT 0,
        minimum_level INTEGER DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_members (
        user_id INTEGER,
        guild_id INTEGER,
        position TEXT,
        FOREIGN KEY (user_id) REFERENCES user_info(user_id),
        FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
        PRIMARY KEY (user_id, guild_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_applications (
        application_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        guild_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES user_info(user_id),
        FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS  auction(
        auction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id INTEGER,
        item_name TEXT,
        start_time INTEGER,
        end_time INTEGER,
        original_end_time INTEGER,
        highest_bidder_id INTEGER,
        highest_bid INTEGER,
        quantity INTERGER,
        item_type TEXT,
        FOREIGN KEY (seller_id) REFERENCES users (user_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS quests (
        quest_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        trigger_region TEXT,
        reward_money INTEGER,
        reward_item_name TEXT,
        reward_item_quantity INTEGER,
        reward_loop TEXT,
        completion_region TEXT,
        user_id INTEGER,
        progress INTEGER DEFAULT 0,  -- 新增進度欄位，預設為0
        FOREIGN KEY (user_id) REFERENCES players (user_id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_market (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        shop TEXT,
        date DATE,
        week INTEGER,
        average_price REAL,
        highest_price REAL,
        lowest_price REAL
    )
''')
# 提交更改並關閉連接
conn.commit()
conn.close()


# 裝備設計
equipment_designs = {
    "weapons": {
        "新手大劍": {"level": 1,"Rarity": "D", "attack": 5, "main_job": "戰士", "enhanced": False},
        "新手大劍+1": {"level": 2,"Rarity": "D", "attack": 7, "main_job": "戰士", "enhanced": True},
        "新手大劍+2": {"level": 3,"Rarity": "D", "attack": 10, "main_job": "戰士", "enhanced": True},
        "新手大劍+3": {"level": 4,"Rarity": "D", "attack": 15, "main_job": "戰士", "enhanced": True},

        "新手短劍": {"level": 1,"Rarity": "D", "attack": 10, "main_job": "刺客", "enhanced": False},
        "新手短劍+1": {"level": 2,"Rarity": "D", "attack": 15, "main_job": "刺客", "enhanced": True},
        "新手短劍+2": {"level": 3,"Rarity": "D", "attack": 20, "main_job": "刺客", "enhanced": True},
        "新手短劍+3": {"level": 4,"Rarity": "D", "attack": 25, "main_job": "刺客", "enhanced": True},

        "新手長弓": {"level": 1,"Rarity": "D", "attack": 10, "main_job": "射手", "enhanced": False},
        "新手長弓+1": {"level": 2,"Rarity": "D", "attack": 15, "main_job": "射手", "enhanced": True},
        "新手長弓+2": {"level": 3,"Rarity": "D", "attack": 20, "main_job": "射手", "enhanced": True},
        "新手長弓+3": {"level": 4,"Rarity": "D", "attack": 25, "main_job": "射手", "enhanced": True},

        "新手法杖": {"level": 1,"Rarity": "D", "attack": 7, "main_job": "法師", "enhanced": False},
        "新手法杖+1": {"level": 2,"Rarity": "D", "attack": 10, "main_job": "法師", "enhanced": True},
        "新手法杖+2": {"level": 3,"Rarity": "D", "attack": 15, "main_job": "法師", "enhanced": True},
        "新手法杖+3": {"level": 4,"Rarity": "D", "attack": 20, "main_job": "法師", "enhanced": True}
    },
    "helmet": {
        "新手頭盔": {"level": 1,"Rarity": "D", "defense": 5, "enhanced": False},
        "新手頭盔+1": {"level": 2,"Rarity": "D", "defense": 7, "enhanced": True},
        "新手頭盔+2": {"level": 3,"Rarity": "D", "defense": 10, "enhanced": True},
        "新手頭盔+3": {"level": 4,"Rarity": "D", "defense": 15, "enhanced": True}
    },
    "armor": {
        "新手胸甲": {"level": 1,"Rarity": "D", "defense": 10, "enhanced": False},
        "新手胸甲+1": {"level": 2,"Rarity": "D", "defense": 15, "enhanced": True},
        "新手胸甲+2": {"level": 3,"Rarity": "D", "defense": 20, "enhanced": True},
        "新手胸甲+3": {"level": 4,"Rarity": "D", "defense": 15, "enhanced": True}
    },
    "pant": {
        "新手褲子": {"level": 1,"Rarity": "D", "defense": 8, "enhanced": False},
        "新手褲子+1": {"level": 2,"Rarity": "D", "defense": 10, "enhanced": True},
        "新手褲子+2": {"level": 3,"Rarity": "D", "defense": 13, "enhanced": True},
        "新手褲子+3": {"level": 4,"Rarity": "D", "defense": 17, "enhanced": True}
    },
    "shoe": {
        "新手鞋子": {"level": 1,"Rarity": "D", "defense": 4, "enhanced": False},
        "新手鞋子+1": {"level": 2,"Rarity": "D", "defense": 5, "enhanced": True},
        "新手鞋子+2": {"level": 3,"Rarity": "D", "defense": 7, "enhanced": True},
        "新手鞋子+3": {"level": 4,"Rarity": "D", "defense": 10, "enhanced": True}
    },
    "Jewelry": {
        "新手戒指": {"level": 1,"Rarity": "D", "attack": 5, "defense": 5, "enhanced": False},
        "新手戒指+1": {"level": 2,"Rarity": "D", "attack": 10, "defense": 10, "enhanced": True},
        "新手戒指+2": {"level": 3,"Rarity": "D", "attack": 15, "defense": 15, "enhanced": True},
        "新手戒指+3": {"level": 4,"Rarity": "D", "attack": 20, "defense": 20, "enhanced": True}
    },
    "skill_1": {
        "護甲": {"level": 1,"Rarity": "D", "main_job": "戰士", "Mp": "30"},
        "突刺": {"level": 1,"Rarity": "D", "main_job": "刺客", "Mp": "30"},
        "隱身": {"level": 1,"Rarity": "D", "main_job": "刺客", "Mp": "20"},
        "血刃": {"level": 1,"Rarity": "D", "main_job": "刺客", "Mp": "35"},
        "箭裂": {"level": 1,"Rarity": "D", "main_job": "射手", "Mp": "30"},
        "火球術": {"level": 1,"Rarity": "D", "main_job": "法師", "Mp": "25"}
    }
}

#=================================================================================================================



logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__) 


class DatabasePool:
    def __init__(self):
        self.conn = sqlite3.connect(Database, timeout=180)  # 设置超时时间为10秒
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def execute(self, query, *args):
        try:
            self.cursor.execute(query, args)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            logger.error("数据库操作出现异常：%s", e)
            raise
    def fetchone(self, query, *args):
        try:
            cursor = self.execute(query, *args)
            return cursor.fetchone()
        except Exception as e:
            logger.error("数据库操作出现异常：%s", e)
            raise

    def fetchall(self, query, *args):
        try:
            cursor = self.execute(query, *args)
            return cursor.fetchall()
        except Exception as e:
            logger.error("数据库操作出现异常：%s", e)
            raise

    def __del__(self):
        self.conn.close()

db_pool = DatabasePool()



# 注册----------------------------------------------------------------------------------------------------------------------------------
@bot.command()
async def register(ctx):
    member_id = ctx.author.id
    # 检查 member_id 是否已注册
    result = db_pool.fetchone("SELECT player_id FROM player_info WHERE user_id = ?", member_id)
    if result:
        # 如果已經註冊過，則更新成員身分組
        embed = discord.Embed(color=0x00ff9d)
        embed.add_field(name=f"您已註冊過了！id是: {result['player_id']}", value="", inline=False)
        embed.set_footer(text="我是ZU, 为您服务")
        await ctx.send(embed=embed)
         # 給玩家身分組
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name="玩家")
        await ctx.author.add_roles(role)
        '''
        # 播放完成註冊音效
        voice_client = discord.utils.get(bot.voice_clients, guild=guild)
        if voice_client and voice_client.is_connected():
            voice_client.play(discord.FFmpegPCMAudio("sound/register.mp3"))
        else:
            voice_channel = discord.utils.get(guild.voice_channels, name="🎤┃語音頻道")
            await voice_channel.connect()
            voice_client = discord.utils.get(bot.voice_clients, guild=guild)
            voice_client.play(discord.FFmpegPCMAudio("sound/register.mp3"))
        return
        '''
    else:
        # 尚未注册，将成员添加到注册数据表中
        registered_count = db_pool.fetchone("SELECT COUNT(*) FROM player_info")[0]
        player_id = 10000 + registered_count + 1

        db_pool.execute("INSERT INTO player_info (user_id, player_id) VALUES (?, ?)", member_id, player_id)
        sql = "UPDATE player_info SET level = ?, money = ?, satiation = ?, experience = ?, max_experience = ?, Main_story = ?, Ability_points = ? WHERE user_id = ?"
        db_pool.execute(sql, 1, 500, 20, 0, 100, "1-1", 10, member_id)
        map_query = "INSERT INTO map (world, region, x, y, user_id) VALUES (?, ?, ?, ?, ?)"
        db_pool.execute(map_query, "五約十制", "新手村", 0, 0, member_id)
    embed = discord.Embed(color=0x00ff9d)
    embed.add_field(name=f"您的玩家ID是: {player_id}", value="您已經成功註冊！請使用指令來遊玩。", inline=False)
    embed.set_footer(text="我是ZU, 为您服务")
    await ctx.send(embed=embed)
    # 給玩家身分組
    channel_id = 1202978654334750781  # 替換為實際的頻道ID
    channel = bot.get_channel(channel_id)
    if channel == 1202978654334750781:
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name="玩家")
        await ctx.author.add_roles(role)

#引導----------------------------------------------------------------------------------------------------------------------------------
@bot.command()
async def play(ctx):
    help_embed = discord.Embed(title="遊戲指令", description="歡迎來到我們的遊戲！以下是遊戲中可用的指令：", color=0x00ff00)

    # Character Management
    help_embed.add_field(name="1. 角色管理", value="!register - 註冊\n!main_job - 主職業的選擇\n!sub_job - 副職業的選擇\n!change_main_job - 主職業的轉職\n!change_sub_job - 副職業的轉職\n!player_info - 玩家數值\n!assign_points `屬性` `點數` - 能力值加點\n!bag - 查看背包\n!equip - `裝備名稱`裝備裝備\n!unequip - `裝備名稱`卸下裝備\n!equipment - 查看裝備", inline=False)

    # Trading and Economy
    help_embed.add_field(name="2. 交易和經濟", value="!add `物品` `數量` `價格` - 上架物品\n!remove `物品` `數量` - 下架物品\n!shop_list `玩家` - 查詢上架狀況\n!buy `玩家` `物品` `數量` - 買物品\n!start_auction `物品` `數量` `起拍價格` `拍賣時間(min)` - 拍賣\n!bid `賣家` `物品` `競標價格` - 競標\n!my_auctions - 查看拍賣和競標清單\n!auction_info `物品` - 查看此物有哪些拍賣再進行", inline=False)

    # Professions
    help_embed.add_field(name="3. 職業", value="!plant - 種植(農夫限定\n!harvest - 採收(農夫限定\n!cook `料理` - 煮菜 料理: 燉白菜 ,沙拉, 大雜燴(廚師限定\n!mine - 挖礦(礦工限定\n!collect - 採藥(採藥人限定\n!brew `藥水` - 釀造 藥水: 人參湯, 雙回復藥水, 治療藥水, 回魔藥水(藥劑師限定\n!eat 料理 - 補飽食度", inline=False)

    # Guild Management
    help_embed.add_field(name="4. 公會管理", value="!build_guild `公會名稱` - 創建公會\n!search_guilds - 搜索公會\n!join_guild `公會名稱` - 加入公會\n!guild - 查看公會信息\n!guild_members - 查看公會成員信息\n!appoint_officer `職位` - 任命職位(僅限公會長", inline=False)

    # Map and Movement
    help_embed.add_field(name="5. 地圖和移動", value="!move `地區` `x,y` - 前往至理想位置\n!location - 查看目前位置", inline=False)

    help_embed.set_footer(text="註冊後將會前往新手村! 需要更詳細的教程使用!teach")

    await ctx.send(embed=help_embed)

@bot.command()
async def teach(ctx):
    tutorials = [
        ("歡迎來到我們的遊戲！", "**教程一：註冊**\n1. 首先，使用 `!register` 指令來註冊您的角色。"),
        ("教程一：註冊", "2. 接著，選擇您的主職業和副職業，您可以使用 `!main_job` 和 `!sub_job` 指令進行選擇。"),
        ("教程一：註冊", "3. 如果您想轉換職業，可以使用 `!change_main_job` 和 `!change_sub_job` 指令。"),
        ("教程二：角色管理", "**教程二：角色管理**\n1. 使用 `!player_info` 指令查看您的角色信息和數值。"),
        ("教程二：角色管理", "2. 您可以使用 `!bag` 指令查看您的背包中的物品。"),
        ("教程二：角色管理", "3. 您可以使用 `!!assign_points 屬性 點數` 指令增加能力值。"),
        ("教程二：角色管理", "4. 若要裝備或卸下裝備，請使用 `!equip` 和 `!unequip` 指令。"),
        ("教程二：角色管理", "5. 使用 `!equipment` 指令查看您當前裝備的狀態。"),
        ("教程三：交易和經濟", "**教程三：交易和經濟**\n1. 想要上架物品嗎？使用 `!add 物品 數量 價格` 指令。"),
        ("教程三：交易和經濟", "2. 若要下架物品，請使用 `!remove 物品 數量` 指令。"),
        ("教程三：交易和經濟", "3. 查看其他玩家上架的物品，使用 `!shop_list 玩家` 指令。"),
        ("教程三：交易和經濟", "4. 想要購買物品？使用 `!buy 玩家 物品 數量` 指令。"),
        ("教程四：職業", "**教程四：職業**\n1. 想要成為一名農夫、廚師、礦工或藥劑師嗎？使用相應的指令開始您的職業生涯吧！"),
        ("教程五：公會管理", "**教程五：公會管理**\n1. 想要創建一個公會？使用 `!build_guild 公會名稱` 指令。"),
        ("教程五：公會管理", "2. 想要加入一個公會？使用 `!join_guild 公會名稱` 指令。"),
        ("教程五：公會管理", "3. 查看您的公會信息，使用 `!guild` 指令。"),
        ("教程六：地圖和移動", "**教程六：地圖和移動**\n1. 使用 `!move 地區 x,y` 指令前往理想的位置。"),
        ("教程六：地圖和移動", "2. 想要知道您目前的位置？使用 `!location` 指令。")
    ]
    
    embed = discord.Embed(title=tutorials[0][0], description=tutorials[0][1], color=0x00ff00)
    message = await ctx.send(embed=embed)
    
    for title, description in tutorials[1:]:
        await asyncio.sleep(10)
        embed = discord.Embed(title=title, description=description, color=0x00ff00)
        await message.edit(embed=embed)

#查詢----------------------------------------------------------------------------------------------------------------------------------
@bot.command()
async def player_info(ctx, member:discord.Member = None):
    if member is None:
       member = ctx.author

    db = sqlite3.connect(Database)
    cursor = db.cursor()

    cursor.execute(f"SELECT main_job, sub_job, level, HP, MP, attack, defense, strength, intelligence, money, satiation, player_id, experience, max_experience, Ability_points FROM player_info WHERE user_id = {member.id}")
    info = cursor.fetchone()
    try:
        main_job = info[0]
        sub_job = info[1]
        level = info[2]
        HP = info[3]
        MP = info[4]
        attack = info[5]
        defense = info[6]
        strength = info[7]
        intelligence = info[8]
        money = info[9]
        satiation = info[10]
        player_id = info[11]
        experience = info[12]
        max_experience = info[13]
        Ability_points = info[14]
    except:
        main_job = None
        sub_job = None
        level = None
        experience = None
        max_experience = None
        HP = None
        MP = None
        attack = None
        defense = None
        strength = None
        intelligence = None
        Ability_points = None
        money = None
        satiation = None
        player_id = None

    embed=discord.Embed(title="您的基本資料：", color=0x00ff9d)
    embed.add_field(name="職業", value=f"\n\n主職業: {main_job}\n副職業: {sub_job}", inline=True)
    embed.add_field(name="角色數值", value=f"等級:{level} ({experience}/{max_experience})\n生命值:{HP}魔力:{MP}\n攻擊力:{attack}防禦力:{defense}\n力量:{strength}智力:{intelligence}\n金錢:{money}飽食度:{satiation}\n能力點:{Ability_points}\nid:{player_id}", inline=False)
    embed.set_footer(text="我是ZU, 為您服務")
    await ctx.send(embed=embed)

#屬性點分配------------------------------------------------------------------------------------------------------
        
# 定義每個屬性的初始值和比例
attribute_info = {
    "生命值": {"initial_value": 5, "en": "max_HP"},
    "魔力": {"initial_value": 5, "en": "max_MP"},
    "攻擊力": {"initial_value": 1, "en": "attack"},
    "防禦力": {"initial_value": 1, "en": "defense"},
    "力量": {"initial_value": 1, "en": "strength"},
    "智力": {"initial_value": 1, "en": "intelligence"}
}

@bot.command()
async def assign_points(ctx, attribute: str, points: int):
    author_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    # 檢查玩家是否有足夠的能力點可用於分配
    cursor.execute("SELECT Ability_points FROM player_info WHERE user_id = ?", (author_id,))
    current_points = cursor.fetchone()[0]
    if current_points < points:
        await ctx.send("您沒有足夠的能力點可用於分配。")
        conn.close()
        return

    # 檢查屬性是否有效
    if attribute not in attribute_info:
        await ctx.send("無效的屬性。")
        conn.close()
        return

    # 根據比例分配能力點到各個屬性
    attribute_value = points * attribute_info[attribute]["initial_value"]
    attribute_en = attribute_info[attribute]["en"]
    cursor.execute(f"UPDATE player_info SET Ability_points = Ability_points - ?, {attribute_en} = {attribute_en} + ? WHERE user_id = ?", (points, attribute_value, author_id))
    conn.commit()

    await ctx.send(f"{attribute} 增加了 {attribute_value}。")

    conn.close()
    
#主職業選擇--------------------------------------------------------------------------------------------------------------------------------
@bot.command()
async def main_job(ctx):
    member = ctx.author

    db = sqlite3.connect(Database)
    cursor = db.cursor()

    cursor.execute("SELECT main_job FROM player_info WHERE user_id = ?", (member.id,))
    main_job = cursor.fetchone()

    if main_job[0] is not None:
        await ctx.send(f"您已經選擇了{main_job[0]}! 請使用 !change_main_job 命令進行轉職")
        db.close()
        return

    embed = discord.Embed(
        title="請選擇您的主職業：",
        description="\n1. 戰士\n2. 刺客\n3. 射手\n4. 法師",
        color=0x00ff9d
    )
    embed.set_footer(text="我是ZU, 為您服務")
    await ctx.send(embed=embed)
    
    cursor.execute(f"SELECT main_job FROM player_info WHERE user_id = {member.id}")
    main_job = cursor.fetchone()

    if main_job[0] is None:
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content in ['1', '2', '3', '4']

        try:
            msg = await bot.wait_for('message', check=check, timeout=180.0)
        except asyncio.TimeoutError:
            await ctx.send("您的操作已超時! 請重新輸入 !job 命令。")
            db.close()
            return

        jobs = {
            '1': ('戰士', (300, 300, 50, 50, 100, 10, 30, 10)),
            '2': ('刺客', (125, 125, 70, 70, 175, 5, 20, 20)),
            '3': ('射手', (100, 100, 100, 100, 200, 5, 20, 15)),
            '4': ('法師', (150, 150, 150, 150, 150, 15, 10, 40))
        }

        main_job, stats = jobs.get(msg.content)

        sql_update = """UPDATE player_info SET
                        HP = ?, Max_Hp = ?, MP = ?, max_Mp = ?,
                        attack = ?, defense = ?, strength = ?, intelligence = ?
                        WHERE user_id = ?"""
        
        game_info = stats + (member.id,)
        cursor.execute(sql_update, game_info)

        sql_main_job = "UPDATE player_info SET main_job = ? WHERE user_id = ?"
        cursor.execute(sql_main_job, (main_job, member.id))

        db.commit()
        db.close()

        embed = discord.Embed(title=f'您選擇了主職業：{main_job}\n\n請使用 !sub_job 來完成副職業選擇', description=main_job, color=0x00ff9d)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)

    else:
        embed = discord.Embed(title=f"您已經選擇了{main_job[0]}!", description="請使用 !change_main_job 命令進行轉職", color=0x00ff9d)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)

#副職業選擇--------------------------------------------------------------------------------------------------------------------------------
    
@bot.command()
async def sub_job(ctx):
    member = ctx.author

    db = sqlite3.connect(Database)
    cursor = db.cursor()

    cursor.execute(f"SELECT sub_job FROM player_info WHERE user_id = {member.id}")
    sub_job = cursor.fetchone()

    if sub_job[0] is None:
        embed=discord.Embed(title="請選擇您的主職業：", description="\n1. 農夫\n2. 廚師\n3. 礦工\n4. 匠人\n5. 採藥人\n6. 藥劑師", color=0x00ff9d)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content in ['1', '2', '3', '4', '5', '6']

        try:
            msg = await bot.wait_for('message', check=check, timeout=180.0)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="您的操作已超時!", description="請重新輸入 !job 命令。", color=0x00ff9d)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return

        if msg.content == '1':
            sub_job = '農夫'
        elif msg.content == '2':
            sub_job = '廚師'
        elif msg.content == '3':
            sub_job = '礦工'
        elif msg.content == '4':
            sub_job = '匠人'
        elif msg.content == '5':
            sub_job = '採藥人'
        elif msg.content == '6':
            sub_job = '藥劑師'

        sql = "UPDATE player_info SET sub_job = ? WHERE user_id = ?"
        val = (sub_job, member.id)
        cursor.execute(sql, val)
        db.commit()
        db.close

        embed = discord.Embed(title=f'您選擇了副職業：{sub_job}\n\n使用 !player_info 可以查看角色數據', description=sub_job, color=0x00ff9d)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)

    else:
        embed = discord.Embed(title=f"您已經選擇了 {sub_job[0]}!", description="請使用 !change_sub_job 命令進行轉職", color=0x00ff9d)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        db.commit()
        cursor.close()
        db.close()

#主職業轉職系統-------------------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def change_main_job(ctx):
    member_id = ctx.author.id

    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT main_job FROM player_info WHERE user_id = ?", (member_id,))
    main_job = cursor.fetchone()[0]
    cursor.execute(f"SELECT level FROM player_info WHERE user_id = ?", (member_id,))
    level = cursor.fetchone()[0]
    if main_job is None:
        embed = discord.Embed(title=f"您還沒選擇主職業!", description="請使用 !main_job 命令選擇主職業", color=0x00ff9d)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        conn.close()
        return
    else:
        embed=discord.Embed(title="請選擇您的主職業：", description="\n1. 戰士\n2. 刺客\n3. 射手\n4. 法師", color=0x00ff9d)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel and message.content in ['1', '2', '3', '4']

    try:
        msg = await bot.wait_for('message', check=check, timeout=180.0)
    except asyncio.TimeoutError:
        embed = discord.Embed(title="您的操作已超時!", description="請重新輸入 !change_main_job 命令。", color=0x00ff9d)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        conn.close()
        return

    if msg.content == '1':
        new_main_job = '戰士'
        game_info = (300, 300, 50, 50, 100, 10, 30, 10, level*3+7, member_id)
    elif msg.content == '2':
        new_main_job = '刺客'
        game_info = (125, 125, 70, 70, 175, 5, 20, 20, level*3+7, member_id)
    elif msg.content == '3':
        new_main_job = '射手'
        game_info = (100, 100, 100, 100, 200, 5, 20, 15, level*3+7, member_id)
    elif msg.content == '4':
        new_main_job = '法師'
        game_info = (150, 150, 150, 150, 15, 10, 40, level*3+7, member_id)
    
    # 更新玩家主職業和數值
    sql = """UPDATE player_info SET
                main_job = ?,
                HP = ?,
                max_Hp = ?,
                MP = ?,
                max_Mp = ?,
                attack = ?,
                defense = ?,
                strength = ?,
                intelligence = ?,
                Ability_points = ?
                WHERE user_id = ?"""
    game_info = (new_main_job, *game_info)
    cursor.execute(sql, game_info)

    # 更新裝備穿戴狀態
    cursor.execute("UPDATE equip_bag SET equipped = 0 WHERE owner_id = ? AND equipped = 1", (member_id,))
    
    conn.commit()
    conn.close()

    embed=discord.Embed(color=0x00ff9d)
    embed.add_field(name=f"您的主職業已更新為 {new_main_job} !", value="", inline=False)
    embed.set_footer(text="我是ZU, 為您服務")
    await ctx.send(embed=embed)



#副職業轉職系統-------------------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def change_sub_job(ctx):
    member_id = ctx.author.id

    # 檢查玩家是否已註冊
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT sub_job FROM player_info WHERE user_id = {member_id}")
        sub_job = cursor.fetchone()
        # 更新副職業
        if sub_job[0] is None:
            embed = discord.Embed(title=f"您還沒選擇副職業!", description="請使用 !sub_job 命令選擇主職業", color=0x00ff9d)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        else:
            embed=discord.Embed(title="請選擇您的主職業：", description="\n1. 農夫\n2. 廚師\n3. 礦工\n4. 匠人\n5. 採藥人\n6. 藥劑師", color=0x00ff9d)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content in ['1', '2', '3', '4', '5', '6']

        try:
            msg = await bot.wait_for('message', check=check, timeout=180.0)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="您的操作已超時!", description="請重新輸入 !change_sub_job 命令。", color=0x00ff9d)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return

        if msg.content == '1':
            sub_job = '農夫'
        elif msg.content == '2':
            sub_job = '廚師'
        elif msg.content == '3':
            sub_job = '礦工'
        elif msg.content == '4':
            sub_job = '匠人'
        elif msg.content == '5':
            sub_job = '採藥人'
        elif msg.content == '6':
            sub_job = '藥劑師'

        sql = "UPDATE player_info SET sub_job = ? WHERE user_id = ?"
        val = (sub_job, member_id)
        cursor.execute(sql, val)
        conn.commit()
        cursor.close()
        conn.close()

        embed=discord.Embed(color=0x00ff9d)
        embed.add_field(name=f"您的副職業已更新為 {sub_job}。", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error("副職業轉職指令出现异常：%s", e)
        await ctx.send("副職業轉職時發生了錯誤, 請聯繫管理員。")
#背包系統---------------------------------------------------------------------------------------------------------------------------------
@bot.command()
async def bag(ctx):
    author_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    # 查詢裝備
    cursor.execute("SELECT item_name, level, Rarity FROM equip_bag WHERE owner_id = ?", (author_id,))
    equip_items = cursor.fetchall()

    # 查詢背包材料、食物和藥水
    cursor.execute("SELECT item_name, quantity, item_type FROM bag WHERE owner_id = ? AND item_type IN ('材料', '食物', '藥水')", (author_id,))
    items = cursor.fetchall()

    conn.close()

    # 分類背包內容
    material_items = "\n".join([f'{item[0]} - {item[2]}: {item[1]}' for item in items if item[2] == "材料"])
    food_items = "\n".join([f"{item[0]} - {item[2]}: {item[1]}" for item in items if item[2] == "食物"])
    potion_items = "\n".join([f"{item[0]} - {item[2]}: {item[1]}" for item in items if item[2] == "藥水"])
    equip_items_text = "\n".join([f"{item[0]} lev.{item[1]} Rar.{item[2]}" for item in equip_items])

    # 檢查是否有物品存在
    if not material_items and not food_items and not potion_items and not equip_items_text:
        embed = discord.Embed(color=0x00ff9d)
        embed.add_field(name="您的背包是空的！", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        return

    # 顯示背包內容
    embed = discord.Embed(color=0x00ff9d)
    embed.add_field(name="您的背包內容：", value="", inline=False)
    if material_items:
        embed.add_field(name="材料 :", value=material_items, inline=True)
    if food_items:
        embed.add_field(name="食物 :", value=food_items, inline=True)
    if potion_items:
        embed.add_field(name="藥水 : ", value=potion_items, inline=True)
    if equip_items_text:
        embed.add_field(name="裝備 :", value=equip_items_text, inline=True)
    embed.set_footer(text="我是ZU, 為您服務")
    await ctx.send(embed=embed)
    conn.close()


@bot.command()
async def equip_detail(ctx, item_name: str):
    author_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    # 查詢裝備詳細數值
    cursor.execute("SELECT * FROM equip_bag WHERE owner_id = ? AND item_name = ?", (author_id, item_name))
    equip_data = cursor.fetchall()

    if equip_data is None or len(equip_data) == 0:
        await ctx.send("您的背包中沒有該裝備！")
        conn.close()
        return

    # 發送裝備詳細信息
    embed = discord.Embed(title="裝備詳細信息", color=0x00ff9d)
    for data in equip_data:
        detail_info = f"裝備名稱：{data[1]}\n稀有度：{data[4]}\n等級：{data[3]}\n裝備類型：{data[2]}\n攻擊力：{data[5]}\n防禦力：{data[7]}\nHP：{data[8]}\nMP：{data[9]}\nMP消耗：{data[10]}\n主職業：{data[6]}"
        embed.add_field(name=f"ID : {data[0]}", value=detail_info, inline=False)

    embed.set_footer(text="我是ZU, 為您服務")
    await ctx.send(embed=embed)

    conn.close()


#**開發者模式**拿取物品------------------------------------------------------------------------------------------------------------------------
@bot.command()
async def add_item(ctx, item_name: str, quantity: int, item_type: str):
    author_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    # 檢查背包是否已有該物品
    cursor.execute(f"SELECT user_id FROM player_info WHERE user_id = ?", (author_id,))
    administrator_id  = cursor.fetchone()
    cursor.execute(f"SELECT item_name FROM bag WHERE owner_id = ? AND item_name = ?", (author_id, item_name))
    existing_item = cursor.fetchone()

    if existing_item:
        # 更新物品數量
        cursor.execute(f"UPDATE bag SET quantity = quantity + ? WHERE owner_id = ? AND item_name = ?", (quantity, author_id, item_name))
        conn.commit()
        conn.close()
    else:
        if existing_item is None:
            cursor.execute(f"INSERT INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (author_id, item_name, quantity, item_type))
            conn.commit()
            conn.close()
            embed=discord.Embed(color=0x00ff9d)
            embed.add_field(name=f"已將 {item_name} x{quantity} 加入背包！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)

        # 新增物品到背包
        else:
            cursor.execute(f"UPDATE bag SET item_name = ?, quantity = ?, item_type = ? WHERE user_id = ? AND item_name = ?, player_id = ?",(item_name, quantity, author_id, item_type, item_name, author_id))
            conn.commit()
            conn.close()
            embed=discord.Embed(color=0x00ff9d)
            embed.add_field(name=f"已將 {item_name} x{quantity} 加入背包！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)

@bot.command()
async def add_equipment(ctx, item_name: str, item_type: str, level: int, rarity: str, attack: int, main_job: str, defense: int, HP: int, MP: int, mp_cost: int):
    author_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    # 將裝備添加到 equip_bag 中
    cursor.execute("INSERT INTO equip_bag (item_name, item_type, level, Rarity, attack, main_job, defense, HP, MP, Mp_cost, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                   (item_name, item_type, level, rarity, attack, main_job, defense, HP, MP, mp_cost, author_id))
    conn.commit()
    conn.close()
    await ctx.send(f"已將 {item_name} 添加到裝備欄！")


@bot.command()
async def add_money(ctx, amount: int):
    user_id = str(ctx.author.id)

    if amount <= 0:
        await ctx.send("請輸入有效的金錢數量！")
        return

    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (user_id,))
        current_money = cursor.fetchone()
        cursor.execute(f"SELECT user_id FROM player_info WHERE user_id = ?", (user_id,))
        administrator_id  = cursor.fetchone()
        if not current_money:
            await ctx.send("未找到用戶信息！")
            return
        if administrator_id[0] != 868495302661898250 or 989064899894329355:
            embed=discord.Embed(color=0x00ff9d)
            embed.add_field(name="你沒有使用這個指令的權限！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)

        new_money = current_money[0] + amount
        cursor.execute("UPDATE player_info SET money = ? WHERE user_id = ?", (new_money, user_id))
        conn.commit()

        await ctx.send(f"您的金錢數量已增加 {amount}，当前总额为 {new_money}！")
#查詢餘額---------------------------------------------------------------------------------------------------------------------------------
@bot.command()
async def money(ctx):
    author_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    try:
        # 查詢使用者餘額
        cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (author_id,))
        result = cursor.fetchone()
        money = result[0]
        embed=discord.Embed(color=0x00ff9d)
        embed.add_field(name=f"您的餘額：{money}", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error("查詢餘額指令出现异常：%s", e)
        await ctx.send("查詢餘額發生了錯誤, 請聯繫管理員。")
    
#上架系統-----------------------------------------------------------------------------------------------------------------------------------
@bot.command()
async def add(ctx, *, args: str):
    seller_id = str(ctx.author.id)
    arg_list = args.split()

    # Check if the player is in a shop region
    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM map WHERE user_id = ?", (seller_id,))
        map_info = cursor.fetchone()

        if not map_info:
            embed = discord.Embed(color=0xFF0000)
            embed.add_field(name="請先使用 !register 進行註冊", value="", inline=False)
            embed.set_footer(text="我是ZU，為您服務")
            await ctx.send(embed=embed)
            return

        region_info = get_region(map_info[2], map_info[3], map_info[4])
        shop = ["新手商店"]
        if any(shop_name in region_info for shop_name in shop):
            item = arg_list[0]
            cursor.execute("SELECT * FROM equip_bag WHERE owner_id = ? AND item_name = ?", (seller_id, item))
            player_items = cursor.fetchall()

            if player_items:
                if len(player_items) > 1:
                    # Create a selection menu with buttons for each item
                    select_menu = discord.ui.View()
                    select_options = []
                    for player_item in player_items:
                        item_type = player_item[2]
                        rarity = player_item[3]
                        level = player_item[4]
                        equipment_id = player_item[0]
                        option_id = str(uuid.uuid4())
                        select_options.append(discord.SelectOption(
                            label=f"{item} (Type: {item_type}, Rarity: {rarity}, Level: {level})",
                            value=option_id,
                            description=f"Equipment ID: {equipment_id}"
                        ))

                    select = discord.ui.Select(
                        placeholder="請選擇要上架的裝備",
                        options=select_options
                    )

                    async def select_callback(interaction):
                        selected_id = select.values[0]
                        for option in select.options:
                            if option.value == selected_id:
                                equipment_id = int(option.description.split(": ")[1])
                                cursor.execute("SELECT item_type, rarity, level FROM equip_bag WHERE equipment_id = ? AND owner_id = ?", (equipment_id, seller_id,))
                                result = cursor.fetchone()
                                if result:
                                    item_type, rarity, level = result
                                else:
                                    embed = discord.Embed(color=0xFF0000)
                                    embed.add_field(name="找不到該裝備,可能已被出售或移除", value="", inline=False)
                                    embed.set_footer(text="我是ZU，為您服務")
                                    await interaction.response.send_message(embed=embed)
                                    return

                        if len(arg_list) < 2:
                            embed = discord.Embed(color=0xFF0000)
                            embed.add_field(name="請輸入有效的價格", value="", inline=False)
                            embed.set_footer(text="我是ZU，為您服務")
                            await interaction.response.send_message(embed=embed)
                            return

                        price = int(arg_list[1])

                        # Check if player has enough money to pay tax
                        cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (seller_id,))
                        player_money = cursor.fetchone()[0]
                        tax_rate = 0.05  # 5% tax rate
                        tax_amount = int(price * tax_rate)

                        if player_money < tax_amount:
                            embed = discord.Embed(color=0xFF0000)
                            embed.add_field(name="您的金錢不足以支付稅金！", value="", inline=False)
                            embed.set_footer(text="我是ZU，為您服務")
                            await interaction.response.send_message(embed=embed)
                            return

                        # 在这里添加一个额外的检查,确保获取到了有效的 item_type、rarity 和 level
                        if result is None:
                            embed = discord.Embed(color=0xFF0000)
                            embed.add_field(name="無法獲取裝備信息,請稍後再試", value="", inline=False)
                            embed.set_footer(text="我是ZU，為您服務")
                            await interaction.response.send_message(embed=embed)
                            return

                        cursor.execute("INSERT INTO items (seller_id, item_name, item_type, rarity, level, price, shop, player_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, item, item_type, rarity, level, price, region_info, equipment_id))

                        # Update the player's money and commit the transaction
                        cursor.execute("UPDATE player_info SET money = money - ? WHERE user_id = ?", (tax_amount, seller_id))
                        conn.commit()

                        #將裝備刪除
                        cursor.execute("DELETE FROM equip_bag WHERE equipment_id = ?", (equipment_id,))
                        conn.commit()

                        embed = discord.Embed(color=0x00ff9d)
                        embed.add_field(name=f"已將 {item} 上架，價格為 {price} 在 {region_info}", value=f"將收取 5% 的手續費，金額為 {tax_amount}", inline=False)
                        embed.set_footer(text="我是ZU，為您服務")
                        await interaction.response.send_message(embed=embed)

                    select.callback = select_callback
                    select_menu.add_item(select)
                    await ctx.send("您有多個相同的裝備,請選擇要上架的裝備:", view=select_menu)
                else:
                    player_item = player_items[0]
                    item_type = player_item[2]
                    rarity = player_item[3]
                    level = player_item[4]
                    equipment_id = player_item[0]

                    if len(arg_list) < 2:
                        embed = discord.Embed(color=0xFF0000)
                        embed.add_field(name="請輸入有效的價格", value="", inline=False)
                        embed.set_footer(text="我是ZU，為您服務")
                        await ctx.send(embed=embed)
                        return

                    price = int(arg_list[1])

                    # Check if player has enough money to pay tax
                    cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (seller_id,))
                    player_money = cursor.fetchone()[0]
                    tax_rate = 0.05  # 5% tax rate
                    tax_amount = int(price * tax_rate)

                    if player_money < tax_amount:
                        embed = discord.Embed(color=0xFF0000)
                        embed.add_field(name="您的金錢不足以支付稅金！", value="", inline=False)
                        embed.set_footer(text="我是ZU，為您服務")
                        await ctx.send(embed=embed)
                        return

                    cursor.execute("INSERT INTO items (seller_id, item_name, item_type, rarity, level, price, shop, player_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (seller_id, item, item_type, rarity, level, price, region_info, player_item))

                    # Update the player's money and commit the transaction
                    cursor.execute("UPDATE player_info SET money = money - ? WHERE user_id = ?", (tax_amount, seller_id))
                    conn.commit()

                    #將裝備刪除
                    cursor.execute("DELETE FROM equip_bag WHERE  item_name = ?", (item,))
                    conn.commit()
                    embed = discord.Embed(color=0x00ff9d)
                    embed.add_field(name=f"已將 {item} 上架，價格為 {price} 在 {region_info}", value=f"將收取 5% 的手續費，金額為 {tax_amount}", inline=False)
                    embed.set_footer(text="我是ZU，為您服務")
                    await ctx.send(embed=embed)
            else:
                if len(arg_list) < 2:
                    embed = discord.Embed(color=0xFF0000)
                    embed.add_field(name="請輸入有效的數量和價格", value="", inline=False)
                    embed.set_footer(text="我是ZU，為您服務")
                    await ctx.send(embed=embed)
                    return

                item = arg_list[0]
                price = int(arg_list[2])
                quantity = int(arg_list[1])

                # Check if quantity and price are valid
                if price <= 0:
                    embed = discord.Embed(color=0xFF0000)
                    embed.add_field(name="請輸入有效的價格", value="", inline=False)
                    embed.set_footer(text="我是ZU，為您服務")
                    await ctx.send(embed=embed)
                    return

                # Check if player has enough money to pay tax
                cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (seller_id,))
                player_money = cursor.fetchone()[0]
                tax_rate = 0.05  # 5% tax rate
                tax_amount = int(price * tax_rate)

                if player_money < tax_amount:
                    embed = discord.Embed(color=0xFF0000)
                    embed.add_field(name="您的金錢不足以支付稅金！", value="", inline=False)
                    embed.set_footer(text="我是ZU，為您服務")
                    await ctx.send(embed=embed)
                    return
                cursor.execute("SELECT * FROM bag WHERE owner_id = ? AND item_name = ?", (seller_id, item))
                player_items = cursor.fetchall()
                item_type = player_items[0][2]
                cursor.execute("INSERT INTO items (seller_id, item_name, item_type, quantity, price, shop, player_id) VALUES (?, ?, ?, ?, ?, ?, ?)", (seller_id, item, item_type, quantity, price, region_info, seller_id))

                # Update the player's money and commit the transaction
                cursor.execute("UPDATE player_info SET money = money - ? WHERE user_id = ?", (tax_amount, seller_id))
                conn.commit()

                # 將上架物品數量減上架數量如果數量等於背包內該物品數量則刪除
                cursor.execute("SELECT quantity FROM bag WHERE owner_id = ? AND item_name = ?", (seller_id, item))
                bag_quantity = cursor.fetchone()
                if bag_quantity:
                    bag_quantity = bag_quantity[0]
                    if quantity <= bag_quantity:
                        cursor.execute("UPDATE bag SET quantity = quantity - ? WHERE owner_id = ? AND item_name = ?", (quantity, seller_id, item))
                    else:
                        quantity = bag_quantity
                        cursor.execute("UPDATE bag SET quantity = 0 WHERE owner_id = ? AND item_name = ?", (seller_id, item))

                embed = discord.Embed(color=0x00ff9d)
                embed.add_field(name=f"已將 {item} * {quantity} 上架，價格為 {price} 在 {region_info}", value=f"將收取 5% 的手續費，金額為 {tax_amount}", inline=False)
                embed.set_footer(text="我是ZU，為您服務")
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(color=0xFF0000)
            embed.add_field(name=f"您不在商店區域內，無法上架物品", value="", inline=False)
            embed.set_footer(text="我是ZU，為您服務")
            await ctx.send(embed=embed)

#============================================================================================================================

@bot.command()
async def remove(ctx, *, args: str):
    seller_id = str(ctx.author.id)
    arg_list = args.split()

    if not arg_list:
        embed = discord.Embed(color=0xFF0000)
        embed.add_field(name="請輸入物品名稱以下架", value="", inline=False)
        embed.set_footer(text="我是ZU，為您服務")
        await ctx.send(embed=embed)
        return

    item_name = arg_list[0]

    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM map WHERE user_id = ?", (seller_id,))
        map_info = cursor.fetchone()
        if not map_info:
            embed = discord.Embed(color=0xFF0000)
            embed.add_field(name="請先使用 !register 進行註冊", value="", inline=False)
            embed.set_footer(text="我是ZU，為您服務")
            await ctx.send(embed=embed)
            return

        region_info = get_region(map_info[2], map_info[3], map_info[4])
        shop = ["新手商店"]
        if any(shop_name in region_info for shop_name in shop):
            # 检查物品是否存在于商店中
            cursor.execute("SELECT * FROM items WHERE seller_id = ? AND item_name = ?", (seller_id, item_name))
            item_infos = cursor.fetchall()

            if not item_infos:
                embed = discord.Embed(color=0xFF0000)
                embed.add_field(name="您沒有在商店中上架該物品", value="", inline=False)
                embed.set_footer(text="我是ZU，為您服務")
                await ctx.send(embed=embed)
                return

            # 如果有多個相同名稱的武器,讓玩家選擇要下架的武器
            if len(item_infos) > 1:
                select_menu = discord.ui.View()
                select_options = []
                for item_info in item_infos:
                    item_type = item_info[10]
                    item_rarity = item_info[3]
                    item_level = item_info[4]
                    item_id = item_info[13]
                    option_id = str(uuid.uuid4())
                    select_options.append(discord.SelectOption(
                        label=f"{item_name} (Type: {item_type}, Rarity: {item_rarity}, Level: {item_level})",
                        value=option_id,
                        description=f"Item ID: {item_id}"
                    ))

                select = discord.ui.Select(
                    placeholder="請選擇要下架的武器",
                    options=select_options
                )

                async def select_callback(interaction):
                    selected_id = select.values[0]
                    for option in select.options:
                        if option.value == selected_id:
                            item_id = int(option.description.split(": ")[1])
                            cursor.execute("SELECT item_type FROM items WHERE item_name = ?", (item_name,))
                            item_type = cursor.fetchone()[0]
                            normal = ["材料", "藥水", "食物"]
                            if item_type in normal:
                                # 普通物品直接移除
                                cursor.execute("DELETE FROM items WHERE  item_name = ?", (item_name,))
                                conn.commit()

                                embed = discord.Embed(color=0x00ff9d)
                                embed.add_field(name=f"已成功下架 {item_name}", value="", inline=False)
                                embed.set_footer(text="我是ZU，為您服務")
                                await interaction.response.send_message(embed=embed)
                            else:
                                # 裝備類物品需要將其返回到玩家的裝備袋
                                item_rarity = item_info[3]
                                item_level = item_info[4]
                                cursor.execute("INSERT INTO equip_bag (owner_id, item_name, item_type, rarity, level) VALUES (?, ?, ?, ?, ?)", (seller_id, item_name, item_type, item_rarity, item_level))
                                cursor.execute("DELETE FROM items WHERE player_id = ?", (item_id,))
                                conn.commit()

                                embed = discord.Embed(color=0x00ff9d)
                                embed.add_field(name=f"已成功下架 {item_name}，並返回到您的裝備袋", value="", inline=False)
                                embed.set_footer(text="我是ZU，為您服務")
                                await interaction.response.send_message(embed=embed)

                select.callback = select_callback
                select_menu.add_item(select)
                await ctx.send(f"您有多個 {item_name} 在商店中上架，請選擇要下架的武器:", view=select_menu)
            else:
                # 只有一個相同名稱的武器,直接下架
                item_info = item_infos[0]
                normal = ["材料", "藥水", "食物"]

                if item_info[10] in normal:
                    quantity = item_info[2]
                    item_type = item_info[10]
                    cursor.execute("SELECT quantity FROM bag WHERE owner_id = ? AND item_name = ?", (seller_id, item_name))
                    bag_quantity = cursor.fetchone()
                    if bag_quantity:
                        bag_quantity = bag_quantity[0]
                        cursor.execute("UPDATE bag SET quantity = quantity + ? WHERE owner_id = ? AND item_name = ?", (quantity, seller_id, item_name))
                    else:
                        cursor.execute("INSERT INTO bag (owner_id, item_name, item_type, quantity) VALUES (?, ?, ?, ?)", (seller_id, item_name, item_type,quantity))

                    # 普通物品直接移除
                    cursor.execute("DELETE FROM items WHERE item_name = ?", (item_name,))
                    conn.commit()

                    embed = discord.Embed(color=0x00ff9d)
                    embed.add_field(name=f"已成功下架 {item_name}", value="", inline=False)
                    embed.set_footer(text="我是ZU，為您服務")
                    await ctx.send(embed=embed)
                else:
                    # 裝備類物品需要將其返回到玩家的裝備袋
                    item_rarity = item_info[3]
                    item_level = item_info[4]
                    cursor.execute("INSERT INTO equip_bag (owner_id, item_name, item_type, rarity, level) VALUES (?, ?, ?, ?, ?)", (seller_id, item_name, item_type, item_rarity, item_level))
                    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
                    conn.commit()

                    embed = discord.Embed(color=0x00ff9d)
                    embed.add_field(name=f"已成功下架 {item_name}，並返回到您的背包", value="", inline=False)
                    embed.set_footer(text="我是ZU，為您服務")
                    await ctx.send(embed=embed)
        else:
            embed = discord.Embed(color=0xFF0000)
            embed.add_field(name=f"您不在商店區域內，無法上架物品", value="", inline=False)
            embed.set_footer(text="我是ZU，為您服務")
            await ctx.send(embed=embed)

#架上查詢---------------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def shop_list(ctx, player: discord.User = None):
    if player is None:
        player = ctx.author
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    player_id = str(player.id)

    cursor.execute("SELECT item_name, item_type, quantity, price, rarity, level, attack, defense, Hp, Mp, Mp_cost, shop FROM items WHERE seller_id = ?", (player_id,))
    items_list = cursor.fetchall()

    if not items_list:
        embed = discord.Embed(color=0x00ffbf)
        embed.add_field(name=f"{player.name} 尚未上架任何物品", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title=f"{player.name} 的上架物品", color=discord.Color.green())

        for item in items_list:
            item_name = item[0]
            item_type = item[1]
            quantity = item[2]
            price = item[3]
            rarity = item[4]
            level = item[5]
            attack = item[6]
            defense = item[7]
            Hp = item[8]
            Mp = item[9]
            Mp_cost = item[10]
            shop = item[11]

            if item_type in ["武器", "裝備"]:
                embed.add_field(name=f"{item_name}", value=f"稀有度: {rarity}，等級: {level}，攻擊力: {attack}，防禦力: {defense}\n生命值: {Hp}，魔力值: {Mp}，魔力消耗: {Mp_cost}\n價格: {price}，商店: {shop}", inline=False)
            else:
                embed.add_field(name=f"{item_name}", value=f"數量: {quantity}，價格: {price}，商店: {shop}", inline=False)
                
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)

#架上查詢2---------------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def shop_search(ctx, seller_item: str = None):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    
    cursor.execute("SELECT item_name, item_type, quantity, price, rarity, level, attack, defense, Hp, Mp, Mp_cost, shop, seller_id FROM items WHERE item_name = ?", (seller_item,))
    items_list = cursor.fetchall()

    if not items_list:
        embed = discord.Embed(color=0x00ffbf)
        embed.add_field(name=f"沒有人上架這種商品", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title=f"{seller_item}", color=discord.Color.green())

        for item in items_list:
            item_name = item[0]
            item_type = item[1]
            quantity = item[2]
            price = item[3]
            rarity = item[4]
            level = item[5]
            attack = item[6]
            defense = item[7]
            Hp = item[8]
            Mp = item[9]
            Mp_cost = item[10]
            shop = item[11]
            seller = item[12]
            # seller 原本是id換成名字
            seller = bot.get_user(int(seller))
            if item_type in ["武器", "裝備"]:
                embed.add_field(name=f"{item_name}", value=f"稀有度: {rarity}，等級: {level}，攻擊力: {attack}，防禦力: {defense}\n生命值: {Hp}，魔力值: {Mp}，魔力消耗: {Mp_cost}\n價格: {price}，商店: {shop}，賣家: {seller.name}", inline=False)
            else:
                embed.add_field(name=f"{item_name}", value=f"數量: {quantity}，價格: {price}，商店: {shop}，賣家: {seller.name}", inline=False)

        await ctx.send(embed=embed)
        conn.close()
        
#買系統----------------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def buy(ctx, seller: discord.User, item: str, quantity: int):
    buyer_id = str(ctx.author.id)
    seller_id = str(seller.id)

    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    # 检查是否有玩家的注册信息
    cursor.execute("SELECT * FROM player_info WHERE user_id = ?", (seller_id,))
    player_info = cursor.fetchone()

    if not player_info:
        embed = discord.Embed(color=0xFF0000)
        embed.add_field(name="請先使用 !register 進行註冊", value="", inline=False)
        embed.set_footer(text="我是ZU，為您服務")
        await ctx.send(embed=embed)
        return

    # 查询玩家所在的地图信息
    cursor.execute("SELECT * FROM map WHERE user_id = ?", (seller_id,))
    map_info = cursor.fetchone()

    if not map_info:
        embed = discord.Embed(color=0xFF0000)
        embed.add_field(name="您尚未在地圖上設定位置！", value="", inline=False)
        embed.set_footer(text="我是ZU，為您服務")
        await ctx.send(embed=embed)
        return

    # 获取玩家所在地图区域信息
    region_info = get_region(map_info[2], map_info[3], map_info[4])
    shop_names = ["新手商店"]  # 商店名称列表

    # 检查玩家是否在商店区域
    if any(shop_name in region_info for shop_name in shop_names):
        # 检查是否有此物品的上架记录

        cursor.execute("SELECT * FROM items WHERE seller_id = ? AND item_name = ? AND quantity >= ? AND shop = ?", (seller_id, item, quantity, region_info))
        existing_item = cursor.fetchone()
        if existing_item:
            price = existing_item[3] * quantity

            # 获取玩家的金钱数量
            cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (buyer_id,))
            player_money = cursor.fetchone()

            if player_money[0] < price:
                await ctx.send(f"錢不夠還差 {price - player_money[0]}")
                return

            # 向玩家确认购买操作
            embed = discord.Embed(color=0x00ffbf)
            embed.add_field(name=f"確定要購買 {seller.name} 的 {item} x{quantity} 嗎？", value=f"價格為 {price}", inline=False)
            embed.add_field(name="請輸入 yes 確認購買，或輸入 no 取消。", value="", inline=True)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)

            def check(msg):
                return msg.author == ctx.author and msg.content.lower() in ['yes', 'no']

            try:
                reply = await bot.wait_for('message', timeout=180.0, check=check)
                if reply.content.lower() == 'yes':
                    # 更新数据库中的信息
                    if quantity == existing_item[2]:
                        cursor.execute("DELETE FROM items WHERE seller_id = ? AND item_name = ?", (seller_id, item))
                    else:
                        cursor.execute("UPDATE items SET quantity = quantity - ? WHERE seller_id = ? AND item_name = ?", (quantity, seller_id, item))
                    cursor.execute("UPDATE player_info SET money = money + ? WHERE user_id = ?", (price, seller_id))
                    cursor.execute("UPDATE player_info SET money = money - ? WHERE user_id = ?", (price, buyer_id))
                    cursor.execute("SELECT item_name FROM bag WHERE owner_id = ? AND item_name = ?", (buyer_id, item))
                    player_item = cursor.fetchone()
                    if player_item:
                        cursor.execute("UPDATE bag SET quantity = quantity + ? WHERE owner_id = ? AND item_name = ? ", (quantity, buyer_id, item))
                    else:
                        cursor.execute("INSERT INTO bag (quantity, owner_id, item_name, item_type, player_id) VALUES (?, ?, ?, ?, ?)", (quantity, buyer_id, item, existing_item[4], buyer_id))
                    await ctx.send(f"您購買了 {seller.name} 的 {item} x{quantity}，花了 {price}！")
                else:
                    await ctx.send("交易取消。")
            except asyncio.TimeoutError:
                await ctx.send("交易確認逾時，交易取消。")
            finally:
                conn.commit()
        else:
            await ctx.send("架上沒有此物品")
    else:
        await ctx.send("您不在商店中，無法購買物品。")

    conn.close()
#拍賣系統-----------------------------------------------------------------------------------------------------------------------------------------
        
@bot.command()
async def start_auction(ctx, item: str, quantity: int, starting_price: int, duration_minutes: int):
    seller_id = str(ctx.author.id)
    end_time = int(time.time()) + (duration_minutes * 60)
    tax_rate = 0.10  # 10% 稅率
    if quantity <= 0 or starting_price <= 0 or duration_minutes <= 0:
        embed = discord.Embed(color=0xFF0000)
        embed.add_field(name="請輸入有效的數量和價格", value="", inline=False)
        embed.set_footer(text="我是ZU，為您服務")
        await ctx.send(embed=embed)
        return

    # Check if quantity and price are within reasonable bounds
    max_value = 2**63 - 1  # Maximum value for a signed 64-bit integer
    if quantity > max_value or starting_price > max_value or duration_minutes > 43200:
        embed = discord.Embed(color=0xFF0000)
        embed.add_field(name="請輸入有效的數量, 價格和時間(不得超過一個月)", value="", inline=False)
        embed.set_footer(text="我是ZU，為您服務")
        await ctx.send(embed=embed)
        return
    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bag WHERE owner_id = ? AND item_name = ? AND quantity >= ?", (seller_id, item, quantity))
        player_item = cursor.fetchone()
        item_type = player_item[2]

        # 檢查物品是否在賣家的庫存中
        cursor.execute("SELECT * FROM bag WHERE owner_id = ? AND item_name = ? AND quantity >= ?", (seller_id, item, quantity))
        item_info = cursor.fetchone()

        if item_info:
            # 計算稅金金額
            tax_amount = int(starting_price * tax_rate)
            cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (seller_id,))
            player_money = cursor.fetchone()[0]
            if player_money < tax_amount:
                embed = discord.Embed(color=0xFF0000)
                embed.add_field(name="您的金錢不足以支付稅金！", value="", inline=False)
                embed.set_footer(text="我是ZU，為您服務")
                await ctx.send(embed=embed)
                return
            cursor.execute("UPDATE bag SET quantity = quantity - ? WHERE owner_id = ? AND item_name = ?", (quantity, seller_id, item))
            cursor.execute("UPDATE player_info SET money = money - ? WHERE user_id = ?", (tax_amount, seller_id))

            cursor.execute("""
                INSERT INTO auction (seller_id, item_name, quantity, item_type, start_time, end_time, original_end_time, highest_bidder_id, highest_bid)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """, (seller_id, item, quantity, item_type, int(time.time()), end_time, end_time, starting_price))

            conn.commit()

            # 發送中文的 Embed 訊息
            embed = discord.Embed(title="拍賣開始", description=f"{quantity} 個 {item} 的競標已開始！", color=0x00ffbf)
            embed.add_field(name="起始價格", value=f"{starting_price}，競標截止時間為 {duration_minutes} 分鐘。", inline=False)
            embed.add_field(name="稅金", value=f"將收取 10% 的拍賣費，金額為 {tax_amount}。", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)

            # 設定任務處理拍賣結束
            bot.loop.create_task(handle_auction_end(ctx, seller_id, item, quantity, item_type, end_time, starting_price))
        else:
            await ctx.send("您的庫存中沒有足夠的該物品。")

# 處理拍賣結束的函數
async def handle_auction_end(ctx, seller_id, item, quantity, item_type, end_time, starting_price):
    await asyncio.sleep(end_time - int(time.time()))  # 等待拍賣結束

    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()

        # 檢索指定物品的拍賣信息
        cursor.execute("""
            SELECT * FROM auction
            WHERE seller_id = ? AND item_name = ? AND end_time = ?
        """, (seller_id, item, end_time))

        auction_info = cursor.fetchone()

        if auction_info:
            highest_bidder_id = auction_info[6]
            highest_bid = auction_info[7]

            # 檢查用戶ID是否有效，然後再獲取用戶
            highest_bidder = None
            try:
                highest_bidder = await bot.fetch_user(int(highest_bidder_id))
            except discord.errors.NotFound:
                pass

            if highest_bidder:
                # 更新賣家的金錢，並將物品轉移給最高競標者
                cursor.execute("SELECT item_name FROM bag WHERE owner_id = ? AND item_name = ?", (highest_bidder_id, item))
                player_item = cursor.fetchone()

                cursor.execute("UPDATE player_info SET money = money + ? WHERE user_id = ?", (highest_bid, seller_id))
                cursor.execute("UPDATE player_info SET money = money - ? WHERE user_id = ?", (highest_bid, highest_bidder_id))
                if player_item:
                    cursor.execute("UPDATE bag SET quantity = quantity + ? WHERE owner_id = ? AND item_name = ?", (quantity, highest_bidder_id, item))
                else:
                    cursor.execute("INSERT INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (highest_bidder_id, item, quantity, item_type))

                # 發送拍賣結束的中文 Embed 訊息
                embed = discord.Embed(title="拍賣結束", description=f"{quantity} 個 {item} 的競標已結束！", color=0x00ffbf)
                embed.add_field(name="最高競標者", value=f"{highest_bidder.name} 以 {highest_bid} 的價格中標！", inline=False)
                embed.set_footer(text="我是ZU, 為您服務")
                await ctx.send(embed=embed)
            else:
                # 最高竞标者无效的情况下的处理
                embed = discord.Embed(title="拍賣結束", description=f"{quantity} 個 {item} 的競標已結束！", color=0x00ffbf)
                embed.add_field(name="最高競標者", value="未知", inline=False)
                embed.set_footer(text="我是ZU, 為您服務")
                await ctx.send(embed=embed)

            # 刪除拍賣記錄
            cursor.execute("DELETE FROM auction WHERE auction_id = ?", (auction_info[0],))
            conn.commit()
        else:
            # 没有找到拍卖记录的情况下的处理
            embed = discord.Embed(title="拍賣結束", description=f"{quantity} 個 {item} 的拍賣已結束，但未找到拍賣信息。", color=0xFF0000)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)

#============================================================================================================

@bot.command()
async def bid(ctx, seller: discord.User, item: str, bid_amount: int):
    bidder_id = str(ctx.author.id)
    seller_id = str(seller.id)
    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()

        # Check if the auction exists and is still active
        cursor.execute("""
            SELECT * FROM auction
            WHERE seller_id = ? AND item_name = ? AND end_time > ?
        """, (seller_id, item, int(time.time())))

        auction_info = cursor.fetchone()

        if auction_info:
            # Check if the bidder's balance is sufficient
            cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (bidder_id,))
            bidder_money = cursor.fetchone()[0]

            if bid_amount <= bidder_money:
                # Verify if the bid is at least 5% higher than the current highest bid
                minimum_bid = auction_info[7] * 1.05
                if bid_amount >= minimum_bid:
                    # Update the highest bidder and bid amount
                    cursor.execute("""
                        UPDATE auction
                        SET highest_bidder_id = ?, highest_bid = ?
                        WHERE auction_id = ?
                    """, (bidder_id, bid_amount, auction_info[0]))

                    # If the bid is in the last 5 minutes, update end_time
                    if auction_info[4] - int(time.time()) <= 300:
                        cursor.execute("""
                            UPDATE auction
                            SET end_time = end_time + 600
                            WHERE auction_id = ?
                        """, (auction_info[0],))

                    conn.commit()

                    # Send Chinese Embed message for successful bid
                    embed = discord.Embed(title="競標成功！", description=f"您以 {bid_amount} 的價格成功競標了來自 {seller.name} 的 {item} ！", color=0x00ffbf)
                    embed.set_footer(text="我是ZU, 為您服務")
                    await ctx.send(embed=embed)
                else:
                    # Send Chinese Embed message for bid not meeting minimum increment
                    embed = discord.Embed(title="競標失敗", description=f"您的出價必須至少是當前最高出價的5%。", color=0xFF0000)
                    embed.set_footer(text="我是ZU, 為您服務")
                    await ctx.send(embed=embed)
            else:
                # Send Chinese Embed message for insufficient balance
                embed = discord.Embed(title="競標失敗", description="您的帳戶餘額不足以支付此次出價。", color=0xFF0000)
                embed.set_footer(text="我是ZU, 為您服務")
                await ctx.send(embed=embed)
        else:
            # Send Chinese Embed message for invalid or ended auction
            embed = discord.Embed(title="無效的競標", description="無效的競標或競標已結束。", color=0x00ffbf)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)

@bot.command()
async def my_auctions(ctx):
    bidder_id = str(ctx.author.id)
    seller_id = str(ctx.author.id)

    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()

        # Get the items the user is currently bidding on
        cursor.execute("""
            SELECT * FROM auction
            WHERE highest_bidder_id = ? AND end_time > ?
        """, (bidder_id, int(time.time())))
        my_bids = cursor.fetchall()

        # Get the items the user has put up for auction
        cursor.execute("""
            SELECT * FROM auction
            WHERE seller_id = ? AND end_time > ?
        """, (seller_id, int(time.time())))
        my_auctions = cursor.fetchall()

        # Create an embed to display the information
        embed = discord.Embed(title="我的拍賣和競標清單", color=0x00ffbf)

        # Display items the user is currently bidding on
        if my_bids:
            for bid in my_bids:
                embed.add_field(
                    name=f"您競標的物品: {bid[2]}",
                    value=f"拍賣 ID: {bid[0]}\n最高出價: {bid[7]}",
                    inline=False
                )

        # Display items the user has put up for auction
        if my_auctions:
            for auction in my_auctions:
                embed.add_field(
                    name=f"您上架的物品: {auction[2]}",
                    value=f"拍賣 ID: {auction[0]}\n最高出價: {auction[7]}",
                    inline=False
                )

        # Send the embed
        await ctx.send(embed=embed)

@bot.command()
async def auction_info(ctx, item: str):
    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()

        # 檢索指定物品的拍賣信息
        cursor.execute("""
            SELECT * FROM auction
            WHERE item_name = ? AND end_time > ?
            ORDER BY highest_bid DESC
        """, (item, int(time.time())))

        auction_data = cursor.fetchall()

        if auction_data:
            # 創建一個嵌入式消息以顯示拍賣信息
            embed = discord.Embed(title=f"{item} 的拍賣信息", color=0x00ffbf)

            for auction_info in auction_data:
                highest_bidder_id = auction_info[5]
                highest_bid = auction_info[7]

                # 檢查用戶ID是否有效，然後再獲取用戶
                highest_bidder = None
                try:
                    highest_bidder = await bot.fetch_user(int(highest_bidder_id))
                except discord.errors.NotFound:
                    pass

                if highest_bidder:
                    embed.add_field(
                        name=f"當前最高出價: {highest_bid} 由 {highest_bidder.name} 提交",
                        value=f"結束時間: {dt.datetime.fromtimestamp(auction_info[4]).strftime('%Y-%m-%d %H:%M:%S')}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"當前最高出價: {highest_bid} 由未知用戶 ({highest_bidder_id}) 提交",
                        value=f"結束時間: {dt.datetime.fromtimestamp(auction_info[4]).strftime('%Y-%m-%d %H:%M:%S')}",
                        inline=False
                    )

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{item} 沒有正在進行中的拍賣。")


#副職業系統(種植;農夫)----------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def plant(ctx):
    # 檢查玩家是否已經是農夫
    player_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT satiation FROM player_info WHERE user_id = ?", (player_id, ))
        satiation = cursor.fetchone()
        cursor.execute("SELECT sub_job FROM player_info WHERE user_id = ?", (player_id, ))
        job = cursor.fetchone()
        cursor.execute("SELECT * FROM farmers WHERE player_id = ?", (player_id,))
        farmer = cursor.fetchone()
        if job[0] != '農夫':
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="您必須先成為農夫才能使用這個指令！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        if satiation[0] == 0:
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="你沒體力了！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return

        if farmer:
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="還有作物在農田裡 !", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return

        # 隨機選擇耕種時間
        planting_time = random.randint(0, 0.01)#3 8
        # 隨機選擇種植的作物
        items = ['蘋果', '馬鈴薯', '白菜']
        probabilities = [0.4, 0.4, 0.2]
        planted_item = random.choices(items, probabilities)[0]

        embed=discord.Embed(color=0x00ffbf)
        embed.add_field(name=f"耕種時間為 {planting_time} 分鐘，並種植了 {planted_item}！", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        cursor.execute("INSERT INTO farmers (player_id, planting_time) VALUES (?, ?)", (player_id, planting_time))
        conn.commit()

        # 等待種植完成
        await asyncio.sleep(planting_time * 60)

        # 收穫並放到 from 資料表
        cursor.execute("UPDATE farmers SET planting_time = planting_time - ?, planting_item = ? WHERE player_id = ?", (planting_time, planted_item, player_id))
        cursor.execute("UPDATE player_info SET satiation = satiation - ? WHERE user_id = ?", (2 , player_id))
        conn.commit()


        embed=discord.Embed(color=0x00ffbf)
        embed.add_field(name=f"您種植的 {planted_item} 已經成熟，輸入!harvest進行採收！", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        conn.close()
    except Exception as e:
        logger.error("種植指令出现异常：%s", e)
        await ctx.send("種植時發生了錯誤, 請聯繫管理員。")
#副職業系統(採收;農夫)----------------------------------------------------------------------------------------------------------------------------


@bot.command()
async def harvest(ctx):
    player_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT sub_job FROM player_info WHERE user_id = ?", (player_id, ))
        job = cursor.fetchone()
        quantity = random.randint(1, 5)
        if job[0] != '農夫':
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="您必須先成為農夫才能使用這個指令！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return

        cursor.execute("SELECT * FROM farmers WHERE player_id = ?", (player_id,))
        harvest_item = cursor.fetchone()

        if not harvest_item[1]:
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name=f"您目前沒有可以採收的作物。{harvest_item[0]} {harvest_item[1]} {harvest_item[2]} {harvest_item[3]}", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
        else:
        # 移除已採收的作物
            cursor.execute(f"SELECT item_name FROM bag WHERE owner_id = ?", (player_id,))
            player_item = cursor.fetchone()
            
            if not player_item:
                cursor.execute("INSERT INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (player_id, harvest_item[3], quantity, "材料"))
                cursor.execute("DELETE FROM farmers WHERE player_id = ?", (player_id,))
                conn.commit()

                embed=discord.Embed(color=0x00ffbf)
                embed.add_field(name=f"您成功採收了 {harvest_item[3]} x {quantity}！", value="", inline=False)
                embed.set_footer(text="我是ZU, 為您服務")
                await ctx.send(embed=embed)
            else:
                cursor.execute("UPDATE bag SET quantity = quantity + ? WHERE owner_id = ? AND item_name = ?", (quantity, player_id, harvest_item[3]))
                cursor.execute("DELETE FROM farmers WHERE player_id = ?", (player_id,))
                conn.commit()

                embed=discord.Embed(color=0x00ffbf)
                embed.add_field(name=f"您成功採收了 {harvest_item[3]} x {quantity}！", value="", inline=False)
                embed.set_footer(text="我是ZU, 為您服務")
                await ctx.send(embed=embed)
                conn.close()
    except Exception as e:
        logger.error("採收指令出现异常：%s", e)
        await ctx.send("採收時發生了錯誤, 請聯繫管理員。")


#副職業系統(料理;廚師)-------------------------------------------------------------------------------------------------------------------------


@bot.command()
async def cook(ctx, dish: str, quantity: int):
    player_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT sub_job FROM player_info WHERE user_id = ?", (player_id, ))
        job = cursor.fetchone()
        if job[0] != '廚師':
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="您必須先成為廚師才能使用這個指令！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        # 檢查玩家是否有足夠的材料
        required_ingredients = {
            '燉白菜': [('馬鈴薯', 1), ('白菜', 1), ('煤炭', 1)],
            '沙拉': [('蘋果', 1), ('馬鈴薯', 1), ('煤炭', 1)],
            '大雜燴': [('蘋果', 1), ('馬鈴薯', 1), ('白菜', 1), ('煤炭', 1)]
        }
        
        for ingredient, required_quantity in required_ingredients.get(dish, []):
            cursor.execute("SELECT quantity FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, ingredient))
            item_quantity = cursor.fetchone()
            if not item_quantity or item_quantity[0] < required_quantity * quantity:
                embed=discord.Embed(color=0x00ffbf)
                embed.add_field(name=f"製作 {dish} 所需材料不足。", value="", inline=False)
                embed.set_footer(text="我是ZU, 為您服務")
                await ctx.send(embed=embed)

                return
        
        # 製作料理
        cook_times = {
            '燉白菜': 1,
            '沙拉': 1,
            '大雜燴': 2
        }
        cook_time = cook_times.get(dish, 0)*quantity
    
        embed=discord.Embed(color=0x00ffbf)
        embed.add_field(name=f"開始製作 {dish} x {quantity}，請等待 {cook_time} 分鐘...", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        for ingredient, required_quantity in required_ingredients.get(dish, []):
            new_quantity = item_quantity[0] - required_quantity * quantity
            if new_quantity <= 0:
                cursor.execute("DELETE FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, ingredient))
            else:
                cursor.execute("UPDATE bag SET quantity = ? WHERE owner_id = ? AND item_name = ?", (new_quantity, player_id, ingredient))
            cursor.execute("UPDATE player_info SET satiation = satiation - ? WHERE user_id = ?", (1 , player_id))
            conn.commit()
        
        await asyncio.sleep(cook_time * 60)
        
        
        # 增加料理數量
        cursor.execute(f"SELECT item_name FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, dish))
        player_item = cursor.fetchone()
        if not player_item:
            cursor.execute("INSERT OR IGNORE INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (player_id, dish, quantity, "料理"))
        else:
            cursor.execute("UPDATE bag SET quantity = quantity + ? WHERE owner_id = ? AND item_name = ?", (quantity, player_id, dish))
            conn.commit()

        embed=discord.Embed(color=0x00ffbf)
        embed.add_field(name=f"成功製作了 {dish} x{quantity}。", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        conn.close()
    except Exception as e:
        logger.error("料理指令出现异常：%s", e)
        await ctx.send("料理時發生了錯誤, 請聯繫管理員。")


#副職業系統(挖礦;礦工)-------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def mine(ctx):
    player_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    try:
        # 檢查玩家是否已經在挖礦
        cursor.execute("SELECT satiation FROM player_info WHERE user_id = ?", (player_id, ))
        satiation = cursor.fetchone()
        cursor.execute("SELECT * FROM farmers WHERE player_id = ?", (player_id,))
        miner = cursor.fetchone()
        cursor.execute("SELECT * FROM player_info WHERE user_id = ?", (player_id,))
        player_job = cursor.fetchone()
        if player_job[2] != '礦工':
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="您必須先成為礦工才能使用這個指令！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        if satiation[0] == 0:
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="你沒體力了！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return

        if miner:
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="您正在挖礦中！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        
        # 隨機挖礦時間 (5~10 分鐘)
        mining_time = random.randint(1, 15)
        embed=discord.Embed(color=0x00ffbf)
        embed.add_field(name=f"您開始挖礦，需要 {mining_time} 分鐘的時間。", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)
        
        # 建立挖礦資料
        cursor.execute("INSERT INTO farmers (player_id, planting_time) VALUES (?, ?)", (player_id, mining_time))
        conn.commit()
        conn.close()  # 关闭连接
        
        # 等待挖礦完成
        await asyncio.sleep(mining_time * 60)
        
        # 根據機率獲得獎勵
        rewards = [
            ("煤炭", 30),
            ("1階裝備經驗石", 20),
            ("1階附魔石", 20),
            ("2階裝備經驗石", 10),
            ("2階附魔石", 10),
            ("3階裝備經驗石", 5),
            ("3階附魔石", 5)
        ]
        
        reward = random.choices([item[0] for item in rewards], [item[1] for item in rewards], k=1)[0]
        
        # 將獎勵放入背包
        conn = sqlite3.connect(Database)  # 重新连接数据库
        cursor = conn.cursor()
        cursor.execute(f"SELECT item_name FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, reward))
        player_item = cursor.fetchone()
        cursor.execute("DELETE FROM farmers WHERE player_id = ?", (player_id,))
        
        if not player_item:
            cursor.execute("INSERT INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (player_id, reward, 1, "材料"))
            cursor.execute("UPDATE player_info SET satiation = satiation - 2 WHERE user_id = ?", (player_id,))  # 添加缺失的参数
            conn.commit()
            conn.close()

            embed=discord.Embed(color=0x00ff9d)
            embed.add_field(name=f"您完成挖礦，獲得了 {reward} 放入您的背包中！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
        else:
            cursor.execute("UPDATE bag SET quantity = quantity + 1 WHERE owner_id = ? AND item_name = ?", (player_id, reward))
            cursor.execute("UPDATE player_info SET satiation = satiation - 1 WHERE user_id = ?", (player_id,))  # 添加缺失的参数
            conn.commit()
            conn.close()

            embed=discord.Embed(color=0x00ff9d)
            embed.add_field(name=f"您完成挖礦，獲得了 {reward} 放入您的背包中！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
    except Exception as e:
        logger.error("挖礦指令出现异常：%s", e)
        await ctx.send("挖礦時發生了錯誤, 請聯繫管理員。")

#副職業系統(強化;匠人)---------------------------------------------------------------------------------------------------------------------------
        
# 計算強化後的裝備屬性
def calculate_enhanced_stats(original_stats, enhanced_level):
    enhanced_stats = copy.deepcopy(original_stats)
    # 在這裡添加考慮強化等級的邏輯，例如根據強化等級提高攻擊力、防禦力等
    enhanced_stats["attack"] += 2 * enhanced_level
    enhanced_stats["defense"] += 2 * enhanced_level
    enhanced_stats["level"] += enhanced_level
    enhanced_stats["enhanced"] = True
    
    # 考慮Rarity
    rarity_mapping = {"D": 0, "C": 1, "B": 2, "A": 3, "S": 4}
    current_rarity_index = rarity_mapping.get(enhanced_stats.get("Rarity", "D"), 0)
    enhanced_rarity_index = min(current_rarity_index + enhanced_level, len(rarity_mapping) - 1)
    enhanced_stats["Rarity"] = next((rarity for rarity, index in rarity_mapping.items() if index == enhanced_rarity_index), "D")
    
    return enhanced_stats

# 檢查匠人是否同意強化
async def craftsman_approves(ctx, craftsman, materials, equipment_name, price):
    # 在這裡加入檢查匠人是否同意的邏輯
    # 這裡的示例總是返回 True，表示匠人同意強化
    embed = discord.Embed(title=f"強化委託 - {craftsman}", color=0x00ff00)
    embed.add_field(name="被強化裝備", value=f"{equipment_name}", inline=False)
    embed.add_field(name="所需材料", value=', '.join([f"{quantity} x {material}" for material, quantity in materials.items()]), inline=False)
    embed.add_field(name="價格", value=f"{price} 元", inline=False)
    embed.set_footer(text=f"{ctx.author.name} 發起了強化委託")

    confirm_embed = discord.Embed(title=f"確定要委託 {craftsman} 強化 {equipment_name} 嗎？", color=0x00ff00)
    confirm_embed.add_field(name="所需材料", value=', '.join([f"{quantity} x {material}" for material, quantity in materials.items()]), inline=False)
    confirm_embed.add_field(name="價格", value=f"{price} 元", inline=False)
    confirm_embed.add_field(name="請輸入 yes 確認委託，或輸入 no 取消。", value="", inline=True)
    confirm_embed.set_footer(text="我是ZU, 為您服務")
    
    # 發送確認消息
    await ctx.send(embed=confirm_embed)

    # 等待確認消息
    def check(msg):
        return msg.author == ctx.author and msg.content.lower() in ['yes', 'no']

    try:
        reply = await bot.wait_for('message', timeout=180.0, check=check)

        if reply.content.lower() == 'yes':
            # 如果玩家確認委託，發送委託成功消息
            await ctx.send(embed=embed)
            return True
        else:
            # 如果玩家取消委託，發送取消消息
            await ctx.send("委託取消。")
            return False
    except asyncio.TimeoutError:
        # 如果等待超時，發送委託取消消息
        await ctx.send("委託確認逾時，委託取消。")
        return False
    
# 匠人同意後的處理邏輯
def handle_craftsman_approval(user_id, equipment_type, equipment_name, enhanced_level):
    # 獲取原始裝備設計
    original_equipment = equipment_designs[equipment_type][equipment_name]

    # 計算強化後的裝備屬性
    enhanced_stats = calculate_enhanced_stats(original_equipment, enhanced_level)

    # 在這裡添加其他處理邏輯
    # 例如，更新裝備狀態、記錄強化記錄等

    # 更新玩家的裝備狀態
    cursor.execute("UPDATE player_info SET enhanced_equipment = ?, enhanced_level = ? WHERE user_id = ?",
                   (equipment_name, enhanced_level, user_id))

    # 記錄強化記錄
    cursor.execute("INSERT INTO enhancement_records (user_id, equipment_type, equipment_name, enhanced_level) VALUES (?, ?, ?, ?)",
                   (user_id, equipment_type, equipment_name, enhanced_level))

    # 將強化後的裝備放入玩家的背包
    cursor.execute("INSERT INTO bag (owner_id, item_name, quantity, item_type, item_properties) VALUES (?, ?, ?, ?, ?)",
                   (user_id, equipment_name, 1, equipment_type, json.dumps(enhanced_stats)))

# 設定 bot 指令
@bot.command(name='aggrandizement')
async def aggrandizement_command(ctx, craftsman: str, equipment_type: str, equipment_name: str, price: int):
    user_id = ctx.author.id

    cursor.execute("SELECT sub_job FROM player_info WHERE user_id = ?", (user_id, ))
    job = cursor.fetchone()
    if job[0] != '匠人':
        await ctx.send("找不到指定的匠人！")
        return

    # 檢查裝備是否存在
    if equipment_type not in equipment_designs:
        await ctx.send("找不到指定的裝備類型！")
        return

    if equipment_name not in equipment_designs[equipment_type]:
        await ctx.send("找不到指定的裝備！")
        return

    # 檢查價格是否合法
    if price <= 0:
        await ctx.send("請輸入有效的價格！")
        return

    # 檢查玩家是否擁有足夠金錢
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (user_id,))
    player_money = cursor.fetchone()[0]

    if player_money < price:
        await ctx.send("您的金錢不足以支付這項強化服務！")
        return

    # 檢查匠人是否同意強化
    materials_needed = [("1階裝備經驗石",), ("1階附魔石",), ("2階裝備經驗石",), ("2階附魔石",), ("3階裝備經驗石",), ("3階附魔石",)]
    materials_required = {material: quantity for quantity, material in enumerate(materials_needed, start=1)}
    approval = await craftsman_approves(ctx, craftsman, materials_required, equipment_name, price)

    if approval:
        # 扣除金錢
        cursor.execute("UPDATE player_info SET money = money - ? WHERE user_id = ?", (price, user_id))

        # 更新裝備屬性
        enhanced_level = 1  # 假設每次強化增加1級
        handle_craftsman_approval(user_id, equipment_type, equipment_name, enhanced_level)

        await ctx.send(f"您成功發起了強化委託，花了 {price} 元！")
    else:
        await ctx.send("委託被取消。")
    cursor.execute("UPDATE player_info SET satiation = satiation - ? WHERE user_id = ?", (1 , user_id))
    conn.commit()
    conn.close()

#副職業系統(採藥;採藥人)-------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def collect(ctx):
    player_id = str(ctx.author.id)
    
    try:
        conn = sqlite3.connect(Database)
        cursor = conn.cursor()
        
        # 檢查玩家是否已經在採藥
        cursor.execute("SELECT satiation FROM player_info WHERE user_id = ?", (player_id,))
        satiation = cursor.fetchone()
        
        cursor.execute("SELECT * FROM farmers WHERE player_id = ?", (player_id,))
        collector = cursor.fetchone()
        
        cursor.execute("SELECT * FROM player_info WHERE user_id = ?", (player_id,))
        player_job = cursor.fetchone()
        
        if player_job[2] != '採藥人':
            embed = discord.Embed(color=0x00ffbf)
            embed.add_field(name="您必須先成為採藥人才能使用這個指令！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        
        if satiation[0] == 0:
            embed = discord.Embed(color=0x00ffbf)
            embed.add_field(name="你沒體力了！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        
        if collector:
            embed = discord.Embed(color=0x00ffbf)
            embed.add_field(name="您正在採藥中，請稍後再試！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        
        # 隨機採藥時間 (1~3 分鐘)
        collection_time = random.randint(1, 3)
        embed = discord.Embed(color=0x00ffbf)
        embed.add_field(name=f"您開始採藥，需要 {collection_time} 分鐘的時間。", value="", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)

        # 建立採藥資料
        cursor.execute("INSERT INTO farmers (player_id, planting_time) VALUES (?, ?)", (player_id, collection_time))
        conn.commit()
        conn.close()
        
        await asyncio.sleep(collection_time * 60)  # 等待採藥完成

        conn = sqlite3.connect(Database)
        cursor = conn.cursor()
        
        # 根據機率獲得藥材
        herbs = [
            ("人參", 20),
            ("長生草", 40),
            ("能量花", 40)
        ]
        
        herb = random.choices([item[0] for item in herbs], [item[1] for item in herbs], k=1)[0]
        
        # 將藥材放入背包
        cursor.execute("SELECT item_name FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, herb))
        player_item = cursor.fetchone()
        cursor.execute("DELETE FROM farmers WHERE player_id = ?", (player_id,))
        
        if not player_item:
            cursor.execute("INSERT INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (player_id, herb, 1, "材料"))
            cursor.execute("UPDATE player_info SET satiation = satiation - 2 WHERE user_id = ?", (player_id,))
            conn.commit()
            conn.close()

            embed = discord.Embed(color=0x00ff9d)
            embed.add_field(name=f"您完成採藥，獲得了 {herb} 放入您的背包中！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
        else:
            cursor.execute("UPDATE bag SET quantity = quantity + 1 WHERE owner_id = ? AND item_name = ?", (player_id, herb))
            cursor.execute("UPDATE player_info SET satiation = satiation - 2 WHERE user_id = ?", (player_id,))
            conn.commit()
            conn.close()

            embed = discord.Embed(color=0x00ff9d)
            embed.add_field(name=f"您完成採藥，獲得了 {herb} 放入您的背包中！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
    except Exception as e:
        logger.error("採藥指令出现异常：%s", e)
        await ctx.send("採藥時發生了錯誤, 請聯繫管理員。")


#-------------------------------------------------------------------------------------------------------------------


@bot.command()
async def brew(ctx, potion_name: str, quantity: int):
    player_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM player_info WHERE user_id = ?", (player_id,))
        player_job = cursor.fetchone()
        if player_job[2] != '藥劑師':
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name="您必須先成為藥劑師才能使用這個指令！", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            return
        # 檢查玩家是否有足夠的材料
        required_ingredients = {
            '人參湯': [('人參', 1), ('煤炭', 1)],
            '雙回復藥水': [('長生草', 1), ('能量花', 1)],
            '治療藥水': [('長生草', 1)],
            '回魔藥水': [('能量花', 1)]
        }
        
        for ingredient, required_quantity in required_ingredients.get(potion_name, []):
            cursor.execute("SELECT quantity FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, ingredient))
            item_quantity = cursor.fetchone()
            if not item_quantity or item_quantity[0] < required_quantity * quantity:
                embed=discord.Embed(color=0x00ffbf)
                embed.add_field(name=f"製作 {potion_name} 所需材料不足。", value="", inline=False)
                embed.set_footer(text="我是ZU, 為您服務")
                await ctx.send(embed=embed)
                return
        
        # 製作藥水
        success_rates = {
            '人參湯': 0.7,
            '雙回復藥水': 0.7,
            '治療藥水': 0.9,
            '回魔藥水': 0.9
        }
        success_rate = success_rates.get(potion_name, 0)
        
        if random.random() < success_rate:
            for ingredient, required_quantity in required_ingredients.get(potion_name, []):
                new_quantity = item_quantity[0] - required_quantity * quantity
                if new_quantity <= 0:
                    cursor.execute("DELETE FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, ingredient))
                else:
                    cursor.execute("UPDATE bag SET quantity = ? WHERE owner_id = ? AND item_name = ?", (new_quantity, player_id, ingredient))
            # 增加藥水數量
            cursor.execute(f"SELECT item_name FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, potion_name))
            player_item = cursor.fetchone()
            if not player_item[0]:
                cursor.execute("INSERT OR IGNORE INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (player_id, potion_name, quantity, "藥水"))
            else:
                cursor.execute("UPDATE bag SET quantity = quantity + ? WHERE owner_id = ? AND item_name = ?", (quantity, player_id, potion_name))
                cursor.execute("UPDATE player_info SET satiation = satiation - ? WHERE user_id = ?", (1 , player_id))
            conn.commit()
            conn.close()

            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name=f"成功製作了 {potion_name} x{quantity}。", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
        else:
            for ingredient, required_quantity in required_ingredients.get(potion_name, []):
                new_quantity = item_quantity[0] - required_quantity * quantity
                if new_quantity <= 0:
                    cursor.execute("DELETE FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, ingredient))
                else:
                    cursor.execute("UPDATE bag SET quantity =  ? WHERE owner_id = ? AND item_name = ?", (new_quantity, player_id, ingredient))
                    cursor.execute("UPDATE player_info SET satiation = satiation - ? WHERE user_id = ?", (1 , player_id))
            conn.commit()
            conn.close()
            embed=discord.Embed(color=0x00ffbf)
            embed.add_field(name=f"製作 {potion_name} 失敗，材料已扣除。", value="", inline=False)
            embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=embed)
            
    except Exception as e:
        logger.error("製藥指令出现异常：%s", e)
        await ctx.send("製藥時發生了錯誤, 請聯繫管理員。")
    finally:
        conn.close()

#-----------------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def eat(ctx, food_name: str, quantity: int):
    player_id = str(ctx.author.id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    try:
        # 检查玩家是否有该食物
        cursor.execute("SELECT * FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, food_name))
        food = cursor.fetchone()
        if not food:
            await ctx.send(f"您的背包中没有 {food_name}。")
            return

        # 更新食物数量
        new_quantity = food[1] - quantity
        if new_quantity <= 0:
            cursor.execute("DELETE FROM bag WHERE owner_id = ? AND item_name = ?", (player_id, food_name))
        else:
            cursor.execute("UPDATE bag SET quantity = quantity - ? WHERE owner_id = ? AND item_name = ?", (quantity, player_id, food_name))
        conn.commit()

        # 增加饱食度
        food_satiation = {
            "燉白菜": 2,
            "沙拉": 2,
            "大雜燴": 4
        }
        increase_satiation = food_satiation.get(food_name, 0)

        # 获取玩家当前饱食度并增加
        cursor.execute("SELECT satiation FROM player_info WHERE player_id = ?", (player_id,))
        current_satiation = cursor.fetchone()
        if current_satiation[0] is None:
            cursor.execute("UPDATE player_info SET satiation = ? WHERE player_id = ?", (20 , player_id))
            return
        new_satiation = current_satiation + increase_satiation*quantity
        if new_satiation > 20:
            await ctx.send(f"你已經很飽了, 飽食度為{current_satiation}不能再吃了")
            return
        # 更新玩家的饱食度
        cursor.execute("UPDATE player_info SET satiation = ? WHERE player_id = ?", (new_satiation, player_id))
        conn.commit()
        conn.close()
        await ctx.send(f"您吃了 {food_name} x {quantity}，增加了 {increase_satiation*quantity} 点饱食度。")
    except Exception as e:
        logger.error("進食指令出现异常：%s", e)
        await ctx.send("進食時發生了錯誤, 請聯繫管理員。")



#=====================================================================================================================================



# 裝備設計
equipment_designs = {
    "weapons": {"新手大劍": {"attack": 5, "main_job": "戰士"},
                "新手短劍": {"attack": 10, "main_job": "刺客"},
                "新手長弓": {"attack": 10, "main_job": "射手"},
                "新手法杖": {"attack": 7, "main_job": "法師"}},

    "helmet": {"新手頭盔": {"defense": 5}},

    "armor": {"新手胸甲":{"defense": 10}},

    "pant": {"新手褲子":{"defense": 8}},

    "shoe": {"新手鞋子":{"defense": 4}},

    "Jewelry": {"新手戒指":{"attack": 5, "defense": 5}},

    "skill_1":{"護甲" : {"main_job": "戰士", "Mp": "30"},
             "突刺": {"main_job": "刺客", "Mp": "30"},
             "隱身": {"main_job": "刺客", "Mp": "20"},
             "血刃": {"main_job": "刺客", "Mp": "35"},
             "箭裂": {"main_job": "射手", "Mp": "30"},
             "火球術": {"main_job": "法師", "Mp": "25"}}

}

# 穿上裝備==============================================================================================================================================

@bot.command()
async def equip(ctx, *, equipment_with_id: str):
    user_id = ctx.author.id
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    # 解析裝備名稱和唯一 ID
    equipment_name, unique_id = equipment_with_id.rsplit('_', 1)

    # 檢查裝備是否存在並且符合玩家主要職業
    cursor.execute("SELECT * FROM equip_bag WHERE owner_id = ? AND item_name = ? AND equipment_id = ?", (user_id, equipment_name, unique_id))
    equipment_data = cursor.fetchone()

    if equipment_data is None:
        await ctx.send("您沒有這件裝備")
        conn.close()
        return

    equipped_equipment_type = equipment_data[2]
    allowed_main_job = equipment_data[6]

    if allowed_main_job and allowed_main_job != "all":
        cursor.execute("SELECT main_job FROM player_info WHERE user_id = ?", (user_id,))
        main_job = cursor.fetchone()[0]
        if main_job != allowed_main_job:
            await ctx.send(f"您的職業無法裝備這件裝備")
            conn.close()
            return

    # 檢查裝備是否能夠裝備在玩家當前欄位
    cursor.execute(f"SELECT item_type FROM equip_bag WHERE owner_id = ? AND item_type = ? AND equipped = 1", (user_id, equipped_equipment_type))
    player_equipment = cursor.fetchone()
    cursor.execute(f"SELECT equipment_id FROM equip_bag WHERE owner_id = ? AND item_type = ? AND equipped = 1", (user_id, equipped_equipment_type))
    equipment_id = cursor.fetchone()
    # 如果玩家已經穿戴了裝備，將其放回背包並扣除相應屬性
    if player_equipment:
        # 取得已穿戴裝備的屬性值
        cursor.execute("SELECT * FROM equip_bag WHERE owner_id = ? AND item_type = ? AND equipment_id = ?", (user_id, equipped_equipment_type, equipment_id[0]))
        unequipped_equipment_data = cursor.fetchone()

        # 將裝備放回背包
        cursor.execute("UPDATE equip_bag SET equipped = 0 WHERE owner_id = ? AND item_type = ? AND equipment_id = ?", (user_id, equipped_equipment_type, equipment_id[0]))
        print(unequipped_equipment_data[5], unequipped_equipment_data[7], unequipped_equipment_data[8], unequipped_equipment_data[9])
        # 扣除穿戴裝備帶有的數值
        cursor.execute("UPDATE player_info SET attack = attack - ?, defense = defense - ?, HP = HP - ?, MP = MP - ? WHERE user_id = ?",
                       (unequipped_equipment_data[5], unequipped_equipment_data[7], unequipped_equipment_data[8], unequipped_equipment_data[9], user_id))

    # 更新玩家裝備欄位
    cursor.execute(f"UPDATE equip_bag SET equipped = 1 WHERE owner_id = ? AND item_name = ? AND equipment_id = ?", (user_id, equipment_name, unique_id))
    print(equipment_data[5], equipment_data[7], equipment_data[8], equipment_data[9])
    # 更新玩家屬性
    cursor.execute("UPDATE player_info SET attack = attack + ?, defense = defense + ?, HP = HP + ?, MP = MP + ? WHERE user_id = ?",
                   (equipment_data[5], equipment_data[7], equipment_data[8], equipment_data[9], user_id))

    await ctx.send(f"已裝備 {equipment_name} 於 {equipped_equipment_type} 欄位")

    conn.commit()
    conn.close()

#卸下裝備---------------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def unequip(ctx, *, equipment: str):
    user_id = ctx.author.id
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    # 檢查裝備是否存在並且符合玩家主要職業
    cursor.execute("SELECT * FROM equip_bag WHERE owner_id = ? AND item_name = ? AND equipped = 1", (user_id, equipment))
    equipment_data = cursor.fetchone()

    if equipment_data is None:
        await ctx.send("您沒有裝備這件裝備")
        conn.close()
        return
    
   
    cursor.execute("UPDATE player_info SET attack = attack - ?, defense = defense - ?, max_HP = max_HP - ?, max_MP = max_MP - ? WHERE user_id = ?",
                   (equipment_data[5], equipment_data[7], equipment_data[8], equipment_data[9], user_id))

    
    cursor.execute("UPDATE equip_bag SET equipped = 0 WHERE owner_id = ? AND item_name = ?", (user_id, equipment))
    cursor.execute("UPDATE bag SET quantity = quantity + 1 WHERE owner_id = ? AND item_name = ?", (user_id, equipment))

    await ctx.send(f"已卸下 {equipment}")

    conn.commit()
    conn.close()


#查看裝備---------------------------------------------------------------------------------------------------------------------------------

@bot.command()
async def equipment(ctx):
    user_id = ctx.author.id
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    try:
     
        cursor.execute(f"SELECT item_name, item_type, equipped FROM equip_bag WHERE owner_id = ?", (user_id,))
        equipped_equipment = cursor.fetchall()

    
        formatted_equipment = []
        for equipment in equipped_equipment:
            if equipment[2] == 1:
                formatted_equipment.append(f"{equipment[1]}: {equipment[0]} (已穿戴)")
            else:
                formatted_equipment.append(f"{equipment[1]}: {equipment[0]}")


        embed = discord.Embed(title="您的裝備：", color=0x00ff9d)
        embed.add_field(name="裝備欄位", value="\n".join(formatted_equipment) or "無裝備", inline=False)
        embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=embed)

    except Exception as e:
        logger.error("查看裝備指令出现异常：%s", e)
        await ctx.send("查看裝備時發生了錯誤, 請聯繫管理員。")
    finally:
        conn.close()



#公會系統---------------------------------------------------------------------------------------------------------------------------------
        




def get_user_guild_id(user_id):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    cursor.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_user_name(user_id):
    user = bot.get_user(user_id)
    return user.name if user else "未知用戶"


@bot.command()
async def build_guild(ctx, Guild_Name: str):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    user_id = ctx.author.id
    required_money = 0


    cursor.execute("SELECT guild_id FROM guilds WHERE guild_name = ?", (Guild_Name,))
    existing_guild = cursor.fetchone()

    if existing_guild:
        conn.close()
        await ctx.send("該公會名已被使用，請選擇其他名稱。")
        return

    cursor.execute("SELECT money FROM player_info WHERE user_id = ?", (user_id,))
    user_money = cursor.fetchone()[0]

    if user_money >= required_money:
        cursor.execute("UPDATE player_info SET money = money - ? WHERE user_id = ?", (required_money, user_id))
        conn.commit()

        cursor.execute("INSERT INTO guilds (guild_name, guild_leader_id) VALUES (?, ?)", (Guild_Name, user_id))
        conn.commit()

        guild_id = cursor.lastrowid
        cursor.execute("INSERT INTO guild_members (user_id, guild_id, position) VALUES (?, ?, ?)", (user_id, guild_id, "公會長"))
        conn.commit()

      
        cursor.execute("UPDATE player_info SET guild_id = ?, position = ? WHERE user_id = ?", (guild_id, "公會長", user_id))
        conn.commit()

        conn.close()
        await ctx.send(f"您成功創建了 {Guild_Name} 公會，花費了 {required_money} 金錢。")
    else:
        conn.close()
        await ctx.send("您的金錢不足，無法創建公會。")




@bot.command()
async def search_guilds(ctx):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    cursor.execute("SELECT guild_name, guild_leader_id FROM guilds")
    guilds = cursor.fetchall()

    if guilds:
        sampled_guilds = random.sample(guilds, min(5, len(guilds)))
        guild_info = "\n".join([f"{guild_name} - 工會長: {get_user_name(guild_leader_id)}" for guild_name, guild_leader_id in sampled_guilds])
        await ctx.send(f"隨機五個公會信息：\n{guild_info}")
    else:
        await ctx.send("目前還沒有任何公會。")



@bot.command()
async def join_guild(ctx, guild_name: str):
    try:
        conn = sqlite3.connect(Database)
        cursor = conn.cursor()
        user_id = ctx.author.id

        
        cursor.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        existing_guild = cursor.fetchone()

        if existing_guild:
            await ctx.send("您已經加入了一個公會，無法加入新的公會。")
            return

      
        cursor.execute("SELECT guild_id, approval_required, minimum_level FROM guilds WHERE guild_name = ?", (guild_name,))
        guild_info = cursor.fetchone()

        if not guild_info:
            await ctx.send(f"名為 '{guild_name}' 的公會不存在。")
            return

        guild_id, approval_required, minimum_level = guild_info

      
        if approval_required:
            await ctx.send("您已提交加入申請，請等待公會審核。")

            cursor.execute("INSERT INTO guild_applications (user_id, guild_id) VALUES (?, ?)", (user_id, guild_id))
            conn.commit()
        else:
            if minimum_level:
                cursor.execute("SELECT level FROM user_info WHERE user_id = ?", (user_id,))
                user_level = cursor.fetchone()[0]

                if user_level < minimum_level:
                    await ctx.send(f"您的等級不足 {minimum_level} 級，無法加入該公會。")
                    return


            cursor.execute("INSERT INTO guild_members (user_id, guild_id, position) VALUES (?, ?, ?)", (user_id, guild_id, "成員"))
            conn.commit()
            await ctx.send(f"您成功加入了 {guild_name} 公會！")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        await ctx.send("加入公會時發生錯誤。請稍後再試，或聯繫管理員。")

    finally:
        conn.close()



@bot.command()
async def guild(ctx):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    user_id = ctx.author.id
    cursor.execute("SELECT guild_id, position FROM guild_members WHERE user_id = ?", (user_id,))
    guild_info = cursor.fetchone()

    if guild_info:
        guild_id, position = guild_info
        cursor.execute("SELECT guild_name FROM guilds WHERE guild_id = ?", (guild_id,))
        guild_name = cursor.fetchone()[0]

        await ctx.send(f"您所在的公會信息：\n公會名稱: {guild_name}\n職位: {position}")
    else:
        await ctx.send("您尚未加入任何公會。")
        conn.commit()
        conn.close()

@bot.command()
async def guild_members(ctx):

        conn = sqlite3.connect(Database)
        cursor = conn.cursor()


        user_id = ctx.author.id
        cursor.execute("SELECT guild_id FROM guild_members WHERE user_id = ?", (user_id,))
        guild_info = cursor.fetchone()

        if guild_info:
            guild_id = guild_info[0]


            cursor.execute("SELECT guild_name FROM guilds WHERE guild_id = ?", (guild_id,))
            guild_name = cursor.fetchone()[0]

            # 獲取所有公會成員信息
            cursor.execute("SELECT player_info.user_id, player_info.user_id, player_info.level, player_info.main_job, guild_members.position FROM player_info JOIN guild_members ON player_info.user_id = guild_members.user_id WHERE guild_members.guild_id = ?", (guild_id,))
            all_members = cursor.fetchall()

            if all_members:
                # 生成所有成員信息的字符串
                member_info = "\n".join([f"{get_user_name(username)} (Level {level} {job}) : {position}" for user_id, username, level, job, position in all_members])
                await ctx.send(f"公會 '{guild_name}' 所有成員信息：\n{member_info}")
            else:
                await ctx.send("公會中尚無成員。")
        else:
            await ctx.send("您尚未加入任何公會。")

# 指令：任命職位
@bot.command()
async def appoint_officer(ctx, target_member: discord.Member, position: str):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    user_id = ctx.author.id
    guild_id = get_user_guild_id(user_id)

    cursor.execute("SELECT position FROM guild_members WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
    leader_position = cursor.fetchone()[0]

    if leader_position != "公會長":
        await ctx.send("您不是公會長，無法任命成員。")
        return

    valid_positions = ["副會長", "外交官", "成員"]
    if position.lower() not in valid_positions:
        await ctx.send("請提供有效的職位，如 '副會長'、'外交官' 或 '成員'。")
        return

    cursor.execute("UPDATE guild_members SET position = ? WHERE user_id = ? AND guild_id = ?", (position, target_member.id, guild_id))
    conn.commit()

    await ctx.send(f"{target_member.display_name} 已被任命為 {position}。")
    conn.commit()
    conn.close()

# 指令：審核加入申請
@bot.command()
async def approve_member(ctx, target_member: discord.Member, decision: str):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    user_id = ctx.author.id
    guild_id = get_user_guild_id(user_id)

    cursor.execute("SELECT position FROM guild_members WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
    leader_position = cursor.fetchone()[0]

    if leader_position not in ["公會長", "副會長"]:
        await ctx.send("您不是公會長或副會長，無法批准或拒絕成員的加入申請。")
        return

    if decision.lower() == "approve":
        cursor.execute("INSERT INTO guild_members (user_id, guild_id, position) VALUES (?, ?, ?)", (target_member.id, guild_id, "member"))
        conn.commit()
        await ctx.send(f"{target_member.display_name} 成功被批准加入公會！")
    elif decision.lower() == "reject":
        # 這裡可以添加額外的拒絕邏輯，例如發送一條消息給被拒絕的成員
        await ctx.send(f"{target_member.display_name} 的加入申請已被拒絕。")
    else:
        await ctx.send("請提供有效的決定，如 'approve' 或 'reject'。")
        conn.commit()
        conn.close()


#戰鬥系統---------------------------------------------------------------------------------------------------------------------------------

# 定義玩家技能效果
player_skills = {
    "護甲": {"type": "增益", "target": "單體", "duration": "非持續", "defense": 10, "MP": 25},
    "突刺": {"type": "傷害", "target": "單體", "duration": "非持續", "damage": 10, "MP": 25},
    "箭裂": {"type": "傷害", "target": "群體", "duration": "非持續", "double_damage": True, "MP": 25},
    "火球術": {"type": "傷害", "target": "單體", "duration": "非持續", "damage": 0, "fire_dot": 5, "dot_duration": 3, "MP": 20},
    "治療術": {"type": "增益", "target": "單體", "duration": "非持續", "heal": 15, "MP": 15},
    "冰凍術": {"type": "控制", "target": "單體", "duration": "非持續", "freeze": True, "MP": 30},
    "群體治癒": {"type": "增益", "target": "群體", "duration": "非持續", "heal": 10, "MP": 20},
    "燃燒": {"type": "傷害", "target": "單體", "duration": "持續", "damage": 5, "dot_duration": 2, "MP": 15}
}

potion_effects = {
    "人參湯": {"HP": 20, "MP": 0},
    "雙回復藥水": {"HP": 10, "MP": 10},
    "回復藥水": {"HP": 10, "MP": 0},
    "回魔藥水": {"HP": 0, "MP": 10}
}

def calculate_damage(ctx, player_data, monster_stats, round, skill_effect=None):
    # 计算基本攻击力
    physical_attack = player_data["attack"] * player_data["strength"]
    magical_attack = player_data["attack"] * player_data["intelligence"]

    if skill_effect is not None:
        # 根据技能类型应用不同的效果
        if skill_effect["type"] == "增益":
            apply_buff(ctx, player_data, skill_effect)
        elif skill_effect["type"] == "傷害":
            apply_damage(ctx, player_data, monster_stats, skill_effect)

    monster_physical_defense = monster_stats["strength"] * monster_stats["defense"]
    monster_magical_defense = monster_stats["intelligence"] * monster_stats["defense"]
    
    # 计算实际伤害
    physical_damage = max(0, physical_attack - monster_physical_defense)
    magical_damage = max(0, magical_attack - monster_magical_defense)

    total_damage = physical_damage + magical_damage

    return total_damage / 10  # 返回整数伤害值

def apply_damage(ctx, player_data, monster_stats, skill_effect):
    # 计算基本攻击力
    physical_attack = player_data["attack"] * player_data["strength"]
    magical_attack = player_data["attack"] * player_data["intelligence"]

    # 计算技能效果的额外伤害
    if "damage" in skill_effect:
        physical_attack += skill_effect["damage"]
        magical_attack += skill_effect["damage"]

    # 计算实际伤害
    monster_physical_defense = monster_stats["strength"] * monster_stats["defense"]
    monster_magical_defense = monster_stats["intelligence"] * monster_stats["defense"]

    physical_damage = max(0, physical_attack - monster_physical_defense)
    magical_damage = max(0, magical_attack - monster_magical_defense)

    total_damage = physical_damage + magical_damage

    if skill_effect.get("double_damage", False):
        total_damage *= 2

    return total_damage

def apply_buff(player_data, skill_effect):

    # 根據技能效果增益的屬性進行修改
    if "attack" in skill_effect:
        player_data["attack"] += skill_effect["attack"]  # 增加攻擊力

    if "defense" in skill_effect:
        player_data["defense"] += skill_effect["defense"]  # 增加防禦力

    if "strength" in skill_effect:
        player_data["strength"] += skill_effect["strength"]  # 增加力量

    if "intelligence" in skill_effect:
        player_data["intelligence"] += skill_effect["intelligence"]  # 增加智力     

    if "heal" in skill_effect:
        player_data["HP"] += skill_effect["heal"]  # 恢復生命值

    return 0

def anthor_damage(ctx, monster_stats, player_data):
    monster_strength = monster_stats["strength"]
    monster_intelligence = monster_stats["intelligence"]
    monster_attack = monster_stats["attack"]

    monster_physical_attack = monster_strength * monster_attack
    monster_magical_attack = monster_intelligence * monster_attack

    player_physical_defense = player_data["strength"] * player_data["defense"]
    player_magical_defense = player_data["intelligence"] * player_data["defense"]

    physical_damage = max(0, monster_physical_attack - player_physical_defense)
    magical_damage = max(0, monster_magical_attack - player_magical_defense)

    total_damage = physical_damage + magical_damage

    return total_damage

async def battle(ctx, monster_stats):
    user_id = ctx.author.id
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    money = 1000  # Initialize money to a default value
    cursor.execute("SELECT * FROM player_info WHERE user_id = ?", (user_id,))
    player_stats = cursor.fetchone()

    player_available_skills = []
    cursor.execute("SELECT skill_1, skill_2, skill_3 FROM equipment WHERE player_id = ?", (user_id,))
    player_skills_list = cursor.fetchone()

    if player_skills_list:
        player_skills_list = [skill for skill in player_skills_list if skill]

        if player_skills_list:
            player_available_skills = [skill for skill in player_skills_list if skill in player_skills]

    win = False
    battle_embed = discord.Embed(title="戰鬥開始！", description=f"你正在與 {monster_stats['name']} 進行戰鬥。", color=0xFF0000)
    battle_embed.set_footer(text="我是ZU, 為您服務")
    await ctx.send(embed=battle_embed)

    player_hp = player_stats[4]
    player_maxHp = player_stats[5]
    player_attack = player_stats[6]
    player_defense = player_stats[7]
    player_strength = player_stats[8]
    player_intelligence = player_stats[9]
    player_MP = player_stats[13]
    player_max_Mp = player_stats[14]
    monster_hp = monster_stats["HP"]
    round = 1
    player_data = {
        "HP": player_hp,
        "max_HP": player_maxHp,
        "attack": player_attack,
        "defense": player_defense,
        "strength": player_strength,
        "intelligence": player_intelligence,
        "Mp": player_MP,
        "max_Mp": player_max_Mp
    }

    while player_hp > 0 and monster_hp > 0:
        player_skill_choices = ", ".join(player_available_skills) if player_available_skills else "無可用技能"
        options_embed = discord.Embed(title="您的回合", description="請選擇您的行動：", color=0xFF0000)
        options_embed.add_field(name="1. 普通攻擊", value="", inline=False)
        options_embed.add_field(name="2. 技能攻擊", value=player_skill_choices, inline=False)
        options_embed.add_field(name="3. 使用藥水", value="", inline=False)
        options_embed.set_footer(text="請在聊天中輸入選項編號。")
        await ctx.send(embed=options_embed)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content in ['1', '2', '3']

        try:
            msg = await bot.wait_for('message', check=check, timeout=180.0)
        except asyncio.TimeoutError:
            await ctx.send("您的操作已超時！")
            return

        action = msg.content
        battle_result_embed = discord.Embed(title="戰鬥結果", color=0xFF0000)

        if action == '1':  # 普通攻擊
            player_damage = calculate_damage(ctx, player_data, monster_stats, round)
            monster_hp -= player_damage
            battle_result_embed.add_field(name="玩家攻擊", value=f"您對 {monster_stats['name']} 造成了 {player_damage} 點傷害！", inline=False)
        elif action == '2':  # 技能攻擊
            if not player_available_skills:
                await ctx.send("您沒有可用的技能！")
                break

            skill_embed = discord.Embed(title="選擇技能", description="請選擇您要使用的技能：", color=0xFF0000)
            for idx, skill in enumerate(player_available_skills, start=1):
                skill_embed.add_field(name=f"{idx}. {skill}", value=f"MP 消耗: {player_skills[skill]['MP']}", inline=False)
            await ctx.send(embed=skill_embed)

            try:
                msg = await bot.wait_for('message', check=check, timeout=180.0)
            except asyncio.TimeoutError:
                await ctx.send("您的操作已超時！")
                return

            skill_choice = player_available_skills[int(msg.content) - 1]
            skill_effect = player_skills[skill_choice]

            if player_MP < skill_effect['MP']:
                await ctx.send("您的魔力不足以使用這個技能！")
                continue

            player_MP -= skill_effect['MP']

            player_damage = calculate_damage(ctx, player_data, monster_stats, round, skill_effect,)
            monster_hp -= player_damage

            battle_result_embed.add_field(name="技能攻擊", value=f"您使用了 {skill_choice} 技能對 {monster_stats['name']} 造成了 {player_damage} 點傷害 消耗了 {player_skills[skill]['MP']} 點魔力!", inline=False)

        elif action == '3':  # 使用藥水
            cursor.execute(f"SELECT item_name FROM bag WHERE owner_id = ? AND item_type = ?", (user_id, "藥水"))
            potion_items = cursor.fetchall()
            potion_choices = {str(idx): potion[0] for idx, potion in enumerate(potion_items, start=1)}

            if not potion_choices:
                await ctx.send("您沒有藥水可用！")
                continue

            potion_embed = discord.Embed(title="使用藥水", description="請選擇您要使用的藥水：", color=0xFF0000)
            for idx, potion_name in potion_choices.items():
                potion_embed.add_field(name=f"{idx}. {potion_name}", value=f"恢復 {potion_effects.get(potion_name, {}).get('HP', 0)} HP 和 {potion_effects.get(potion_name, {}).get('MP', 0)} MP", inline=False)
            await ctx.send(embed=potion_embed)

            try:
                msg = await bot.wait_for('message', check=check, timeout=180.0)
            except asyncio.TimeoutError:
                await ctx.send("您的操作已超時！")
                return

            potion_name = potion_choices.get(msg.content)
            if potion_name:
                potion_effect = potion_effects.get(potion_name)
                if potion_effect:
                    player_hp += potion_effect.get('HP', 0)
                    player_MP += potion_effect.get('MP', 0)
                    if player_hp > player_maxHp:
                        player_hp = player_maxHp
                    if player_MP > player_max_Mp:
                        player_MP = player_max_Mp
                    await ctx.send(f"使用了 {potion_name}，恢復了{potion_effect.get('HP', 0)} HP 和 {potion_effect.get('MP', 0)} MP！")
                else:
                    await ctx.send("無效的藥水名稱！")
            else:
                await ctx.send("無效的選擇！")

        if monster_hp > 0:
            monster_damage = anthor_damage(ctx, monster_stats,player_data)
            player_hp = max(0, player_hp - monster_damage)

            battle_result_embed.add_field(name="怪物攻擊", value=f"{monster_stats['name']} 對您造成了 {monster_damage} 點傷害！", inline=False)
            battle_result_embed.add_field(name="玩家HP", value=f"{player_hp} / {player_maxHp}", inline=False)
            battle_result_embed.add_field(name="怪物HP", value=f"{monster_hp} / {monster_stats['max_HP']}", inline=False)
            battle_result_embed.add_field(name=f"第{round}回合", value="", inline=False)
            await ctx.send(embed=battle_result_embed)

            round += 1
        else:
            loot_items = monster_stats.get("loot", {})
            money = monster_stats.get("money", 0)
            experience = monster_stats.get("experience", 0)
            Main_story = monster_stats.get("Main_story", "")

            await ctx.send(f"您擊敗了{monster_stats.get('name', '未知怪物')}")
            
            cursor.execute("UPDATE player_info SET money = money + ? WHERE user_id = ?", (money, user_id))
            cursor.execute("UPDATE player_info SET Main_story = ? WHERE user_id = ?", (Main_story, user_id))
            cursor.execute("UPDATE player_info SET experience = experience + ? WHERE user_id = ?", (experience, user_id))
            conn.commit()
            
            loot_info = []
            for loot_item in monster_stats["loot"]:
                item_name = loot_item["name"]
                quantity = loot_item.get("quantity", 0)
                item_type = loot_item.get("item_type", "")
                probability = loot_item.get("probability", 1.0)  # 如果未指定機率，默認為1.0，即100%

                if random.random() < probability:
                    cursor.execute("SELECT quantity FROM bag WHERE owner_id = ? AND item_name = ?", (user_id, item_name))
                    existing_quantity = cursor.fetchone()

                    if existing_quantity:
                        new_quantity = existing_quantity[0] + quantity
                        cursor.execute("UPDATE bag SET quantity = ? WHERE owner_id = ? AND item_name = ?", (new_quantity, user_id, item_name))
                    else:
                        cursor.execute("INSERT INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (user_id, item_name, quantity, item_type))

                    loot_info.append(f"{item_name}: {quantity}")


            level_experience_mapping = {
                1: 100,
                2: 300,
                3: 600,
                4: 1200,
                5: 3000,
                6: 5000,
                7: 7500,
                8: 10000,
                9: 15000,
                10: 25000,
                11: 50000,
                12: 100000,
                13: 200000,
                14: 350000,
                15: 500000,         
            }
            next_max_experience = level_experience_mapping.get(player_stats[3] + 1, 0)

            # Create an embed for loot information
            loot_embed = discord.Embed(title="戰利品", color=0x00ff9d)
            loot_embed.add_field(name="金錢", value=str(money), inline=False)
            loot_embed.add_field(name="經驗", value=str(experience), inline=False)
            for item_info in loot_info:
                loot_embed.add_field(name="物品", value=item_info, inline=False)
            loot_embed.set_footer(text="我是ZU, 為您服務")
            # Send the loot information as an embed
            await ctx.send(embed=loot_embed)

            cursor.execute("SELECT experience FROM player_info WHERE user_id = ?", (user_id,))
            experience = cursor.fetchone()
            cursor.execute("SELECT max_experience FROM player_info WHERE user_id = ?", (user_id,))
            max_experience = cursor.fetchone()

            if experience[0] >= max_experience[0]:
                while experience[0] >= max_experience[0]:
                    lost_experience = experience[0] - max_experience[0]
                    cursor.execute("UPDATE player_info SET experience = ? WHERE user_id = ?", (lost_experience, user_id))
                    cursor.execute("UPDATE player_info SET max_experience = ? WHERE user_id = ?", (next_max_experience, user_id))
                    cursor.execute("UPDATE player_info SET level = level + 1 WHERE user_id = ?", (user_id,))
                    cursor.execute("UPDATE player_info SET Ability_points = Ability_points + 3 WHERE user_id = ?", (user_id,))
                    cursor.execute("SELECT experience FROM player_info WHERE user_id = ?", (user_id,))
                    experience = cursor.fetchone()
                    cursor.execute("SELECT max_experience FROM player_info WHERE user_id = ?", (user_id,))
                    max_experience = cursor.fetchone()

                level_embed = discord.Embed(title="升級", color=0x00ff9d)
                level_embed.add_field(name="您升級到了", value=f"{player_stats[3] + 1}級", inline=False)
                level_embed.set_footer(text="我是ZU, 為您服務")
                await ctx.send(embed=level_embed)

            cursor.execute("SELECT title FROM quests WHERE user_id = ?", (user_id,))
            title = cursor.fetchone()
            title = title[0] if title else None
            await update_quest_progress(ctx, cursor, user_id, "村長任務 - 擊敗遠古矮人", 10, "區域 - 草原")
            conn.commit()
            conn.close()
            win = True

    if win:
        return
    else:
        await ctx.send("您已經死了。")

async def update_quest_progress(ctx, cursor, user_id, quest_title, increment, local):
    cursor.execute("SELECT progress FROM quests WHERE user_id = ? AND title = ?", (user_id, quest_title))
    progress = cursor.fetchone()

    if progress is not None:
        current_progress = progress[0]
        new_progress = min(current_progress + increment, 100)  # 限制進度最大值為 100
        cursor.execute("UPDATE quests SET progress = ? WHERE user_id = ? AND title = ?", (new_progress, user_id, quest_title))
    cursor.execute("SELECT * FROM quests WHERE user_id = ? AND title = ?", (user_id,quest_title))
    quests = cursor.fetchone()
    new_progress = quests[10]
    if new_progress == 100 or new_progress == "100":
        quest_embed = discord.Embed(title=f"{quest_title}", color=0x00ff9d)
        quest_embed.add_field(name=f"{quest_title} 已完成，請盡快去{local}領取獎勵", value="", inline=False)
        await ctx.send(embed=quest_embed)


#群聊系統---------------------------------------------------------------------------------------------------------------------------------
        
virtual_chatrooms = {}

@bot.command()
async def chat(ctx, room_name: str):
    # 檢查聊天室是否已經存在
    if room_name in virtual_chatrooms:
        await ctx.send(f"聊天室 '{room_name}' 已存在，請選擇其他名稱。")
        return

    # 創建新的聊天室
    virtual_chatrooms[room_name] = []

    await ctx.send(f"聊天室 '{room_name}' 已創建！")

@bot.command()
async def join(ctx, room_name: str):
    # 檢查用戶是否已經在該聊天室中
    if ctx.author.id in virtual_chatrooms.get(room_name, []):
        await ctx.send(f"您已經在聊天室 '{room_name}' 中。")
    else:
        # 加入聊天室
        virtual_chatrooms[room_name].append(ctx.author.id)
        await ctx.send(f"您已成功加入聊天室 '{room_name}'。")

@bot.command()
async def leave(ctx, room_name: str):
    # 檢查用戶是否在聊天室中
    if ctx.author.id in virtual_chatrooms.get(room_name, []):
        # 離開聊天室
        virtual_chatrooms[room_name].remove(ctx.author.id)
        await ctx.send(f"您已成功離開聊天室 '{room_name}'。")
    else:
        await ctx.send(f"您不在聊天室 '{room_name}' 中。")

@bot.command()
async def say(ctx, room_name: str, *, message: str):
    # 檢查用戶是否在聊天室中
    if ctx.author.id in virtual_chatrooms.get(room_name, []):
        # 發送消息到聊天室
        for user_id in virtual_chatrooms[room_name]:
            user = bot.get_user(user_id)
            if user:
                await user.send(f"[{room_name}] {ctx.author.display_name}: {message}")

        # 刪除在公共頻道中的消息
        await ctx.user.send.delete()
    else:
        await ctx.send(f"您不在聊天室 '{room_name}' 中，無法發送消息。")
#-----------------------------------------------------移動------------------------------------------------------------
# 定義區域大小
region_size = 25

# 移動速度
base_speed = 1  # 移動一單位距離的基本時間（秒）
region_speed = 5  # 跨區域的額外時間（秒）
world_speed = 10  # 跨世界的額外時間（秒）

# 新手村規劃
def get_region(region, x, y):
    if region == "新手村":
        # 區域 - 新手引導(冒險者公會)
        if -5 <= x <= 5 and -5 <= y <= 5:
            return "區域 - 新手引導(冒險者公會)"
        # 區域 - 村莊
        elif 5 <= x <= 25 and -5 <= y <= 25:
            return "區域 - 村莊"
        # 區域 - 商店
        elif -15 <= x <= 5 and 5 <= y <= 25:
            return "新手商店"
        # 區域 - 村長的家
        elif -25 <= x <= -15 and 5 <= y <= 25:
            return "區域 - 村長的家"
        # 區域 - 鍛鍊場
        elif -25 <= x <= -5 and -25 <= y <= 5:
            return "區域 - 鍛鍊場"
        # 區域 - 草原
        elif -5 <= x <= 25 and -25 <= y <= -5:
            return "區域 - 草原"
        else:
            return f"區域 ({x}, {y}) - 未知區域"
    if region == "洛亞斯爾聖地-王都":
        # 區域 - 王都
        if -5 <= x <= 5 and -5 <= y <= 5:
            return "區域 - 王都"

async def move_work(ctx, region, x, y, region_info):
    user_id = ctx.author.id
    user = await bot.fetch_user(user_id)
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()
    if get_region(region, x, y) == "新手商店":
        shop_embed = discord.Embed(title=f"{region_info}", description="", color=0x00ffbf)
        shop_embed.add_field(name=f"{user.mention}", value=f"你好這位冒險家我叫露娜, 歡迎來到我的商店", inline=False)
        shop_embed.add_field(name=f"{user.mention}", value=f"使用 !shop_list [新手商店] 能查到這裡賣捨麼", inline=False)
        shop_embed.add_field(name=f"{user.mention}", value=f"使用 !buy [物品名稱] [數量] 能購買", inline=False)
        shop_embed.add_field(name=f"{user.mention}", value=f"使用 !add [物品名稱] [數量] [價格] 能在我的上架物品, 我會收取5%的錢作為手續費", inline=False)
        await ctx.send(embed=shop_embed)

    if get_region(region, x, y) == "區域 - 新手引導(冒險者公會)":
        cursor.execute("SELECT main_job FROM player_info WHERE user_id = ?", (user_id,))
        main_job = cursor.fetchone()
        cursor.execute("SELECT sub_job FROM player_info WHERE user_id = ?", (user_id,))
        sub_job = cursor.fetchone()
        cursor.execute("SELECT level FROM player_info WHERE user_id = ?", (user_id,))
        level = cursor.fetchone()
        if main_job[0] is None:
            main_job_embed = discord.Embed(title=f"{region_info}", description="", color=0x00ffbf)
            main_job_embed.add_field(name=f"{user.mention}", value=f"", inline=False)
            main_job_embed.add_field(name=f"您還未選擇主職業使用 !main_job 選擇", value=f"", inline=False)
            await ctx.send(embed=main_job_embed)
        elif sub_job[0]is None:
            sub_job_embed = discord.Embed(title=f"{region_info}", description="", color=0x00ffbf)
            sub_job_embed.add_field(name=f"", value=f"您還未選擇副職業使用 !sub_job 選擇", inline=False)
            await ctx.send(embed=sub_job_embed)
        elif level[0] < 5:
            main_job_embed = discord.Embed(title=f"{region_info}", description="", color=0x00ffbf)
            main_job_embed.add_field(name=f"", value=f"您等級太低請到 草原 刷怪升級到五級吧!", inline=False)
            await ctx.send(embed=main_job_embed)
        else:
            main_job_embed = discord.Embed(title=f"{region_info}", description="", color=0x00ffbf)
            main_job_embed.add_field(name=f"", value=f"您抵達新手村要求現在將把您傳送到 洛亞斯爾聖地-王都 !", inline=False)
            await ctx.send(embed=main_job_embed)

    if get_region(region, x, y) == "區域 - 村莊":
        main_job_embed = discord.Embed(title=f"{region_info}", description="", color=0x00ffbf)
        main_job_embed.add_field(name=f"", value=f"到 冒險者公會 完成新手任務離開新手村", inline=False)
        await ctx.send(embed=main_job_embed)

    if region_info == "區域 - 村長的家":
        cursor.execute("SELECT * FROM quests WHERE user_id = ? AND title = ?", (user_id, "村長任務 - 擊敗遠古矮人"))
        quests = cursor.fetchone()
        progress = quests[10]
        if progress == 100:
            cursor.execute(f"SELECT item_name FROM bag WHERE owner_id = ? AND item_name = ?", (user_id, "新手武器包"))
            existing_item = cursor.fetchone()
            if existing_item:
                # 更新物品數量
                cursor.execute(f"UPDATE bag SET quantity = quantity + ? WHERE owner_id = ? AND item_name = ?", (1, user_id, "新手武器包"))
                conn.commit()
                conn.close()
            else:
                if existing_item is None:
                    cursor.execute(f"INSERT INTO bag (owner_id, item_name, quantity, item_type) VALUES (?, ?, ?, ?)", (user_id, "新手武器包", 1, "材料"))
                    conn.commit()
                    conn.close()
                    embed=discord.Embed(color=0x00ff9d)
                    embed.add_field(name=f"恭喜你完成 村長任務 - 擊敗遠古矮人 ", value="已將新手武器包放入背包", inline=False)
                    embed.set_footer(text="我是ZU, 為您服務")
                    await ctx.send(embed=embed)

                # 新增物品到背包
                else:
                    cursor.execute(f"UPDATE bag SET item_name = ?, quantity = ?, item_type = ? WHERE user_id = ? AND item_name = ?",("新手武器包", 1, user_id, "材料", "新手武器包"))
                    conn.commit()
                    conn.close()
                    embed=discord.Embed(color=0x00ff9d)
                    embed.add_field(name=f"恭喜你完成 村長任務 - 擊敗遠古矮人 ", value="已將新手武器包放入背包", inline=False)
                    embed.set_footer(text="我是ZU, 為您服務")
                    await ctx.send(embed=embed)

        else:
            main_job_embed = discord.Embed(title=f"{region_info}", description="", color=0x00ffbf)
            main_job_embed.add_field(name=f"", value=f"你好，冒險者！我有一個任務需要你完成, 請前往草原，擊敗遠古矮人，完成任務後，你將獲得新手武器包 1 個。你願意接受嗎？", inline=False)
            main_job_embed.add_field(name=f"選擇 yes or no", value=f"", inline=False)
            await ctx.send(embed=main_job_embed)

            # 等待玩家回應
            def check(response):
                return response.author == user and response.content.lower() in ['yes', 'no']

            try:
                response = await bot.wait_for('message', timeout=180.0, check=check)

                if response.content.lower() == 'yes':
                    await ctx.send(f"太好了，謝謝你願意幫忙, 使用 !quests 可以看到目前的任務進度")
                    # 觸發一個示例任務
                    trigger_quest(
                        user_id = user_id,
                        title="村長任務 - 擊敗遠古矮人",
                        description="前往草原擊敗 10 隻遠古矮人，獲得新手武器包。",
                        trigger_region="草原",
                        reward_money=0,
                        reward_item_name = "新手武器包",
                        reward_item_quantity = 1,
                        completion_region="區域 - 村長的家"
                    )

                else:
                    await ctx.send("感謝你的考慮，如果你改變主意，請隨時來找我。")
            except asyncio.TimeoutError:
                await ctx.send("時間已經過去，任務失效。如果你想接受任務，請再次找我。")

    if get_region(region, x, y) == "區域 - 草原":
        
        battle_embed = discord.Embed(title="是否要觀看劇情", description=f"", color=0xFF0000)
        battle_embed.add_field(name=f"1 觀看\n2 跳過", value=f" ", inline=False)
        battle_embed.set_footer(text="我是ZU, 為您服務")
        await ctx.send(embed=battle_embed)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content in ['1', '2']
        
        try:
            msg = await bot.wait_for('message', check=check, timeout=180.0)
        except asyncio.TimeoutError:
            await ctx.send("您的操作已超時")
            return
        
        if msg.content == '1':
            story_embed = discord.Embed(title="第一章 開端 這是一個古老故事的開始", color=0x00ffbf)
            story_embed.add_field(name="敘述著遠古時代的神秘與奇跡", value="在這個古老的大陸上，傳說著一個被時間深深遺忘的種族——矮人，他們曾經在大地上建立了無數堅固的城堡，挖掘了深不見底的礦脈，展現出不凡的技藝和堅毅的精神。", inline=False)
            story_embed.add_field(name="然而，隨著歲月的流逝...", value="這個榮耀的種族逐漸消失在歷史的長河中。他們的城市被風沙掩埋，礦脈的寶藏也被深深埋蔽，彷彿這個種族從未存在過。", inline=False)
            story_embed.add_field(name="傳說中，那些古老的城市和被世界遺忘的礦脈卻始終存在...", value="而你，年輕的冒險者，聽聞了這個傳說，被吸引著這段神秘的歷史，勇敢地踏上了尋找遠古矮人遺跡的冒險之旅。", inline=False)
            story_embed.add_field(name="在踏上這段旅程的過程中...", value="你不僅發現了那些被荒廢的城市，還遭遇到了居住在遠古礦脈中的古老矮人靈魂。這些靈魂守護著失落的寶藏，並且懷著沉睡千年的憤怒，對來者進行著嚴峻的考驗。", inline=False)
            story_embed.add_field(name="這是你與遠古矮人的首次交鋒...", value="他們的技藝與你的武器碰撞，古老的符文與魔法交織，劇烈的戰鬥在這片被時光遺忘的土地上展開。你將面臨著前所未有的挑戰，但也將揭開這段古老故事的神秘面紗，一步步走向屬於你的冒險傳奇。", inline=False)
            story_embed.add_field(name="您遇到了 遠古矮人", value="您要怎麼應對這場挑戰？\n1. 準備好戰鬥\n2. 逃跑", inline=False)
            story_embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=story_embed)
        elif msg.content == '2':
            battle_embed = discord.Embed(title="跳過劇情", description=f"", color=0xFF0000)
            battle_embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=battle_embed)

        combat_embed = discord.Embed(title=f"{region_info}", description="", color=0x00ffbf)
        combat_embed.add_field(name=f"{user.mention}", value=f"你遇到了 遠古矮人 要與之一戰嗎?", inline=False)
        combat_embed.add_field(name=f"1 戰鬥\n2 逃離", value=f"", inline=False)
        await ctx.send(embed=combat_embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content in ['1', '2']

        try:
            msg = await bot.wait_for('message', check=check, timeout=180.0)
        except asyncio.TimeoutError:
            await ctx.send("您的操作已超時")
            return

        if msg.content == '1':
            monster_data = {
                "name": "遠古矮人",
                "HP": 500,
                "max_HP": 500,
                "attack": 20,
                "defense": 250,
                "strength": 8,
                "intelligence": 3,
                "money": random.randint(35, 55),
                "experience": random.randint(50, 100),
                "Main_story": "1-1",
                "loot": [
                ],
            }
            await battle(ctx, monster_data)
        elif msg.content == '2':
            battle_embed = discord.Embed(title="戰鬥結束！", description=f"您脫離了戰鬥", color=0xFF0000)
            battle_embed.set_footer(text="我是ZU, 為您服務")
            await ctx.send(embed=battle_embed)

# 計算移動時間
def calculate_travel_time(region1, region2, x1, y1, x2, y2):
    # 計算與中心的距離
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)/5

    # 計算基本移動時間
    base_time = distance * base_speed

    # 跨區域額外時間
    region_penalty = 0
    if region1 != region2:
        region_penalty = region_speed


    total_time = base_time + region_penalty 
    return total_time

async def move_command(ctx, region, coordinates):
    x, y = map(int, coordinates.split(','))

    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()
        user_id = ctx.author.id

        cursor.execute("SELECT * FROM map WHERE user_id = ?", (user_id,))
        map_info = cursor.fetchone()

        if map_info:
            travel_time = calculate_travel_time(map_info[2], region, map_info[3], map_info[4], x, y)
            region_info = get_region(region, x, y)

            # Create an Embed for the move information
            move_embed = discord.Embed(title="移動信息", description=f"預計花費時間 {travel_time:.2f} 秒", color=0x00ffbf)
            move_embed.add_field(name="目標座標", value=f"({x}, {y})", inline=False)
            move_embed.add_field(name="目標區域", value=region_info, inline=False)
            await ctx.send(embed=move_embed)

            await asyncio.sleep(travel_time)

            cursor.execute("UPDATE map SET region = ?, x = ?, y = ? WHERE user_id = ?", (region, x, y, user_id))
            conn.commit()

            # Send the move information using Embed
            embed = discord.Embed(title="移動信息", description=f"", color=0x00ffbf)
            embed.add_field(name="抵達座標", value=f"({x}, {y})", inline=False)
            embed.add_field(name="抵達區域", value=region_info, inline=False)
            await ctx.send(embed=embed)

            await move_work(ctx, region, x, y, region_info)
        else:
            await ctx.send("請先使用 !register 進行註冊")

bot.remove_command('move')

# 假設您有一個處理指令的函數
@bot.command()
async def move(ctx, region, coordinates):
    await move_command(ctx, region, coordinates)

# 增加查看位置的指令
@bot.command(name='location')
async def location(ctx):
    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()
        user_id = ctx.author.id

        cursor.execute("SELECT * FROM map WHERE user_id = ?", (user_id,))
        map = cursor.fetchone()

        if map:
            region_info = get_region(map[2], map[3], map[4])

            # Create an Embed for the location information
            location_embed = discord.Embed(title="位置信息", color=0x00ff9d)
            location_embed.add_field(name="當前座標", value=f"({map[3]}, {map[4]})", inline=False)
            location_embed.add_field(name="當前區域", value=f"{map[2]}的{region_info}", inline=False)

            # Send the location information using Embed
            await ctx.send(embed=location_embed)
        else:
            register_embed = discord.Embed(title="註冊", color=0x00ff9d)
            register_embed.add_field(name="請先使用 !register 進行註冊", value="", inline=False)

            # Send the location information using Embed
            await ctx.send(embed=register_embed)

#-------------------------------------------------- 任務系統 ---------------------------------------------------------
        
# 函數：觸發任務
def trigger_quest(user_id, title, description, trigger_region, reward_money, reward_item_name=None, reward_item_quantity=None, completion_region=None):
    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quests (user_id, title, description, trigger_region, reward_money, reward_item_name, reward_item_quantity, completion_region, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (user_id, title, description, trigger_region, reward_money, reward_item_name, reward_item_quantity, completion_region))
        conn.commit()

@bot.command(name='quests')
async def quests(ctx):
    with sqlite3.connect(Database) as conn:
        cursor = conn.cursor()
        user_id = ctx.author.id

        cursor.execute("SELECT * FROM quests WHERE user_id = ?", (user_id,))
        quests = cursor.fetchall()

        if quests:
            # 創建一個 Embed
            quests_embed = discord.Embed(title="您的任務列表", color=0x00ff9d)

            for quest in quests:
                quest_id, title, description, trigger_region, reward_money, reward_item_name, reward_item_quantity, reward_loop, completion_region, user_id, progress = quest

                completion_status = "已完成" if progress == 100 else f"進度: {progress}%"

                # 添加每個任務信息到 Embed 的不同字段
                quests_embed.add_field(name=f"任務 {title}",
                                       value=f"描述: {description}\n"
                                             f"觸發區域: {trigger_region}\n"
                                             f"獎勵金錢: {reward_money}\n"
                                             f"獎勵物品: {reward_item_name} * {reward_item_quantity}\n"
                                             f"完成區域: {completion_region}\n"
                                             f"{completion_status}",
                                       inline=False)

            # 發送包含所有任務信息的 Embed
            await ctx.send(embed=quests_embed)
        else:
            await ctx.send("目前沒有任務。")
               
#-----------------------------------------------------------------------------------------------------------------------------------------------
@tasks.loop(hours=24)  # 每24小時執行一次
async def daily_reminder():
    channel_id = 1102081674923225140  # 替換為實際的頻道ID
    channel = bot.get_channel(channel_id)

    if channel:
        current_time = datetime.datetime.now().strftime("%H:%M")
        if current_time == "09:00":
            await channel.send("早上好 !")
#-------------------------------------------------- 股市系統 ---------------------------------------------------------   

# 股市系統 - 新增每天更新股市的任務
@tasks.loop(hours=24)  
async def update_stock_market():
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    yesterday = datetime.date.today() - datetime.timedelta(days=1)

    cursor.execute("""
        SELECT DISTINCT item_name, shop
        FROM stock_market
        WHERE date = ?
    """, (yesterday,))

    items_and_shops = cursor.fetchall()

    for item, shop in items_and_shops:
        cursor.execute("""
            SELECT week, average_price, highest_price, lowest_price
            FROM stock_market
            WHERE item_name = ? AND shop = ? AND date BETWEEN date(?, '-6 days') AND date(?)
        """, (item, shop, yesterday, yesterday))

        data = cursor.fetchall()

        if not data:
            continue

        weeks = [entry[0] for entry in data]
        average_prices = [entry[1] for entry in data]
        highest_prices = [entry[2] for entry in data]
        lowest_prices = [entry[3] for entry in data]

        plt.figure(figsize=(10, 6))
        plt.plot(weeks, average_prices, label='Average Price', marker='o')
        plt.plot(weeks, highest_prices, label='Highest Price', marker='o')
        plt.plot(weeks, lowest_prices, label='Lowest Price', marker='o')

        plt.title(f"{item} 在 {shop} 的股市資訊 (最近七天)")
        plt.xlabel("Week")
        plt.ylabel("Price")
        plt.legend()

        image_stream = BytesIO()
        plt.savefig(image_stream, format='png')
        plt.close()

        image_stream.seek(0)

        channel_id = 1192518148361031791
        channel = bot.get_channel(channel_id)

        if channel:
            await channel.send(file=discord.File(fp=image_stream, filename=f'{item}_{shop}_stock_market.png'))

    cursor.execute("""
        SELECT SUM(price) 
        FROM transactions 
        WHERE transaction_date = ?
    """, (yesterday,))
    total_transactions = cursor.fetchone()[0] 

    cursor.execute("""
        INSERT INTO daily_transactions (date, total_transactions)
        VALUES (?, ?)
    """, (yesterday, total_transactions))

    conn.commit()
    conn.close()

@update_stock_market.before_loop
async def before_update_stock_market():
    await bot.wait_until_ready()


@bot.command(name='update_stock_market')
async def update_stock_market(ctx):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    yesterday = datetime.date.today() - datetime.timedelta(days=1)

    cursor.execute("""
        SELECT DISTINCT item_name, shop
        FROM stock_market
        WHERE date = ?
    """, (yesterday,))

    items_and_shops = cursor.fetchall()

    for item, shop in items_and_shops:
        cursor.execute("""
            SELECT week, average_price, highest_price, lowest_price
            FROM stock_market
            WHERE item_name = ? AND shop = ? AND date BETWEEN date(?, '-6 days') AND date(?)
        """, (item, shop, yesterday, yesterday))

        data = cursor.fetchall()

        if not data:
            continue

        weeks = [entry[0] for entry in data]
        average_prices = [entry[1] for entry in data]
        highest_prices = [entry[2] for entry in data]
        lowest_prices = [entry[3] for entry in data]

        plt.figure(figsize=(10, 6))
        plt.plot(weeks, average_prices, label='Average Price', marker='o')
        plt.plot(weeks, highest_prices, label='Highest Price', marker='o')
        plt.plot(weeks, lowest_prices, label='Lowest Price', marker='o')

        plt.title(f"{item} 在 {shop} 的股市資訊 (最近七天)")
        plt.xlabel("Week")
        plt.ylabel("Price")
        plt.legend()

        image_stream = BytesIO()
        plt.savefig(image_stream, format='png')
        plt.close()

        image_stream.seek(0)
        await ctx.send(file=discord.File(fp=image_stream, filename=f'{item}_{shop}_stock_market.png'))

    conn.close()
#-------------------------------------------------- 股市測試 ---------------------------------------------------------   
@bot.command(name='creat')
async def creat(ctx):
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    items = ["item1", "item2", "item3"]
    shops = ["shop1", "shop2", "shop3"]

    date_range = [dt.date.today() - dt.timedelta(days=i) for i in range(7)]

    for date in date_range:
        for item in items:
            for shop in shops:
                week = date.strftime("%Y-%m-%d")
                average_price = random.randint(50, 200) 
                highest_price = average_price + random.randint(0, 50) 
                lowest_price = max(0, average_price - random.randint(0, 50)) 
                cursor.execute("""
                    INSERT INTO stock_market (item_name, shop, date, week, average_price, highest_price, lowest_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (item, shop, date, week, average_price, highest_price, lowest_price))

    conn.commit()
    conn.close()


#--------------------------------------------------------------------------------------------------------------------
@bot.command(name='delete')
async def delete_records(ctx, player: discord.User, table):
    if ctx.message.author.guild_permissions.administrator:
        allowed_tables = ["player_info", "auction", "bag", "equipment", "farmers", "guild_members", "guild_applications", "guilds", "items", "map", "monster_info", "quests", "stock_market"]  # 添加其他允许的表名
        if table not in allowed_tables:
            await ctx.send("无效的表名。")
            return

        with sqlite3.connect(Database) as conn:
            cursor = conn.cursor()
            user_id_tables = ["guild_applications", "guild_members", "map", "player_info, "]
            auction_tables = ["auction"]
            owner_id_tables = ["bag"]
            player_id_tables = ["equipment", "farmers"]
            if table in user_id_tables:
                cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (player.id,))
                conn.commit()
            if table in auction_tables:
                cursor.execute(f"DELETE FROM {table} WHERE auction_id = ?", (player.id,))
                conn.commit()
            if table in owner_id_tables:
                cursor.execute(f"DELETE FROM {table} WHERE owner_id = ?", (player.id,))
                conn.commit()
            if table in player_id_tables:
                cursor.execute(f"DELETE FROM {table} WHERE player_id = ?", (player.id,))
                conn.commit()

        await ctx.send(f"{table} 中的 {player.display_name} 的所有记录已被删除。")
    else:
        await ctx.send("您没有执行此操作所需的权限。")

@bot.command()
async def delete_all_items(ctx):
    if ctx.message.author.guild_permissions.administrator:
        with sqlite3.connect(Database) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items")
            conn.commit()

        await ctx.send("所有物品已成功删除。")
    else:
        await ctx.send("您没有执行此操作所需的权限。")
@bot.command()
async def change_seller(ctx):
    # 检查是否为管理员
    if ctx.message.author.guild_permissions.administrator:
        # 使用 UPDATE 语句更改所有记录的 seller_id
        with sqlite3.connect(Database) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET seller_id = '露娜'")
            conn.commit()

        await ctx.send("所有物品的卖家已成功更改为“露娜”。")
    else:
        await ctx.send("您没有执行此操作所需的权限。")



@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    

bot.run("TOKEN")
