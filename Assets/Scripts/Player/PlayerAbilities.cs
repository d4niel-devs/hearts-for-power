using System;
using UnityEngine;

public enum AbilityId { Dash, Bomb, Sword, MagicBolt, Fireball, IceShards, Lightning }

// Everything the knight can gain from pedestals. Taking an item you already have levels it up.
public class AbilityInfo
{
    public AbilityId id;
    public string name;
    public string key;        // shown on the ability bar
    public string icon;       // Resources/Sprites path
    public bool isSpell;      // spells come from boss pedestals and cost a whole heart container
    public string[] levels;   // what each level does (index 0 = level 1)

    public int MaxLevel => levels.Length;
    public int CostHalfHearts => isSpell ? 2 : 1;
}

// Tracks which abilities the knight has, their levels and cooldowns, and fires them:
// E bomb, Q magic bolt, R fireball, F ice shards, C lightning (dash lives in PlayerMovement, sword in SwordFollow).
// Spells always fire in the direction the knight is facing.
public class PlayerAbilities : MonoBehaviour
{
    public static readonly AbilityInfo[] All =
    {
        new AbilityInfo { id = AbilityId.Dash, name = "Shadow Dash", key = "SHIFT", icon = "Items/Icon_Dash", levels = new[] {
            "SHIFT: dash a short way. Untouchable while dashing.",
            "Dash recharges much faster.",
            "Dashing through enemies cuts them for 15 damage." } },
        new AbilityInfo { id = AbilityId.Bomb, name = "Bomb", key = "E", icon = "Items/Icon_Bomb", levels = new[] {
            "E: drop a bomb that blasts nearby enemies for 40.",
            "Bigger blast for 60 damage, refills faster.",
            "Huge blast for 90 damage." } },
        new AbilityInfo { id = AbilityId.Sword, name = "Stronger Sword", key = "SPACE", icon = "Items/Icon_Sword", levels = new[] {
            "Sword deals +6 damage, reaches further and swings wider.",
            "Sword deals +6 more damage and reaches further.",
            "Sword deals +6 more damage and reaches further.",
            "Sword deals +6 more damage and reaches further." } },
        new AbilityInfo { id = AbilityId.MagicBolt, name = "Magic Bolt", key = "Q", icon = "Items/Icon_MagicBolt", isSpell = true, levels = new[] {
            "Q: fire a fast magic bolt for 12 damage.",
            "Bolts hit for 18 and fire faster.",
            "Fire two bolts at once." } },
        new AbilityInfo { id = AbilityId.Fireball, name = "Fireball", key = "R", icon = "Items/Icon_Fireball", isSpell = true, levels = new[] {
            "R: hurl a fireball that explodes (20 hit + 25 blast).",
            "Bigger, stronger explosion.",
            "Massive explosion (34 hit + 50 blast)." } },
        new AbilityInfo { id = AbilityId.IceShards, name = "Ice Shards", key = "F", icon = "Items/Icon_IceShards", isSpell = true, levels = new[] {
            "F: fire 3 ice shards that slow enemies.",
            "Fire 5 shards.",
            "Shards hit harder and freeze for longer." } },
        new AbilityInfo { id = AbilityId.Lightning, name = "Lightning", key = "C", icon = "Items/Icon_Lightning", isSpell = true, levels = new[] {
            "C: strike every enemy in a line for 25.",
            "Strikes for 35 and recharges faster.",
            "Strikes for 50." } },
    };

    public static AbilityInfo Info(AbilityId id) => All[(int)id];

    public event Action Changed;

    private readonly int[] levels = new int[All.Length];
    private readonly float[] readyAt = new float[All.Length];
    private readonly float[] cooldownLength = new float[All.Length];

    private PlayerMovement movement;
    private PlayerHealth health;

    void Awake()
    {
        movement = GetComponent<PlayerMovement>();
        health = GetComponent<PlayerHealth>();
    }

    public int Level(AbilityId id) => levels[(int)id];
    public bool Has(AbilityId id) => levels[(int)id] > 0;
    public bool IsMaxed(AbilityId id) => levels[(int)id] >= Info(id).MaxLevel;

    public void LevelUp(AbilityId id)
    {
        if (IsMaxed(id)) return;
        levels[(int)id]++;
        Changed?.Invoke();
    }

    // 1 = just used, 0 = ready
    public float CooldownFraction(AbilityId id)
    {
        int i = (int)id;
        if (cooldownLength[i] <= 0f) return 0f;
        return Mathf.Clamp01((readyAt[i] - Time.time) / cooldownLength[i]);
    }

    bool TryUse(AbilityId id, float cooldown)
    {
        int i = (int)id;
        if (levels[i] == 0 || Time.time < readyAt[i]) return false;
        readyAt[i] = Time.time + cooldown;
        cooldownLength[i] = cooldown;
        return true;
    }

    // ---------------------------------------------------------------- stats per level
    static float ByLevel(int level, params float[] values) => values[Mathf.Clamp(level, 0, values.Length - 1)];

    public float DashCooldown => ByLevel(Level(AbilityId.Dash), 0f, 1.0f, 0.55f, 0.55f);
    public int DashDamage => Level(AbilityId.Dash) >= 3 ? 15 : 0;
    public int SwordBonusDamage => 6 * Level(AbilityId.Sword);
    public float SwordArcBonus => 12f * Level(AbilityId.Sword);
    public float SwordLengthMultiplier => 1f + 0.12f * Level(AbilityId.Sword);

    public bool TryUseDash() => TryUse(AbilityId.Dash, DashCooldown);

    // ---------------------------------------------------------------- input
    void Update()
    {
        if (GameManager.InputLocked || (health != null && health.IsDead)) return;

        if (Input.GetKeyDown(KeyCode.E)) UseBomb();
        if (Input.GetKeyDown(KeyCode.Q)) UseMagicBolt();
        if (Input.GetKeyDown(KeyCode.R)) UseFireball();
        if (Input.GetKeyDown(KeyCode.F)) UseIceShards();
        if (Input.GetKeyDown(KeyCode.C)) UseLightning();
    }

    Vector2 Facing => movement != null ? movement.Facing : Vector2.down;
    Vector2 CastPoint => (Vector2)transform.position + new Vector2(0f, -0.15f) + Facing * 0.5f;

    void UseBomb()
    {
        int lv = Level(AbilityId.Bomb);
        if (!TryUse(AbilityId.Bomb, ByLevel(lv, 0f, 4f, 3f, 2.5f))) return;
        Audio.Play("BombPlace");
        Bomb.Drop((Vector2)transform.position + new Vector2(0f, -0.4f), (int)ByLevel(lv, 0, 40, 60, 90), ByLevel(lv, 0f, 1.6f, 2.1f, 2.7f));
    }

    void UseMagicBolt()
    {
        int lv = Level(AbilityId.MagicBolt);
        if (!TryUse(AbilityId.MagicBolt, ByLevel(lv, 0f, 0.45f, 0.32f, 0.32f))) return;
        int damage = (int)ByLevel(lv, 0, 12, 18, 18);
        Audio.Play("SpellMagicBolt", 0.6f);
        Vector2 side = new Vector2(-Facing.y, Facing.x);
        if (lv >= 3)
        {
            Bolt(CastPoint + side * 0.22f, damage);
            Bolt(CastPoint - side * 0.22f, damage);
        }
        else Bolt(CastPoint, damage);
    }

    void Bolt(Vector2 from, int damage)
    {
        var p = Projectile.Spawn("Effects/MagicBolt", from, Facing * 14f, damage, false);
        p.puffColor = new Color(0.75f, 0.5f, 1f);
        p.knockback = 2.5f;
    }

    void UseFireball()
    {
        int lv = Level(AbilityId.Fireball);
        if (!TryUse(AbilityId.Fireball, ByLevel(lv, 0f, 1.4f, 1.2f, 1.0f))) return;
        Audio.Play("SpellFireball", 0.8f);
        var p = Projectile.Spawn("Effects/Fireball", CastPoint, Facing * 7.5f, (int)ByLevel(lv, 0, 20, 26, 34), false);
        p.radius = 0.3f;
        p.puffColor = new Color(1f, 0.6f, 0.2f);
        p.explodeRadius = ByLevel(lv, 0f, 1.3f, 1.8f, 2.4f);
        p.explodeDamage = (int)ByLevel(lv, 0, 25, 35, 50);
        p.explodeColor = new Color(1f, 0.55f, 0.15f);
        p.spin = true;
    }

    void UseIceShards()
    {
        int lv = Level(AbilityId.IceShards);
        if (!TryUse(AbilityId.IceShards, 1.0f)) return;
        int count = (int)ByLevel(lv, 0, 3, 5, 5);
        Audio.Play("SpellIceShards", 0.7f);
        int damage = (int)ByLevel(lv, 0, 8, 8, 12);
        float slowTime = ByLevel(lv, 0f, 2f, 2f, 3.5f);
        float baseAngle = Mathf.Atan2(Facing.y, Facing.x) * Mathf.Rad2Deg;
        const float spread = 14f;
        for (int i = 0; i < count; i++)
        {
            float angle = (baseAngle + (i - (count - 1) / 2f) * spread) * Mathf.Deg2Rad;
            var dir = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
            var p = Projectile.Spawn("Effects/IceShard", CastPoint, dir * 11f, damage, false);
            p.slowFactor = 0.45f;
            p.slowTime = slowTime;
            p.puffColor = new Color(0.7f, 0.9f, 1f);
            p.knockback = 1.5f;
        }
    }

    void UseLightning()
    {
        int lv = Level(AbilityId.Lightning);
        if (!TryUse(AbilityId.Lightning, ByLevel(lv, 0f, 2.0f, 1.5f, 1.5f))) return;
        Audio.Play("SpellLightning", 0.8f);
        LightningStrike.Fire(CastPoint, Facing, (int)ByLevel(lv, 0, 25, 35, 50));
    }
}
