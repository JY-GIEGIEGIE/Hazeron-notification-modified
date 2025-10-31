import sqlite3
import json
import os
import hashlib
import copy
from typing import List, Dict, Any, Tuple
from datetime import datetime

# ==========================================================
# 路径定义
# ==========================================================
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'storage')
DB_FILE = os.path.join(DB_DIR, 'notifier.db')

# 确保 storage 目录存在
os.makedirs(DB_DIR, exist_ok=True) 

def get_db_connection():
    """获取数据库连接，启用字典访问和外键约束"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # 启用外键约束
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ==========================================================
# 1. 数据库初始化 (包含非破坏性配置更新)
# ==========================================================

# ==========================================================
# 辅助函数 1: 配置继承与任务生成
# ==========================================================

def _generate_task_list(sites_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    根据 sites_config 生成扁平化的任务列表。
    处理 Site 级配置的继承和 Channel 级配置的覆盖。
    修复了浅层复制导致的数据污染问题。
    """
    all_tasks = []
    
    for site in sites_config:
        site_name = site['name']
        mode = site.get('mode', 'html')
        channels_config = site.get('channels', [])
        
        # 提取 Site 级默认配置，使用 deepcopy 确保嵌套字典独立
        site_defaults = copy.deepcopy({
            k: v for k, v in site.items() if k not in ['name', 'channels']
        })
        
        # --- A. 处理多 Channel 任务 ---
        if channels_config:
            for channel in channels_config:
                # 任务配置从 Site 默认配置的深层副本开始
                task_config = copy.deepcopy(site_defaults)
                
                # Channel 级配置覆盖 Site 级配置
                for key, value in channel.items():
                    if key in ['channel_name', 'url']: 
                        continue
                    
                    # 对 html_config/api_config 进行深层合并
                    if key in ['html_config', 'api_config'] and isinstance(value, dict):
                        # 确保从 task_config 获取，并进行合并
                        inherited_conf = task_config.get(key, {}).copy()
                        inherited_conf.update(value)
                        task_config[key] = inherited_conf
                    else:
                        task_config[key] = value
                
                # 封装任务字典
                all_tasks.append({
                    'site_name': site_name,
                    'channel_name': channel['channel_name'],
                    'url_config_raw': channel['url'], 
                    'final_config_merged': task_config
                })
        
        # --- B. 处理单 Channel 任务 (Site 即 Channel) ---
        else:
            # Task config 即为 Site defaults 的深层副本
            task_config = site_defaults
            url_source_config = task_config.get(f'{mode}_config', {})
            
            all_tasks.append({
                'site_name': site_name,
                'channel_name': site_name, 
                'url_config_raw': url_source_config.get('url', ''),
                'final_config_merged': task_config
            })
            
    return all_tasks

# ==========================================================
# 辅助函数 2: 数据清洗与扁平化
# ==========================================================

def _prepare_channel_data(task: Dict[str, Any]) -> Tuple[str, str, str, str, str, str]:
    """
    将合并后的任务配置清洗、扁平化，并准备好 SQL 语句所需的参数。
    修复了 base_link_url 丢失问题：不再 pop 关键配置。
    """
    # 提取任务元数据
    site_name = task['site_name']
    channel_name = task['channel_name']
    final_config = task['final_config_merged']
    
    # 提取模式
    final_mode = final_config.get('mode', 'html')
    
    # URL 规范化
    url_config_raw = task['url_config_raw']
    url_list = [url_config_raw] if isinstance(url_config_raw, str) else (url_config_raw if isinstance(url_config_raw, list) else [])
    main_url = url_list[0] if url_list else "N/A"
    
    # 提取 base_link_url 到独立列变量 (L)
    base_link_url = ''
    config_key = f'{final_mode}_config'
    
    if config_key in final_config:
        # 从嵌套配置中提取 base_link_url
        base_link_url = final_config[config_key].get('base_link_url', '')
        
        # ⚠️ 【修复链接丢失问题】: 停止 pop 操作！
        # final_config[config_key].pop('url', None) 
        # final_config[config_key].pop('base_link_url', None) # 移除此行

    # 最终配置定型和序列化
    final_config['url_list'] = url_list # 添加规范化的 url 列表
    
    # 移除顶层冗余字段
    final_config.pop('name', None)
    final_config.pop('channels', None)
    final_config.pop('mode', None)
    
    config_json = json.dumps(final_config)
    
    # 返回 SQL 语句所需参数
    return site_name, channel_name, main_url, base_link_url, final_mode, config_json

# ==========================================================
# 主函数 1: 初始化数据库
# ==========================================================

def initialize_db(sites_config: List[Dict[str, Any]]):
    """
    主配置函数：初始化数据库结构，并执行非破坏性配置更新。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # --- A. 创建表结构 ---
    # Channel 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Channel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE, 
            base_link_url TEXT, 
            mode TEXT NOT NULL,
            config_json TEXT NOT NULL
        )
    """)
    # Notification 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Notification (
            fingerprint TEXT PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            published_date TEXT,
            push_time TEXT,
            FOREIGN KEY (channel_id) REFERENCES Channel(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_channel ON Notification (channel_id)")

    # --- B. 生成任务列表 ---
    tasks_to_process = _generate_task_list(sites_config)
    
    # --- C. 遍历任务并写入数据库 (非破坏性更新) ---
    for task in tasks_to_process:
        # 使用辅助函数进行数据清洗和准备
        site_name, channel_name, main_url, base_link_url, final_mode, config_json = _prepare_channel_data(task)

        # 1. 尝试 UPDATE 已存在的记录 (基于 url 唯一键)
        cursor.execute("""
            UPDATE Channel SET
                site_name = ?,
                channel_name = ?,
                base_link_url = ?,
                mode = ?,
                config_json = ?
            WHERE url = ?
        """, (site_name, channel_name, base_link_url, final_mode, config_json, main_url))
        
        # 2. 如果 UPDATE 失败 (即新配置)，则执行 INSERT
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT OR IGNORE INTO Channel 
                (site_name, channel_name, url, base_link_url, mode, config_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (site_name, channel_name, main_url, base_link_url, final_mode, config_json))

    conn.commit()
    conn.close()
    print("数据库初始化和配置导入完成。")


# ==========================================================
# 2. 核心去重和存储函数 (Fingerprint Logic)
# ==========================================================

def generate_fingerprint(title: str, link: str) -> str:
    """根据通知的标题和链接生成唯一的 SHA-256 指纹。"""
    # 【已修正】使用正确的 sha256 算法
    data = f"{title.strip().lower()}:{link.strip()}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def is_notification_new(fingerprint: str) -> bool:
    """检查通知是否已存在于 Notification 表中。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT 1 FROM Notification WHERE fingerprint = ?",
        (fingerprint,)
    )
    
    is_new = cursor.fetchone() is None
    conn.close()
    return is_new

def add_new_notification(channel_id: int, notification_data: Dict[str, str]) -> None:
    """将新的通知记录添加到 Notification 表中。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fingerprint = generate_fingerprint(
        notification_data['title'], 
        notification_data['link']
    )
    
    push_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 使用 OR IGNORE 确保即使并发写入也不会崩溃
    cursor.execute("""
        INSERT OR IGNORE INTO Notification 
        (fingerprint, channel_id, title, link, published_date, push_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        fingerprint,
        channel_id,
        notification_data['title'],
        notification_data['link'],
        notification_data.get('date', 'N/A'),
        push_time
    ))
    
    conn.commit()
    conn.close()

# ==========================================================
# 3. 核心配置获取函数 (任务调度接口)
# ==========================================================

def get_all_channels() -> List[Dict[str, Any]]:
    """从数据库获取所有栏目的完整配置，并将其扁平化。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, site_name, channel_name, url, base_link_url, mode, config_json FROM Channel")
    
    channels = []
    for row in cursor.fetchall():
        config = json.loads(row['config_json'])
        
        # 将数据库独立列数据和 JSON 配置数据合并，形成完整的扁平化任务字典
        channels.append({
            'channel_id': row['id'],
            'site_name': row['site_name'],
            'channel_name': row['channel_name'],
            'url': row['url'],                # 主 URL (独立列)
            'base_link_url': row['base_link_url'], # 键名与配置一致
            'mode': row['mode'],
            **config                          # 展开 JSON 中的内容 (包含 url_list, max_count, html_config/api_config 等)
        })
        
    conn.close()
    return channels


# ==========================================================
# 4. 搜索查询函数 (供 search_service.py 调用)
# ==========================================================

def get_notifications_by_keyword_sync(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    同步函数：根据关键词搜索 Notification 表的 title 字段。
    
    :param keyword: 搜索关键词。
    :param limit: 返回结果限制。
    :return: 结果字典列表。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 核心 SQL 查询
    sql = """
        SELECT 
            title, 
            link, 
            published_date AS date, 
            site_name,
            channel_name
        FROM 
            Notification n
        JOIN 
            Channel c ON n.channel_id = c.id
        WHERE 
            n.title LIKE ?
        ORDER BY 
            n.push_time DESC 
        LIMIT 
            ?
    """
    
    # 使用 % 符号进行模糊匹配，防止 SQL 注入
    params = (f'%{keyword}%', limit)
    
    cursor.execute(sql, params)
    
    # 将 sqlite3.Row 对象转换为标准的 dict
    results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return results