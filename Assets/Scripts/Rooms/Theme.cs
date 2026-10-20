using System.Collections.Generic;
using UnityEngine;

public enum FloorTheme { Dungeon, Crypt, Caves }

// Which art set the rooms of the current floor use. Floors cycle Mossy Dungeon -> Bone Crypt ->
// Lava Caves (the same cycle as the bosses). Room art lives in Resources/Sprites/Room (the dungeon)
// and Resources/Sprites/Room/<Theme>/ with the same file names (made by room_art.py); anything a
// theme doesn't have falls back to the dungeon version.
public static class Theme
{
    public static FloorTheme Current { get; private set; } = FloorTheme.Dungeon;

    static readonly Dictionary<string, string> resolved = new Dictionary<string, string>();

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetStatics()
    {
        Current = FloorTheme.Dungeon;
        resolved.Clear();
    }

    public static FloorTheme ForFloor(int floor) => (FloorTheme)((floor - 1) % 3);

    public static void Set(FloorTheme theme)
    {
        if (theme == Current) return;
        Current = theme;
        resolved.Clear();
    }

    public static string DisplayName(FloorTheme theme) => theme switch
    {
        FloorTheme.Crypt => "The Bone Crypt",
        FloorTheme.Caves => "The Lava Caves",
        _ => "The Mossy Dungeon",
    };

    public static string Music(FloorTheme theme) => theme switch
    {
        FloorTheme.Crypt => "Crypt",
        FloorTheme.Caves => "Caves",
        _ => "Dungeon",
    };

    // Lava pits glow and pulse
    public static bool GlowingPits => Current == FloorTheme.Caves;

    // "Rock_0" -> "Room/Crypt/Rock_0" when the crypt has its own, else "Room/Rock_0" (for Fx.Sprite)
    public static string Path(string name)
    {
        if (resolved.TryGetValue(name, out var path)) return path;
        path = "Room/" + name;
        if (Current != FloorTheme.Dungeon)
        {
            string themed = $"Room/{Current}/{name}";
            if (Resources.Load<Sprite>("Sprites/" + themed) != null) path = themed;
        }
        resolved[name] = path;
        return path;
    }

    public static Sprite Sprite(string name) => Fx.Sprite(Path(name));

    // How likely each monster is to be picked for a room on this theme (1 = normal)
    public static float MonsterWeight(string monster) => Current switch
    {
        FloorTheme.Dungeon => monster switch { "Slime" => 2f, "Goblin" => 2f, "Zombie" => 1.5f, "Bat" => 1.5f, _ => 0.6f },
        FloorTheme.Crypt => monster switch { "Skeleton" => 2.5f, "Ghost" => 2f, "Zombie" => 2f, "Necromancer" => 1.5f, "Bat" => 0.8f, _ => 0.5f },
        _ => monster switch { "Orc" => 2f, "Kobold" => 2.5f, "Goblin" => 1.5f, "Bat" => 1.5f, _ => 0.5f },
    };
}
