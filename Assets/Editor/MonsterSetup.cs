using System.Linq;
using UnityEditor;
using UnityEngine;

// Rebuilds a prefab for every monster in Assets/Animations/Monsters into Assets/Resources/Monsters,
// and for the bosses in Assets/Animations/Bosses into Assets/Resources/Bosses,
// where the GameManager loads them from when filling rooms. Stats (health, speed, behaviour)
// are set by the GameManager at spawn time, so the prefabs only hold the look and physics.
// Prefabs that don't exist yet are built automatically when the editor loads, so hand edits to
// existing prefabs (e.g. the Orc Warlord's box collider) are kept.
// Menu: Hearts for Power > Build Missing Monster Prefabs / Rebuild ALL Monster Prefabs (overwrites edits)
[InitializeOnLoad]
public static class MonsterSetup
{
    const string AnimRoot = "Assets/Animations/Monsters";
    const string PrefabRoot = "Assets/Resources/Monsters";
    const string BossAnimRoot = "Assets/Animations/Bosses";
    const string BossPrefabRoot = "Assets/Resources/Bosses";

    struct MonsterDef
    {
        public string name;
        public Vector2 colliderSize;
        public Vector2 colliderOffset;
        public CapsuleDirection2D direction;
        public bool boss;
        public BossType bossType;
    }

    // Collider sizes are in sprite units (one 32px frame = 1 unit, before the 2x scale)
    static readonly MonsterDef[] Monsters =
    {
        new MonsterDef { name = "Slime",    colliderSize = new Vector2(0.75f, 0.4f),  colliderOffset = new Vector2(0f, -0.27f), direction = CapsuleDirection2D.Horizontal },
        new MonsterDef { name = "Goblin",   colliderSize = new Vector2(0.45f, 0.6f),  colliderOffset = new Vector2(0f, -0.12f), direction = CapsuleDirection2D.Vertical },
        new MonsterDef { name = "Kobold",   colliderSize = new Vector2(0.45f, 0.65f), colliderOffset = new Vector2(0f, -0.1f),  direction = CapsuleDirection2D.Vertical },
        new MonsterDef { name = "Skeleton", colliderSize = new Vector2(0.45f, 0.75f), colliderOffset = new Vector2(0f, -0.05f), direction = CapsuleDirection2D.Vertical },
        new MonsterDef { name = "Zombie",   colliderSize = new Vector2(0.5f, 0.8f),   colliderOffset = new Vector2(0f, -0.05f), direction = CapsuleDirection2D.Vertical },
        new MonsterDef { name = "Orc",      colliderSize = new Vector2(0.6f, 0.75f),  colliderOffset = new Vector2(0f, -0.05f), direction = CapsuleDirection2D.Vertical },
        new MonsterDef { name = "Bat",      colliderSize = new Vector2(0.55f, 0.35f), colliderOffset = new Vector2(0f, 0.05f),  direction = CapsuleDirection2D.Horizontal },
        new MonsterDef { name = "Ghost",    colliderSize = new Vector2(0.55f, 0.7f),  colliderOffset = new Vector2(0f, 0.02f),  direction = CapsuleDirection2D.Vertical },
        new MonsterDef { name = "Mimic",    colliderSize = new Vector2(0.55f, 0.5f),  colliderOffset = new Vector2(0f, -0.2f),  direction = CapsuleDirection2D.Horizontal },
        new MonsterDef { name = "Spirit",   colliderSize = new Vector2(0.45f, 0.5f),  colliderOffset = new Vector2(0f, 0.05f),  direction = CapsuleDirection2D.Vertical },
        new MonsterDef { name = "Necromancer", colliderSize = new Vector2(0.45f, 0.75f), colliderOffset = new Vector2(0f, -0.05f), direction = CapsuleDirection2D.Vertical },
    };

    // Boss sprites are 64px = 2 units, so collider sizes here are out of 2
    static readonly MonsterDef[] Bosses =
    {
        new MonsterDef { name = "KingSlime",   colliderSize = new Vector2(1.5f, 0.85f), colliderOffset = new Vector2(0f, -0.45f), direction = CapsuleDirection2D.Horizontal, boss = true, bossType = BossType.KingSlime },
        new MonsterDef { name = "AncientLich", colliderSize = new Vector2(0.8f, 1.4f),  colliderOffset = new Vector2(0f, -0.2f),  direction = CapsuleDirection2D.Vertical,   boss = true, bossType = BossType.AncientLich },
        new MonsterDef { name = "OrcWarlord",  colliderSize = new Vector2(0.9f, 1.3f),  colliderOffset = new Vector2(0f, -0.2f),  direction = CapsuleDirection2D.Vertical,   boss = true, bossType = BossType.OrcWarlord },
    };

    static MonsterSetup()
    {
        EditorApplication.delayCall += () =>
        {
            if (!EditorApplication.isPlayingOrWillChangePlaymode) BuildMissing();
        };
    }

    static string PrefabPath(MonsterDef def) => $"{(def.boss ? BossPrefabRoot : PrefabRoot)}/{def.name}.prefab";

    [MenuItem("Hearts for Power/Build Missing Monster Prefabs")]
    public static void BuildMissing()
    {
        var missing = Monsters.Concat(Bosses)
            .Where(def => AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath(def)) == null)
            .ToArray();
        if (missing.Length == 0) return;
        EnsureFolders();
        int built = missing.Count(def => BuildPrefab(def) != null);
        AssetDatabase.SaveAssets();
        Debug.Log($"MonsterSetup: built {built} missing prefab(s): {string.Join(", ", missing.Select(d => d.name))}.");
    }

    [MenuItem("Hearts for Power/Rebuild ALL Monster Prefabs (overwrites edits)")]
    public static void Rebuild()
    {
        EnsureFolders();
        int built = Monsters.Count(def => BuildPrefab(def) != null);
        int bosses = Bosses.Count(def => BuildPrefab(def) != null);
        AssetDatabase.SaveAssets();
        Debug.Log($"MonsterSetup: rebuilt {built} monster prefabs in {PrefabRoot} and {bosses} boss prefabs in {BossPrefabRoot}.");
    }

    static void EnsureFolders()
    {
        EnsureFolder("Assets/Resources");
        EnsureFolder(PrefabRoot);
        EnsureFolder(BossPrefabRoot);
    }

    static GameObject BuildPrefab(MonsterDef def)
    {
        string folder = $"{(def.boss ? BossAnimRoot : AnimRoot)}/{def.name}";
        var controller = AssetDatabase.LoadAssetAtPath<AnimatorOverrideController>($"{folder}/{def.name}.overrideController");
        var sprite = AssetDatabase.LoadAllAssetsAtPath($"{folder}/{def.name}_Sheet.png")
            .OfType<Sprite>()
            .FirstOrDefault(s => s.name == $"{def.name}_Idle_Down_0");
        if (controller == null || sprite == null)
        {
            Debug.LogError($"MonsterSetup: missing override controller or sprite sheet for {def.name} in {folder}.");
            return null;
        }

        var go = new GameObject(def.name);
        go.transform.localScale = new Vector3(2f, 2f, 1f);

        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = sprite;
        sr.sortingOrder = 1;

        go.AddComponent<Animator>().runtimeAnimatorController = controller;

        var rb = go.AddComponent<Rigidbody2D>();
        rb.bodyType = RigidbodyType2D.Kinematic;   // the player can't push monsters
        rb.useFullKinematicContacts = true;
        rb.gravityScale = 0f;
        rb.freezeRotation = true;

        var col = go.AddComponent<CapsuleCollider2D>();
        col.direction = def.direction;
        col.size = def.colliderSize;
        col.offset = def.colliderOffset;

        go.AddComponent<EnemyHealth>();
        go.AddComponent<EnemyChase>();
        go.AddComponent<MonsterAnimator>();
        if (def.boss) go.AddComponent<BossController>().type = def.bossType;

        var prefab = PrefabUtility.SaveAsPrefabAsset(go, PrefabPath(def));
        Object.DestroyImmediate(go);
        return prefab;
    }

    static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path)) return;
        int slash = path.LastIndexOf('/');
        AssetDatabase.CreateFolder(path.Substring(0, slash), path.Substring(slash + 1));
    }
}
