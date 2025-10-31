from typing import List, Dict, Any
from database.utils_db import get_db_connection
import sqlite3
import jieba
import re

# ----------------------------------------------------------------------
# 1. 核心工具函数：中文分词与 FTS5 查询构建
# ----------------------------------------------------------------------

def segment_text(text: str) -> str:
    """使用 Jieba 对文本进行分词，并用空格连接，以便 FTS5 索引。"""
    # 使用全模式（cut_all=True）来提高分词的召回率。
    return " ".join(jieba.cut(text.strip(), cut_all=True))

def _process_term(term: str) -> str:
    """对纯文本进行分词、模糊化，并用 AND 连接后，用括号包裹。"""
    term = term.strip()
    if not term:
        return ""
    
    # 1. 分词
    segmented_terms = segment_text(term)
    
    # 2. 模糊化 (加 *)
    fts_terms = [f'{t}*' for t in segmented_terms.split() if t and len(t.strip()) > 0]
    
    if not fts_terms:
        return ""
        
    # 3. 结果: (词1* AND 词2*)
    return f"({' AND '.join(fts_terms)})"

# ----------------------------------------------------------------------
# 2. parse_to_fts5_query 函数 (核心修正)
# ----------------------------------------------------------------------
def parse_to_fts5_query(keyword: str) -> str:
    """
    将用户输入的关键词转换为 FTS5 的 MATCH 查询字符串。
    处理复杂结构：使用递归/迭代分割，对纯文本进行分词和模糊化。
    """
    keyword = keyword.strip()
    if not keyword:
        return ""
    
    # 定义需要保留的 FTS5 特殊语法和分隔符 (AND/OR/NOT, 括号, 引号)
    # 使用正则表达式将整个查询分割成纯文本、布尔运算符和括号
    # 使用 () 包裹的 regex groups 会被保留在结果列表中
    
    operators_and_structs = re.split(r'(\bAND\b|\bOR\b|\bNOT\b|[()]|"[^"]*")', keyword, flags=re.IGNORECASE)
    
    final_query_parts: List[str] = []
    
    for part in operators_and_structs:
        part = part.strip()
        if not part:
            continue
            
        # 1. 检查是否是 FTS5 结构/操作符 (保留)
        if re.match(r'^(AND|OR|NOT|[()]|"[^"]*?")$', part, re.IGNORECASE):
            # 操作符、括号或引号包裹的短语直接保留
            final_query_parts.append(part)
        else:
            # 2. 纯中文搜索词（进行分词和模糊化）
            processed_term = _process_term(part)
            if processed_term:
                final_query_parts.append(processed_term)
            
    # 将所有的部分重新连接起来，返回最终的 FTS5 MATCH 字符串
    return " ".join(final_query_parts)

# ----------------------------------------------------------------------
# 2. 搜索操作：异步调用中的同步执行函数
# ----------------------------------------------------------------------

def search_notifications_sync(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    执行基于 FTS5 的同步全文搜索操作。
    此函数设计用于被 asyncio.run_in_executor 调用。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fts_query = parse_to_fts5_query(keyword)
    
    if not fts_query:
        conn.close()
        return []

    # 核心 FTS5 查询：从 FTS5 表查询，通过 fingerprint 连接回主表，并使用 BM25 评分排序。
    sql = """
        SELECT 
            n.title, 
            n.link, 
            n.published_date AS date, 
            c.site_name,
            c.channel_name
        FROM 
            Notification_fts fts  
        JOIN 
            Notification n ON fts.fingerprint = n.fingerprint
        JOIN 
            Channel c ON n.channel_id = c.id
        WHERE 
            fts.title MATCH ?  
        ORDER BY 
            rank DESC  
        LIMIT 
            ?
    """
    
    params = (fts_query, limit)
    
    try:
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        # 实际项目中应记录日志
        print(f"[FTS5 Search ERROR] Query: '{fts_query}', Error: {e}")
        return []
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 3. 索引操作：供 database.py 调用的同步 FTS5 写入函数
# ----------------------------------------------------------------------

def update_fts5_index_sync(cursor: sqlite3.Cursor, fingerprint: str, title: str):
    """
    优化后的 FTS5 索引写入函数：只接受 cursor，移除冗余 DELETE。
    """
    
    # 插入新记录，使用分词后的文本
    segmented_title = segment_text(title)
    
    # 使用 INSERT OR IGNORE 确保 FTS5 表的写入的健壮性。
    cursor.execute("""
        INSERT OR IGNORE INTO Notification_fts (fingerprint, title) 
        VALUES (?, ?)
    """, (fingerprint, segmented_title))