using System.Collections.Generic;
using UnityEngine;

// Which sound each monster (and boss) makes when it appears, attacks and dies.
// `kind` is the monster / boss prefab name (EnemyHealth.kind).
public static class MonsterVoice
{
    static readonly Dictionary<string, string> EmergeSounds = new Dictionary<string, string>
    {
        { "Slime", "SlimeHop" }, { "Goblin", "GoblinCackle" }, { "Zombie", "ZombieGroan" }, { "Kobold", "KoboldYip" },
        { "Skeleton", "SkeletonRattle" }, { "Orc", "OrcGrunt" }, { "Bat", "BatSqueak" }, { "Ghost", "GhostWoo" },
        { "Mimic", "MimicReveal" }, { "Necromancer", "NecroChant" }, { "Spirit", "NecroRaise" },
        { "KingSlime", "KingSlimeRoar" }, { "AncientLich", "LichRoar" }, { "OrcWarlord", "OrcWarlordRoar" },
    };

    static readonly Dictionary<string, string> AttackSounds = new Dictionary<string, string>
    {
        { "Goblin", "GoblinCackle" }, { "Kobold", "KoboldHiss" }, { "Skeleton", "BowTwang" }, { "Orc", "OrcShout" },
        { "Bat", "BatSqueak" }, { "Mimic", "MimicChomp" }, { "Necromancer", "NecroChant" }, { "Ghost", "GhostWoo" },
        { "Spirit", "SpiritShot" },
    };

    static readonly Dictionary<string, string> DeathSounds = new Dictionary<string, string>
    {
        { "Slime", "SlimeDie" }, { "Goblin", "GoblinDie" }, { "Zombie", "ZombieDie" }, { "Kobold", "KoboldDie" },
        { "Skeleton", "SkeletonDie" }, { "Orc", "OrcDie" }, { "Bat", "BatDie" }, { "Ghost", "GhostDie" },
        { "Mimic", "MimicDie" }, { "Necromancer", "NecroDie" }, { "Spirit", "GhostDie" },
        { "KingSlime", "KingSlimeDie" }, { "AncientLich", "LichDie" }, { "OrcWarlord", "OrcWarlordDie" },
    };

    public static void Emerge(string kind, float pitch = 1f, float volume = 0.7f) => Say(EmergeSounds, kind, pitch, volume);
    public static void Attack(string kind, float pitch = 1f, float volume = 0.8f) => Say(AttackSounds, kind, pitch, volume);

    public static void Die(string kind, float pitch = 1f)
    {
        if (!Say(DeathSounds, kind, pitch, 0.9f)) Audio.Play("MonsterDie", 0.8f, pitch);
    }

    static bool Say(Dictionary<string, string> table, string kind, float pitch, float volume)
    {
        if (string.IsNullOrEmpty(kind) || !table.TryGetValue(kind, out var sound)) return false;
        Audio.Play(sound, volume, pitch);
        return true;
    }
}
