from tortoise import fields
from tortoise.models import Model

# ────────────────────────────────
# 👤 User Profile & Progress
# ────────────────────────────────
class User(Model):
    id = fields.BigIntField(pk=True)
    discord_id = fields.CharField(max_length=20, unique=True)
    name = fields.TextField()
    
    gold = fields.IntField(default=0)
    gems = fields.IntField(default=0)
    affection = fields.IntField(default=0)

    level = fields.IntField(default=1)
    xp = fields.IntField(default=0)
    summon_count = fields.IntField(default=0)
    pity_counter = fields.IntField(default=0)

    # Relationships
    waifus: fields.ReverseRelation["Character"]
    relics: fields.ReverseRelation["Relic"]
    cooldowns: fields.ReverseRelation["Cooldown"]
    unlocks: fields.ReverseRelation["Unlock"]


# ────────────────────────────────
# 🧙 Waifus (Claimed Characters)
# ────────────────────────────────
class Character(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)

    level = fields.IntField(default=1)
    hp = fields.IntField(default=100)
    atk = fields.IntField(default=10)
    crit = fields.IntField(default=0)
    exp = fields.IntField(default=0)

    potential = fields.JSONField(default=dict)  # e.g., {"luck": 2, "evasion": 1}

    # Foreign Keys
    owner = fields.ForeignKeyField("models.User", related_name="waifus")
    relic = fields.ForeignKeyField("models.Relic", null=True, related_name="equipped_to")


# ────────────────────────────────
# 🗡️ Relics (Equippable Items)
# ────────────────────────────────
class Relic(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    quality = fields.CharField(max_length=20)
    attributes = fields.JSONField()  # e.g., {"atk": 10, "crit": 2}

    level = fields.IntField(default=1)
    awaken = fields.IntField(default=0)
    image = fields.CharField(max_length=255, null=True)

    # Foreign Keys
    user = fields.ForeignKeyField("models.User", related_name="relics")
    equipped_to: fields.ReverseRelation["Character"]


# ────────────────────────────────
# ⏳ Cooldown Tracking
# ────────────────────────────────
class Cooldown(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="cooldowns")

    command = fields.CharField(max_length=50)     # e.g., "daily", "summon"
    last_used = fields.DatetimeField()


# ────────────────────────────────
# 🔓 Unlocks (Progress Features)
# ────────────────────────────────
class Unlock(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="unlocks")

    name = fields.CharField(max_length=100)
    unlocked_at = fields.DatetimeField(auto_now_add=True)


# ────────────────────────────────
# 🧬 Character Template (Master Data)
# ────────────────────────────────
class CharacterTemplate(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    potential = fields.IntField()
    main_attribute = fields.CharField(max_length=20)
    exclusive_relic = fields.CharField(max_length=100)
    temple_description = fields.TextField()

    active_skills = fields.JSONField()
    passive_skills = fields.JSONField()
    fate = fields.JSONField()
    gallery = fields.JSONField()
    categories = fields.JSONField()

    image_path = fields.CharField(max_length=255, null=True)


# ────────────────────────────────
# ⚔️ Weapon Template (Master Data)
# ────────────────────────────────
class WeaponTemplate(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    rarity = fields.CharField(max_length=20)
    stats = fields.JSONField()
    description = fields.TextField()
    image_path = fields.CharField(max_length=255, null=True)
