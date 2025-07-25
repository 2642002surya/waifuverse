import os
import json
from tortoise import Tortoise, run_async
from models import CharacterTemplate, WeaponTemplate  # Adjust if in different path

CHARACTER_DIR = "characters"
WEAPON_DIR = "store/weapons"

async def init():
    await Tortoise.init(
        db_url="postgres://user:password@localhost:5432/dbname",  # replace with your actual DB info
        modules={"models": ["db.models"]},
    )
    await Tortoise.generate_schemas()

async def import_characters():
    for file in os.listdir(CHARACTER_DIR):
        if file.endswith(".json"):
            with open(os.path.join(CHARACTER_DIR, file), "r", encoding="utf-8") as f:
                data = json.load(f)

            name = data.get("name")
            folder_prefix = file.replace(".json", "")  # e.g., amaterasu

            await CharacterTemplate.get_or_create(
                name=name,
                defaults={
                    "potential": data.get("potential", 0),
                    "main_attribute": data.get("main_attribute", ""),
                    "exclusive_relic": data.get("exclusive_relic", ""),
                    "temple_description": data.get("temple_description", ""),
                    "active_skills": data.get("active_skills", []),
                    "passive_skills": data.get("passive_skills", []),
                    "fate": data.get("fate", []),
                    "gallery": data.get("gallery", []),
                    "categories": data.get("categories", []),
                    "image_folder": folder_prefix
                }
            )

async def import_weapons():
    for file in os.listdir(WEAPON_DIR):
        if file.endswith(".json"):
            with open(os.path.join(WEAPON_DIR, file), "r", encoding="utf-8") as f:
                data = json.load(f)

            name = data.get("name")
            image_name = file.replace(".json", ".webp")

            await WeaponTemplate.get_or_create(
                name=name,
                defaults={
                    "rarity": data.get("rarity", "Common"),
                    "stats": data.get("stats", {}),
                    "description": data.get("description", ""),
                    "image_path": os.path.join(WEAPON_DIR, image_name)
                }
            )

async def main():
    await init()
    await import_characters()
    await import_weapons()
    await Tortoise.close_connections()

if __name__ == "__main__":
    run_async(main())
