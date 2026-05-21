import os
import time
import random
import threading
import json
from typing import List, Optional, Dict, Any

_lock = threading.Lock()
_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        with _lock:
            if _db_instance is None:
                from pymongo import MongoClient
                uri = os.environ.get("MONGODB_URI", "")
                if not uri:
                    raise RuntimeError(
                        "MONGODB_URI environment variable is not set.\n"
                        "Set it in Railway: Settings > Variables > MONGODB_URI"
                    )
                client = MongoClient(uri, serverSelectionTimeoutMS=15000)
                client.server_info()
                db = client["boostbot"]
                _ensure_indexes(db)
                _db_instance = db
    return _db_instance

def _ensure_indexes(db):
    try:
        db.tokens.create_index([("type", 1), ("added_at", 1)])
        db.keys.create_index([("key", 1)], unique=True)
        db.used_keys.create_index([("key", 1)])
        db.oauth_tokens.create_index([("raw_token", 1)], unique=True)
        db.proxies.create_index([("proxy", 1)], unique=True)
    except Exception:
        pass

# ── Token operations (replaces 1m.txt / 3m.txt) ───────────────────────────────

def token_type(filename: str) -> str:
    return "1m" if "1m" in filename else "3m"

def getStock_db(ttype: str) -> List[str]:
    docs = list(get_db().tokens.find({"type": ttype}, {"_id": 0, "token": 1}))
    result = []
    for d in docs:
        t = d["token"]
        result.append(t.split(":")[2] if t.count(":") >= 2 else t)
    return result

def getStock_Auto_db(ttype: str, num: int) -> List[str]:
    db = get_db()
    docs = list(db.tokens.find({"type": ttype}).limit(num))
    result = []
    for doc in docs:
        t = doc["token"]
        result.append(t.split(":")[2] if t.count(":") >= 2 else t)
        db.tokens.delete_one({"_id": doc["_id"]})
    return result

def remove_db(raw_token: str, ttype: str):
    db = get_db()
    if db.tokens.delete_one({"token": raw_token, "type": ttype}).deleted_count == 0:
        for doc in db.tokens.find({"type": ttype}):
            t = doc["token"]
            r = t.split(":")[2] if t.count(":") >= 2 else t
            if r.strip() == raw_token.strip():
                db.tokens.delete_one({"_id": doc["_id"]})
                return

def add_tokens_db(ttype: str, token_list: List[str]) -> int:
    db = get_db()
    added = 0
    existing = {d["token"] for d in db.tokens.find({"type": ttype}, {"_id": 0, "token": 1})}
    for t in token_list:
        if t and t not in existing:
            try:
                db.tokens.insert_one({"token": t, "type": ttype, "added_at": time.time()})
                added += 1
                existing.add(t)
            except Exception:
                pass
    return added

def clear_tokens_db(ttype: str):
    get_db().tokens.delete_many({"type": ttype})

def count_tokens_db(ttype: str) -> int:
    return get_db().tokens.count_documents({"type": ttype})

def get_all_token_lines_db(ttype: str) -> List[str]:
    docs = list(get_db().tokens.find({"type": ttype}, {"_id": 0, "token": 1}))
    return [d["token"] for d in docs]

def remove_token_by_raw_or_line(token_val: str, ttype: str):
    db = get_db()
    if db.tokens.delete_one({"token": token_val, "type": ttype}).deleted_count:
        return
    for doc in db.tokens.find({"type": ttype}):
        t = doc["token"]
        r = t.split(":")[2] if t.count(":") >= 2 else t
        if r.strip() == token_val.strip():
            db.tokens.delete_one({"_id": doc["_id"]})
            return

# ── Key operations (replaces keys.json) ──────────────────────────────────────

def load_keys() -> List[Dict]:
    return list(get_db().keys.find({}, {"_id": 0}))

def save_keys(keys: List[Dict]):
    db = get_db()
    db.keys.delete_many({})
    if keys:
        db.keys.insert_many([{k: v for k, v in e.items() if k != "_id"} for e in keys])

def get_key(key_str: str) -> Optional[Dict]:
    return get_db().keys.find_one({"key": key_str}, {"_id": 0})

def add_key_entry(entry: Dict):
    e = {k: v for k, v in entry.items() if k != "_id"}
    try:
        get_db().keys.insert_one(e)
    except Exception:
        pass

def add_keys_bulk(entries: List[Dict]):
    if not entries:
        return
    db = get_db()
    for e in entries:
        clean = {k: v for k, v in e.items() if k != "_id"}
        try:
            db.keys.insert_one(clean)
        except Exception:
            pass

def delete_key_entry(key_str: str):
    get_db().keys.delete_one({"key": key_str})

def clear_all_keys():
    get_db().keys.delete_many({})

def update_key_amount(key_str: str, new_amount: int):
    get_db().keys.update_one({"key": key_str}, {"$set": {"amount": new_amount}})

def fetch_from_key_db(key_str: str):
    k = get_key(key_str)
    if k:
        return k["amount"], k["month"]
    raise KeyError(f"Key not found: {key_str}")

def mark_key_used_db(key, month, amount, guild_id, successful, failed, time_taken):
    db = get_db()
    db.keys.delete_one({"key": key})
    db.used_keys.insert_one({
        "key": key, "month": month, "amount": amount,
        "guild_id": guild_id, "successful": successful,
        "failed": failed, "time_taken": time_taken,
        "used_at": time.time()
    })

def get_used_keys() -> List[Dict]:
    return list(get_db().used_keys.find({}, {"_id": 0}))

def clear_used_keys():
    get_db().used_keys.delete_many({})

def is_key_used(key_str: str) -> bool:
    return get_db().used_keys.find_one({"key": key_str}) is not None

# ── OAuth token operations (replaces oauth_tokens.json) ───────────────────────

def get_stored_oauth(raw_token: str) -> Optional[str]:
    try:
        doc = get_db().oauth_tokens.find_one({"raw_token": raw_token})
        if doc and time.time() - doc.get("obtained_at", 0) < 518400:
            return doc.get("access_token")
    except Exception:
        pass
    return None

def store_oauth(raw_token: str, user_id: str, access_token: str):
    try:
        get_db().oauth_tokens.update_one(
            {"raw_token": raw_token},
            {"$set": {"raw_token": raw_token, "user_id": user_id,
                      "access_token": access_token, "obtained_at": time.time()}},
            upsert=True
        )
    except Exception:
        pass

def get_all_oauth() -> Dict:
    docs = list(get_db().oauth_tokens.find({}, {"_id": 0}))
    return {
        d["raw_token"]: {
            "user_id": d.get("user_id"),
            "access_token": d.get("access_token"),
            "obtained_at": d.get("obtained_at", 0)
        }
        for d in docs
    }

# ── Proxy operations (replaces proxies.txt) ───────────────────────────────────

def get_random_proxy() -> Optional[str]:
    proxies_env = os.environ.get("PROXIES", "")
    if proxies_env:
        lines = [l.strip() for l in proxies_env.splitlines() if l.strip()]
        if lines:
            return random.choice(lines)
    try:
        db = get_db()
        count = db.proxies.count_documents({})
        if count > 0:
            skip = random.randint(0, count - 1)
            doc = list(db.proxies.find().skip(skip).limit(1))
            if doc:
                return doc[0].get("proxy")
    except Exception:
        pass
    try:
        with open("data/proxies.txt", "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if lines:
            return random.choice(lines)
    except Exception:
        pass
    return None

def add_proxies(proxy_list: List[str]) -> int:
    db = get_db()
    added = 0
    for p in proxy_list:
        if p:
            try:
                db.proxies.insert_one({"proxy": p})
                added += 1
            except Exception:
                pass
    return added

# ── Boost log operations (replaces success.txt / failed_boosts.txt) ───────────

def log_boost_success(token: str, guild_id: str = ""):
    try:
        get_db().boost_logs.insert_one({
            "token": token, "guild_id": guild_id,
            "status": "success", "timestamp": time.time()
        })
    except Exception:
        pass

def log_boost_failed(token: str, guild_id: str = ""):
    try:
        get_db().boost_logs.insert_one({
            "token": token, "guild_id": guild_id,
            "status": "failed", "timestamp": time.time()
        })
    except Exception:
        pass

def get_boost_logs(status: Optional[str] = None, limit: int = 500) -> List[Dict]:
    query = {}
    if status:
        query["status"] = status
    return list(get_db().boost_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit))
