import json
from tortoise import Tortoise, run_async
from models import User, Character

async def migrate():
    await Tortoise.init(
        db_url="postgresql://waifuverse_user:sz2IdWdly0wLzTYCEv0yIJBueK2i9U9t@dpg-d21ncpe3jp1c73830jp0-a/waifuverse?sslmode=require",  # ← UPDATE ME
        modules={"models": ["models"]},
    )
    await Tortoise.generate_schemas()

    with open("data/user.json", "r") as f:
        data = json.load(f)

    for discord_id, user_data in data.items():
        user, created = await User.get_or_create(
            discord_id=discord_id,
            defaults={
                "name": user_data.get("name", ""),
                "gold": user_data.get("gold", 0),
                "gems": user_data.get("gems", 0),
                "affection": user_data.get("affection", 0),
                "summon_count": user_data.get("summon_count", 0),
                "level": user_data.get("level", 1),
                "xp": user_data.get("xp", 0),
                "pity_counter": user_data.get("pity_counter", 0),
            },
        )

        for waifu in user_data.get("claimed_waifus", []):
            await Character.create(
                name=waifu["name"],
                level=waifu.get("level", 1),
                atk=waifu.get("atk", 10),
                hp=waifu.get("hp", 100),
                crit=waifu.get("crit", 0),
                exp=waifu.get("exp", 0),
                owner=user,
            )

    print("✅ Migration complete.")
    await Tortoise.close_connections()

run_async(migrate())
