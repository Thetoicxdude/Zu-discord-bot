# Discord RPG遊戲機器人

這是一個基於Discord的多功能RPG遊戲機器人,提供了豐富的遊戲功能和系統。玩家可以在Discord中體驗完整的RPG遊戲流程,包括角色創建、冒險、戰鬥、社交等多個方面。

## 主要功能

### 角色系統
- 角色註冊與管理
- 職業選擇(主職業和副職業)
- 等級提升與屬性分配
- 技能學習與使用

### 物品系統
- 背包管理
- 裝備穿戴與卸下
- 物品使用(如藥水)
- 物品合成

### 經濟系統
- 商店購買與出售
- 玩家間交易
- 拍賣系統
- 股市系統

### 地圖系統
- 多區域地圖
- 自由移動
- 區域探索
- 隨機事件

### 社交系統
- 公會創建與管理
- 公會任務
- 玩家聊天室

### 戰鬥系統
- 回合制戰鬥
- 技能使用
- 怪物掉落
- 經驗獲取

### 任務系統
- 主線任務
- 支線任務
- 每日任務
- 成就系統

### 其他系統
- 農場與採集
- 製作系統
- 寵物系統(待實現)

## 主要指令

### 角色相關
- `!register` - 註冊新角色
- `!player_info` - 查看角色信息
- `!main_job <職業名>` - 選擇主職業
- `!sub_job <職業名>` - 選擇副職業
- `!level_up` - 升級並分配屬性點

### 物品相關
- `!bag` - 查看背包
- `!equip <物品名>` - 裝備物品
- `!unequip <物品名>` - 卸下裝備
- `!use <物品名>` - 使用物品

### 經濟相關
- `!shop_list` - 查看商店物品列表
- `!buy <物品名> <數量>` - 購買物品
- `!sell <物品名> <數量>` - 出售物品
- `!add <物品名> <數量> <價格>` - 上架物品到拍賣行
- `!remove <物品名>` - 從拍賣行下架物品

### 地圖相關
- `!move <區域名> <x座標>,<y座標>` - 移動到指定位置
- `!location` - 查看當前位置

### 公會相關
- `!build_guild <公會名>` - 創建公會
- `!join_guild <公會名>` - 加入公會
- `!guild` - 查看公會信息
- `!guild_members` - 查看公會成員列表

### 戰鬥相關
- 戰鬥系統自動觸發,無需特定指令

### 任務相關
- `!quests` - 查看當前任務列表

### 其他
- `!plant <作物名>` - 種植作物
- `!harvest` - 收穫作物
- `!craft <物品名>` - 製作物品

## 技術實現

- 使用 Discord.py 庫開發,實現與Discord API的交互
- 採用SQLite數據庫存儲遊戲數據,包括玩家信息、物品、公會等
- 使用異步編程處理用戶交互,提高響應速度
- 模塊化設計各個遊戲系統,便於擴展和維護
- 使用embed消息美化輸出,提升用戶體驗
- 實現了基本的錯誤處理和日誌記錄

## 安裝與運行

1. 克隆項目:
   ```
   git clone https://github.com/yourusername/discord-rpg-bot.git
   cd discord-rpg-bot
   ```

2. 安裝依賴:
   ```
   pip install -r requirements.txt
   ```

3. 設置 Discord Bot Token:
   - 在Discord開發者平台創建一個新的應用並獲取Bot Token
   - 將Token添加到配置文件或環境變量中

4. 初始化數據庫:
   ```
   python init_db.py
   ```

5. 運行bot:
   ```
   python main.py
   ```

## 配置

可以通過修改 `config.py` 文件來調整以下設置:
- Discord Bot Token
- 數據庫路徑
- 遊戲平衡參數(如經驗值曲線、物品價格等)
- 功能開關

## 貢獻

我們歡迎各種形式的貢獻,包括但不限於:
- 報告bug
- 提出新功能建議
- 改進代碼
- 優化遊戲平衡
- 補充文檔

請先查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳細的貢獻指南。

## 待實現功能

- [ ] 寵物系統
- [ ] PVP競技場
- [ ] 排行榜系統
- [ ] 更多職業和技能
- [ ] 副本系統

## 授權

本項目採用 MIT 授權協議。詳見 [LICENSE](LICENSE) 文件。

## 聯繫方式

如有任何問題或建議,請通過以下方式聯繫我們:
- Discord: [加入我們的Discord服務器](https://discord.gg/yourserver)
- Email: your.email@example.com
- GitHub Issues: [提交Issue](https://github.com/yourusername/discord-rpg-bot/issues)

