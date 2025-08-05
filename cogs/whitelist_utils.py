
from database import db

def get_whitelist(guild_id):
    return db.get_whitelist(guild_id)

def save_whitelist(guild_id, users):
    db.save_whitelist(guild_id, users)

def add_to_whitelist(guild_id, user_id):
    whitelist = get_whitelist(guild_id)
    if user_id not in whitelist:
        whitelist.append(user_id)
        save_whitelist(guild_id, whitelist)

def remove_from_whitelist(guild_id, user_id):
    whitelist = get_whitelist(guild_id)
    if user_id in whitelist:
        whitelist.remove(user_id)
        save_whitelist(guild_id, whitelist)

def is_whitelisted(guild_id, user_id):
    return user_id in get_whitelist(guild_id)
