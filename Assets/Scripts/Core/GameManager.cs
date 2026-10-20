using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

// Runs the game, Isaac-style: each floor is a generated map of rooms (start, fights, a treasure
// shop and a boss). Walking into an uncleared room locks its doors and, after a short pause, every
// monster for that room rises out of the ground at once. Beating the boss drops a heart container,
// a spell pedestal and stairs down to the next, harder floor. Endless; the score is the deepest floor.
// Created automatically in any scene with a knight (PlayerMovement); add it to the scene yourself
// if you want to tweak the settings in the Inspector.
public class GameManager : MonoBehaviour
{
    public enum Phase { Starting, Title, Exploring, Fighting, Transition, GameOver }

    [System.Serializable]
    public class MonsterType
    {
        public string name;               // prefab in Resources/Monsters
        public int health;
        public float speed;
        public int contactDamage;         // half hearts
        public MonsterBehaviour behaviour;
        public Color puffColor;
        public int firstFloor;            // first floor it can appear on (0 = never picked for rooms)
        public int cost;                  // how much of a room's budget it uses
        public MonsterMovement movement;  // walks, flies over pits, or drifts through everything
    }

    public static GameManager Instance { get; private set; }
    // True on the title screen, while paused, sliding between rooms, or after death: no moving, attacking or using abilities
    public static bool InputLocked => Instance != null &&
        (Instance.Paused || Instance.CurrentPhase == Phase.GameOver || Instance.CurrentPhase == Phase.Transition ||
         Instance.CurrentPhase == Phase.Title);

    [Header("Rooms")]
    [Tooltip("Seconds between the doors locking and the monsters rising out of the ground.")]
    public float spawnDelay = 0.8f;
    [Tooltip("Monster health grows by this fraction per floor.")]
    public float healthGrowthPerFloor = 0.3f;

    [Header("Drops")]
    [Range(0f, 1f)] public float heartDropChance = 0.01f;
    [Range(0f, 1f)] public float potHeartChance = 0.04f;

    [Header("Testing")]
    [Tooltip("Editor only. F5: kill every monster (Shift+F5: spawn a necromancer)   F6: +1 heart container   F7: go to the boss room (Shift+F7: next floor)   F8: toggle invincibility   F9: take half a heart   F10: go to the treasure room")]
    public bool debugKeys = true;

    public List<MonsterType> monsters = new List<MonsterType>
    {
        new MonsterType { name = "Slime",    health = 18, speed = 1.6f, contactDamage = 1, behaviour = MonsterBehaviour.Hop,     puffColor = new Color(0.4f, 0.65f, 1f),     firstFloor = 1, cost = 1 },
        new MonsterType { name = "Goblin",   health = 14, speed = 2.8f, contactDamage = 1, behaviour = MonsterBehaviour.Chase,   puffColor = new Color(0.5f, 0.75f, 0.3f),   firstFloor = 1, cost = 1 },
        new MonsterType { name = "Zombie",   health = 40, speed = 1.3f, contactDamage = 2, behaviour = MonsterBehaviour.Chase,   puffColor = new Color(0.5f, 0.62f, 0.45f),  firstFloor = 1, cost = 2 },
        new MonsterType { name = "Kobold",   health = 22, speed = 2.0f, contactDamage = 1, behaviour = MonsterBehaviour.Lunge,   puffColor = new Color(0.85f, 0.42f, 0.25f), firstFloor = 2, cost = 2 },
        new MonsterType { name = "Skeleton", health = 22, speed = 1.8f, contactDamage = 1, behaviour = MonsterBehaviour.Archer,  puffColor = new Color(0.92f, 0.9f, 0.82f),  firstFloor = 2, cost = 2 },
        new MonsterType { name = "Orc",      health = 65, speed = 1.5f, contactDamage = 2, behaviour = MonsterBehaviour.Charger, puffColor = new Color(0.45f, 0.6f, 0.33f),  firstFloor = 3, cost = 3 },
        new MonsterType { name = "Bat",      health = 10, speed = 3.0f, contactDamage = 1, behaviour = MonsterBehaviour.Flutter, puffColor = new Color(0.6f, 0.45f, 0.8f),   firstFloor = 1, cost = 1, movement = MonsterMovement.Fly },
        new MonsterType { name = "Ghost",    health = 26, speed = 1.6f, contactDamage = 1, behaviour = MonsterBehaviour.Haunt,   puffColor = new Color(0.85f, 0.9f, 1f),    firstFloor = 2, cost = 2, movement = MonsterMovement.Phase },
        new MonsterType { name = "Necromancer", health = 30, speed = 1.5f, contactDamage = 1, behaviour = MonsterBehaviour.Summoner, puffColor = new Color(0.4f, 0.8f, 0.5f), firstFloor = 3, cost = 3 },
        // Spirits are only ever summoned by necromancers, and can't be killed (they die with it)
        new MonsterType { name = "Spirit",   health = 30, speed = 1.7f, contactDamage = 1, behaviour = MonsterBehaviour.Spirit,  puffColor = new Color(0.5f, 1f, 0.6f),     firstFloor = 0, cost = 0, movement = MonsterMovement.Phase },
        // Mimics only ever come out of broken pots (see Obstacle.Break)
        new MonsterType { name = "Mimic",    health = 30, speed = 1.4f, contactDamage = 1, behaviour = MonsterBehaviour.Hop,     puffColor = new Color(0.8f, 0.5f, 0.3f),   firstFloor = 0, cost = 2 },
    };

    public Phase CurrentPhase { get; private set; }
    public int Floor { get; private set; }
    public int RoomsCleared { get; private set; }
    public int Kills { get; private set; }
    public int ChampionsSlain { get; private set; }
    public int BossesBeaten { get; private set; }
    public float RunTime { get; private set; }      // seconds actually played (not paused)
    public bool Paused { get; private set; }
    public bool NewBest { get; private set; }
    public int BestFloor => PlayerPrefs.GetInt(BestFloorKey, 0);
    public EnemyHealth Boss { get; private set; }
    public string BossName { get; private set; }
    public FloorMap Map { get; private set; }

    const string BestFloorKey = "HeartsForPower.BestFloor";
    static bool skipTitle;   // Restart / Try Again go straight into a new run
    static readonly Color DirtColor = new Color(0.45f, 0.34f, 0.24f);

    private Transform player;
    private Rigidbody2D playerBody;
    private Collider2D playerCollider;
    private PlayerHealth playerHealth;
    private PlayerAbilities playerAbilities;
    private System.Random random;
    private float flowTimer;
    private readonly List<Vector2> corpses = new List<Vector2>();   // where monsters died in this room (necromancers raise them)

    float HealthMultiplier(int depth) => 1f + healthGrowthPerFloor * (Floor - 1) + 0.03f * depth;
    float SpeedMultiplier => Mathf.Min(1.35f, 1f + 0.06f * (Floor - 1));

    // ---------------------------------------------------------------- setup

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Bootstrap()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
        SceneManager.sceneLoaded += OnSceneLoaded;
        EnsureExists();
    }

    static void OnSceneLoaded(Scene scene, LoadSceneMode mode) => EnsureExists();

    static void EnsureExists()
    {
        if (FindAnyObjectByType<GameManager>() != null) return;
        if (FindAnyObjectByType<PlayerMovement>() == null) return;
        new GameObject("GameManager").AddComponent<GameManager>();
    }

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(this);
            return;
        }
        Instance = this;
        TimeControl.Reset();
        random = new System.Random();
        if (GetComponent<GameUI>() == null) gameObject.AddComponent<GameUI>();
    }

    void OnDestroy()
    {
        if (Instance == this)
        {
            Instance = null;
            Room.Current = null;
            TimeControl.Reset();
        }
    }

    void Start()
    {
        var movement = FindAnyObjectByType<PlayerMovement>();
        if (movement == null)
        {
            Debug.LogError("GameManager: no knight (PlayerMovement) in the scene.");
            enabled = false;
            return;
        }
        player = movement.transform;
        playerBody = movement.GetComponent<Rigidbody2D>();
        playerCollider = EnemyChase.ActiveCollider(movement.gameObject);
        playerHealth = movement.GetComponent<PlayerHealth>();
        playerAbilities = movement.GetComponent<PlayerAbilities>();
        playerHealth.Died += OnPlayerDied;
        Obstacle.PotHeartChance = potHeartChance;

        StartFloor(1);
        if (skipTitle) BeginRun();
        else
        {
            CurrentPhase = Phase.Title;   // the start room sits dimmed behind the title screen
            Audio.Music("Title", 0.5f);
        }
        skipTitle = false;
    }

    // Title screen "Play"
    public void BeginRun()
    {
        CurrentPhase = Phase.Exploring;
        Audio.Music(FloorMusic, 0.6f);
        GameUI.ShowBanner("FLOOR 1", $"{Theme.DisplayName(Theme.Current)}  -  WASD to move, SPACE to swing", 3f);
    }

    // Back to the title screen (abandons the run)
    public void QuitToTitle()
    {
        skipTitle = false;
        TimeControl.Reset();
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    public static void QuitGame()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }

    void Update()
    {
        if (CurrentPhase == Phase.GameOver)
        {
            if (Input.GetKeyDown(KeyCode.R)) Restart();
            return;
        }
        if (CurrentPhase == Phase.Title) return;              // the title menu (GameUI) runs things
        // Esc or P (the Unity editor's Game view can swallow Esc)
        bool pauseKey = Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P);
        if (pauseKey && !GameUI.MenuHandlesEscape) SetPaused(!Paused);
        if (Paused) return;
        RunTime += Time.unscaledDeltaTime;
        if (debugKeys && Application.isEditor) DebugKeys();   // never active in a build

        var room = Room.Current;
        if (room == null) return;

        // Monsters re-plan their route around obstacles a few times a second
        flowTimer -= Time.deltaTime;
        if (flowTimer <= 0f)
        {
            flowTimer = 0.2f;
            room.Grid.UpdateFlow(player.position);
        }

        if (CurrentPhase == Phase.Exploring || CurrentPhase == Phase.Fighting) KeepPlayerInRoom(room);
        if (CurrentPhase == Phase.Exploring) CheckDoorways(room);
    }

    // Safety net only: if the knight ever ends up past a wall (e.g. shoved by a boss), put him back.
    // Measured at his feet collider, not his pivot (the pivot sits higher up, so near the top wall it
    // would read as "outside" while he's just standing against it), and only once he's clearly past
    // the wall, so normal wall contact is never touched.
    void KeepPlayerInRoom(Room room)
    {
        Rect inner = room.Interior;
        Vector2 feet = playerCollider != null ? (Vector2)playerCollider.bounds.center : playerBody.position;
        const float tolerance = 0.6f;
        bool inside = feet.x >= inner.xMin - tolerance && feet.x <= inner.xMax + tolerance &&
                      feet.y >= inner.yMin - tolerance && feet.y <= inner.yMax + tolerance;
        if (inside) return;

        // Standing in an open doorway is fine (that's how he leaves the room)
        for (int s = 0; s < 4; s++)
        {
            var door = room.DoorOn((Side)s);
            if (door == null || !door.IsOpen) continue;
            Vector2 d = feet - (Vector2)door.transform.position;
            bool vertical = s == (int)Side.North || s == (int)Side.South;
            if (vertical ? Mathf.Abs(d.x) < 1f && Mathf.Abs(d.y) < 2f : Mathf.Abs(d.y) < 1f && Mathf.Abs(d.x) < 2f) return;
        }

        Vector2 fixedFeet = new Vector2(Mathf.Clamp(feet.x, inner.xMin + 0.4f, inner.xMax - 0.4f),
                                        Mathf.Clamp(feet.y, inner.yMin + 0.4f, inner.yMax - 0.4f));
        playerBody.position += fixedFeet - feet;
        player.position = playerBody.position;
    }

    public void SetPaused(bool paused)
    {
        Paused = paused;
        TimeControl.Paused = paused;
        Audio.Play(paused ? "UiSelect" : "UiBack");
    }

    public void Restart()
    {
        skipTitle = true;
        TimeControl.Reset();
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    // ---------------------------------------------------------------- floors

    void StartFloor(int floor)
    {
        // Remove the previous floor's rooms
        if (Map != null)
        {
            foreach (var info in Map.Rooms.Values)
                if (info.instance != null) Destroy(info.instance.gameObject);
        }
        foreach (var enemy in EnemyHealth.Alive.ToArray()) Destroy(enemy.gameObject);

        Floor = floor;
        Theme.Set(Theme.ForFloor(floor));
        Obstacle.MimicChance = floor >= 2 ? 0.1f : 0f;   // some pots hide mimics from floor 2 on
        Map = FloorMap.Generate(floor, random);
        var start = BuildRoom(Map.Start);
        Room.Current = start;
        playerBody.position = start.Grid.TileCenter(new Vector2Int(RoomGrid.Width / 2, RoomGrid.Height / 2 - 1));
        player.position = playerBody.position;
        RoomCamera.Snap();
        start.Grid.UpdateFlow(player.position);
        Audio.Music(FloorMusic);
        EnterRoom(start);
    }

    // Each floor theme has its own track
    string FloorMusic => Theme.Music(Theme.Current);

    public void GoDownStairs()
    {
        if (CurrentPhase == Phase.GameOver) return;
        StartCoroutine(GoDownStairsRoutine());
    }

    IEnumerator GoDownStairsRoutine()
    {
        CurrentPhase = Phase.Transition;
        Audio.Play("Stairs");
        GameUI.Fade(1f, 0.5f);
        yield return new WaitForSeconds(0.55f);
        StartFloor(Floor + 1);
        GameUI.Fade(0f, 0.5f);
        GameUI.ShowBanner($"FLOOR {Floor}", Theme.DisplayName(Theme.Current), 2.5f);
    }

    Room BuildRoom(RoomInfo info)
    {
        if (info.instance != null) return info.instance;
        return Room.Build(info, random.Next());
    }

    // ---------------------------------------------------------------- moving between rooms

    void CheckDoorways(Room room)
    {
        Rect inner = room.Interior;
        Vector2 p = player.position;
        for (int s = 0; s < 4; s++)
        {
            var side = (Side)s;
            var door = room.DoorOn(side);
            if (door == null || !door.IsOpen) continue;
            bool through = side switch
            {
                Side.North => p.y > inner.yMax + 0.3f,
                Side.South => p.y < inner.yMin - 0.1f,
                Side.East => p.x > inner.xMax + 0.3f,
                _ => p.x < inner.xMin - 0.3f,
            };
            if (through)
            {
                StartCoroutine(MoveToRoom(side));
                return;
            }
        }
    }

    IEnumerator MoveToRoom(Side side)
    {
        var from = Room.Current;
        var info = Map.Neighbour(from.Info, side);
        if (info == null) yield break;

        CurrentPhase = Phase.Transition;
        var next = BuildRoom(info);
        next.gameObject.SetActive(true);
        Room.Current = next;   // the camera starts sliding over

        // The knight steps in through the opposite door
        playerBody.position = next.EntryPoint(FloorMap.Opposite(side));
        player.position = playerBody.position;
        playerBody.linearVelocity = Vector2.zero;
        next.Grid.UpdateFlow(player.position);

        var camera = FindAnyObjectByType<RoomCamera>();
        yield return new WaitForSeconds(camera != null ? camera.slideTime : 0.35f);
        from.gameObject.SetActive(false);
        EnterRoom(next);
    }

    void EnterRoom(Room room)
    {
        corpses.Clear();
        var info = room.Info;
        info.visited = true;
        info.seen = true;
        foreach (var offset in FloorMap.SideOffsets)
            if (Map.Rooms.TryGetValue(info.cell + offset, out var n)) n.seen = true;

        if (info.type == RoomType.Treasure && !room.ShopStocked) StockShop(room);

        if (info.cleared)
        {
            room.SetDoorsOpen(true, false);
            CurrentPhase = Phase.Exploring;
        }
        else if (info.type == RoomType.Boss) StartCoroutine(BossFight(room));
        else StartCoroutine(Fight(room));
    }

    // ---------------------------------------------------------------- fights

    IEnumerator Fight(Room room)
    {
        CurrentPhase = Phase.Fighting;
        room.SetDoorsOpen(false, true);
        yield return new WaitForSeconds(spawnDelay);

        var points = room.SpawnPoints(player.position, 5f);
        if (points.Count < 3) points = room.SpawnPoints(player.position, 3f);
        Shuffle(points);
        var wave = BuildRoomMonsters(room.Info.depth);
        var voices = new HashSet<string>();
        for (int i = 0; i < wave.Count && i < points.Count; i++)
        {
            SpawnMonster(wave[i], points[i], 1f, false, room.Info.depth, emerge: true, canBeChampion: true);
            voices.Add(wave[i].name);
        }
        Fx.Shake(0.12f, 0.2f);
        Audio.Play("Emerge");
        foreach (var kind in voices) MonsterVoice.Emerge(kind, 1f, 0.55f);   // one call per kind of monster

        yield return new WaitUntil(() => EnemyHealth.Alive.Count == 0);
        RoomCleared(room);
    }

    IEnumerator BossFight(Room room)
    {
        CurrentPhase = Phase.Fighting;
        room.SetDoorsOpen(false, true);
        Audio.Music(null, 0.6f);
        yield return new WaitForSeconds(spawnDelay + 0.4f);

        // Bosses cycle King Slime -> The Ancient Lich -> Orc Warlord, getting tougher each cycle
        int tier = (Floor - 1) / 3 + 1;
        var bossType = new[] { BossType.KingSlime, BossType.AncientLich, BossType.OrcWarlord }[(Floor - 1) % 3];
        string prefabName = bossType.ToString();
        int baseHealth = bossType == BossType.KingSlime ? 260 : bossType == BossType.AncientLich ? 300 : 360;
        Color bossPuff = bossType == BossType.KingSlime ? new Color(0.4f, 0.65f, 1f)
            : bossType == BossType.AncientLich ? new Color(0.45f, 0.9f, 0.55f) : new Color(0.55f, 0.6f, 0.45f);
        // Rise at whichever central spot is furthest from the knight (never right next to the door he came in by)
        Vector2 position = room.Grid.TileCenter(new Vector2Int(RoomGrid.Width / 2, RoomGrid.Height / 2));
        foreach (var t in new[] { new Vector2Int(6, 1), new Vector2Int(6, 5), new Vector2Int(3, 3), new Vector2Int(9, 3), new Vector2Int(6, 3) })
        {
            Vector2 p = room.Grid.TileCenter(t);
            if (Vector2.Distance(p, player.position) > Vector2.Distance(position, player.position)) position = p;
        }

        var prefab = Resources.Load<GameObject>("Bosses/" + prefabName);
        if (prefab == null)
        {
            Debug.LogError($"GameManager: missing boss prefab Resources/Bosses/{prefabName} (run Hearts for Power > Build Missing Monster Prefabs)");
            RoomCleared(room);
            yield break;
        }

        var go = Instantiate(prefab, position, Quaternion.identity);
        go.name = prefabName;
        go.layer = LayerMask.NameToLayer("Enemy");
        var health = go.GetComponent<EnemyHealth>();
        float tierMultiplier = 1f + 0.5f * (tier - 1);
        health.SetMaxHealth(Mathf.RoundToInt(baseHealth * tierMultiplier));
        health.isBoss = true;
        health.kind = prefabName;
        health.puffColor = bossPuff;
        health.Died += OnEnemyDied;
        var chase = go.GetComponent<EnemyChase>();
        chase.player = player;
        chase.contactDamage = 2;
        chase.behaviour = MonsterBehaviour.Scripted;
        var boss = go.GetComponent<BossController>();
        if (boss == null) boss = go.AddComponent<BossController>();
        boss.type = bossType;
        boss.tier = tier;
        chase.BeginEmerge(0.8f);
        Fx.Puff(position, DirtColor, 40, 7f, 2f);
        Fx.Ring(position, 3f, DirtColor, 0.5f);
        Fx.Shake(0.45f, 0.6f);
        Audio.Play("Emerge", 1f, 0.7f);
        MonsterVoice.Emerge(prefabName, 1f, 1f);
        Audio.Music("Boss", 0.3f);

        Boss = health;
        BossName = boss.DisplayName;
        GameUI.ShowBanner(BossName, null, 2f);

        // (the boss's own death explosion plays out first)
        yield return new WaitUntil(() => EnemyHealth.Alive.Count == 0 && health == null);
        Boss = null;
        BossesBeaten++;
        RoomCleared(room);
        Audio.Music(null, 0.4f);
        Audio.Play("BossDefeated");

        // Rewards: one random spell (1 heart container) and the way down
        yield return new WaitForSeconds(0.8f);
        var spell = PickSpell();
        if (spell.HasValue)
        {
            var pedestal = Pedestal.Spawn(room.Grid.TileCenter(new Vector2Int(RoomGrid.Width / 2, RoomGrid.Height / 2)), spell.Value, 2);
            pedestal.transform.SetParent(room.transform, true);
        }
        Stairs.Spawn(room, room.Grid.TileCenter(new Vector2Int(RoomGrid.Width / 2, 1)));
        GameUI.ShowBanner("BOSS DEFEATED", "Take the stairs down when you're ready", 3f);
        yield return new WaitForSeconds(1.5f);
        Audio.Music(FloorMusic, 1.5f);
    }

    void RoomCleared(Room room)
    {
        room.Info.cleared = true;
        RoomsCleared++;
        if (room.Info.type != RoomType.Boss) Audio.Play("RoomClear", 0.7f);
        room.SetDoorsOpen(true, true);
        CurrentPhase = Phase.Exploring;
    }

    List<MonsterType> BuildRoomMonsters(int depth)
    {
        var available = monsters.FindAll(m => m.firstFloor > 0 && m.firstFloor <= Floor);
        var list = new List<MonsterType>();
        int budget = 3 + 2 * Floor + depth / 2;
        while (budget > 0 && list.Count < 10)
        {
            var affordable = available.FindAll(m => m.cost <= budget);
            if (affordable.Count == 0) break;
            var m = PickWeighted(affordable);
            list.Add(m);
            budget -= m.cost;
            if (m.name == "Bat")                                   // bats come in little swarms
                for (int extra = random.Next(1, 3); extra > 0 && list.Count < 10; extra--) list.Add(m);
        }
        return list;
    }

    // Random monster, favouring the ones that fit this floor's theme
    MonsterType PickWeighted(List<MonsterType> options)
    {
        float total = 0f;
        foreach (var m in options) total += Theme.MonsterWeight(m.name);
        float roll = (float)random.NextDouble() * total;
        foreach (var m in options)
        {
            roll -= Theme.MonsterWeight(m.name);
            if (roll <= 0f) return m;
        }
        return options[options.Count - 1];
    }

    // 2% on floor 1, +1% per floor, at most 8%
    float ChampionChance => Mathf.Min(0.08f, 0.02f + 0.01f * (Floor - 1));

    EnemyHealth SpawnMonster(MonsterType type, Vector2 position, float scale, bool mini, int depth, bool emerge, bool canBeChampion = false)
    {
        var prefab = Resources.Load<GameObject>("Monsters/" + type.name);
        if (prefab == null)
        {
            Debug.LogError($"GameManager: missing prefab Resources/Monsters/{type.name}");
            return null;
        }
        var go = Instantiate(prefab, position, Quaternion.identity);
        go.name = type.name;
        go.layer = LayerMask.NameToLayer("Enemy");
        go.transform.localScale = Vector3.Scale(go.transform.localScale, new Vector3(scale, scale, 1f));

        var health = go.GetComponent<EnemyHealth>();
        health.SetMaxHealth(Mathf.RoundToInt(type.health * HealthMultiplier(depth) * (mini ? 0.35f : 1f)));
        health.puffColor = type.puffColor;
        health.kind = type.name;
        health.isMini = mini;
        health.Died += OnEnemyDied;

        var chase = go.GetComponent<EnemyChase>();
        chase.player = player;
        chase.speed = type.speed * SpeedMultiplier * (mini ? 1.25f : 1f);
        chase.behaviour = type.behaviour;
        chase.movement = type.movement;
        chase.contactDamage = type.contactDamage;
        if (canBeChampion && !mini && Random.value < ChampionChance) MakeChampion(go, health, chase);
        if (emerge)
        {
            chase.BeginEmerge(0.45f);
            Fx.Puff(position + new Vector2(0f, -0.4f), DirtColor, 14, 4f, 1.4f);
            Fx.Puff(position + new Vector2(0f, -0.4f), new Color(0.3f, 0.24f, 0.18f), 8, 2.5f, 1.8f);
        }
        return health;
    }

    // Used by bosses to call in help
    public EnemyHealth SpawnMinion(string monsterName, Vector2 position)
    {
        var type = monsters.Find(m => m.name == monsterName);
        if (type == null || CurrentPhase == Phase.GameOver) return null;
        return SpawnMonster(type, position, 1f, false, 0, emerge: true);
    }

    void MakeChampion(GameObject go, EnemyHealth health, EnemyChase chase)
    {
        var champion = go.AddComponent<Champion>();
        champion.trait = (ChampionTrait)Random.Range(0, 4);
        health.isChampion = true;
        health.SetBaseColor(champion.Tint);
        go.transform.localScale *= 1.15f;
        if (champion.trait == ChampionTrait.Tough) health.SetMaxHealth(health.MaxHealth * 2);
        if (champion.trait == ChampionTrait.Swift) chase.speed *= 1.5f;
    }

    // A pot turned out to be a mimic: it bursts out right where the pot stood
    public void SpawnMimic(Vector2 position)
    {
        var type = monsters.Find(m => m.name == "Mimic");
        if (type == null || CurrentPhase == Phase.GameOver) return;
        var mimic = SpawnMonster(type, position, 1f, false, Room.Current != null ? Room.Current.Info.depth : 0, emerge: false);
        if (mimic == null) return;
        MonsterVoice.Emerge("Mimic");
        Fx.Puff(position, new Color(0.72f, 0.42f, 0.24f), 18, 5f, 1.5f);
        Fx.Shake(0.12f, 0.15f);
        GameUI.Popup("MIMIC!", (Vector3)position + Vector3.up * 0.9f);
    }

    // Necromancers: use up a spot where a monster died (false if there is none)
    public bool TakeCorpse(out Vector2 spot)
    {
        spot = default;
        if (corpses.Count == 0) return false;
        int i = Random.Range(0, corpses.Count);
        spot = corpses[i];
        corpses.RemoveAt(i);
        return true;
    }

    // ---------------------------------------------------------------- treasure shop

    void StockShop(Room room)
    {
        room.ShopStocked = true;
        var items = new List<AbilityId>();
        foreach (var id in new[] { AbilityId.Dash, AbilityId.Bomb, AbilityId.Sword })
            if (!playerAbilities.IsMaxed(id)) items.Add(id);
        if (items.Count == 0)
        {
            var spell = PickSpell();
            if (spell.HasValue) items.Add(spell.Value);
        }

        var columns = items.Count == 1 ? new[] { 6 } : items.Count == 2 ? new[] { 4, 8 } : new[] { 3, 6, 9 };
        for (int i = 0; i < items.Count; i++)
        {
            var pedestal = Pedestal.Spawn(room.Grid.TileCenter(new Vector2Int(columns[i], RoomGrid.Height / 2)), items[i], 1);
            pedestal.transform.SetParent(room.transform, true);
            pedestal.shopRoom = room;
        }
    }

    // A bought shop item makes everything else in that treasure room cost half a heart more
    public void OnShopPurchase(Room room)
    {
        room.TreasurePurchases++;
        foreach (var pedestal in room.GetComponentsInChildren<Pedestal>(true))
            if (!pedestal.Taken) pedestal.SetCost(1 + room.TreasurePurchases);
    }

    AbilityId? PickSpell()
    {
        var pool = new List<AbilityId>();
        foreach (var id in new[] { AbilityId.MagicBolt, AbilityId.Fireball, AbilityId.IceShards, AbilityId.Lightning })
        {
            if (playerAbilities.IsMaxed(id)) continue;
            pool.Add(id);
            if (!playerAbilities.Has(id)) pool.Add(id);   // new spells twice as likely
        }
        if (pool.Count == 0) return null;
        return pool[random.Next(pool.Count)];
    }

    // ---------------------------------------------------------------- deaths

    void OnEnemyDied(EnemyHealth enemy)
    {
        Kills++;
        if (enemy.isChampion) ChampionsSlain++;
        Vector2 at = enemy.transform.position;

        if (enemy.isBoss)
        {
            HeartPickup.Spawn(at, 2, true);
            return;
        }
        if (!enemy.isMini && enemy.kind != "Spirit" && corpses.Count < 8) corpses.Add(at);

        // Big slimes split into two small fast ones
        if (enemy.kind == "Slime" && !enemy.isMini)
        {
            var type = monsters.Find(m => m.name == "Slime");
            for (int i = -1; i <= 1; i += 2)
            {
                var mini = SpawnMonster(type, RoomBounds.Clamp(at + new Vector2(0.35f * i, 0f), 0.4f), 0.6f, true, 0, emerge: false);
                if (mini != null) mini.GetComponent<EnemyChase>().Knockback(new Vector2(4f * i, 1f));
            }
        }

        // Splitting champions burst into two small copies
        var champion = enemy.GetComponent<Champion>();
        if (champion != null && champion.trait == ChampionTrait.Splitting)
        {
            var type = monsters.Find(m => m.name == enemy.kind);
            if (type != null)
                for (int i = -1; i <= 1; i += 2)
                {
                    var half = SpawnMonster(type, RoomBounds.Clamp(at + new Vector2(0.4f * i, 0f), 0.4f), 0.65f, true, 0, emerge: false);
                    if (half == null) continue;
                    half.SetBaseColor(champion.Tint);
                    half.GetComponent<EnemyChase>().Knockback(new Vector2(4f * i, 1f));
                }
        }

        float dropChance = enemy.isChampion ? 0.15f : heartDropChance;
        if (Random.value < dropChance) HeartPickup.Spawn(at, 2, false);
    }

    void OnPlayerDied()
    {
        CurrentPhase = Phase.GameOver;
        StopAllCoroutines();
        Audio.Sting("GameOver", stopMusic: true);
        if (Floor > BestFloor)
        {
            NewBest = true;
            PlayerPrefs.SetInt(BestFloorKey, Floor);
            PlayerPrefs.Save();
        }
    }

    // ---------------------------------------------------------------- testing

    void DebugKeys()
    {
        bool shift = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
        if (Input.GetKeyDown(KeyCode.F5) && shift)                                        // spawn a necromancer to test with
            SpawnMinion("Necromancer", RoomBounds.Clamp((Vector2)player.position + new Vector2(4f, 0f), 1f));
        else if (Input.GetKeyDown(KeyCode.F5))
            foreach (var enemy in EnemyHealth.Alive.ToArray()) enemy.ForceKill();
        if (Input.GetKeyDown(KeyCode.F6)) playerHealth.AddContainers(2, true);
        if (Input.GetKeyDown(KeyCode.F7) && shift && CurrentPhase == Phase.Exploring) GoDownStairs();   // skip to the next floor
        else if (Input.GetKeyDown(KeyCode.F7) && CurrentPhase == Phase.Exploring) StartCoroutine(TeleportTo(Map.BossRoom));
        if (Input.GetKeyDown(KeyCode.F10) && CurrentPhase == Phase.Exploring) StartCoroutine(TeleportTo(Map.TreasureRoom));
        if (Input.GetKeyDown(KeyCode.F8))
        {
            playerHealth.GodMode = !playerHealth.GodMode;
            GameUI.ShowBanner("DEBUG", playerHealth.GodMode ? "Invincible" : "Invincibility off", 1.5f);
        }
        if (Input.GetKeyDown(KeyCode.F9))
        {
            bool god = playerHealth.GodMode;
            playerHealth.GodMode = false;
            playerHealth.TakeDamage(1, (Vector2)player.position + Vector2.right);
            playerHealth.GodMode = god;
        }
    }

    IEnumerator TeleportTo(RoomInfo info)
    {
        if (info == null || Room.Current.Info == info) yield break;
        CurrentPhase = Phase.Transition;
        var from = Room.Current;
        var room = BuildRoom(info);
        room.gameObject.SetActive(true);
        Room.Current = room;
        Side entry = Side.South;
        for (int s = 0; s < 4; s++) if (info.doors[s]) entry = (Side)s;
        playerBody.position = room.EntryPoint(entry);
        player.position = playerBody.position;
        room.Grid.UpdateFlow(player.position);
        RoomCamera.Snap();
        from.gameObject.SetActive(false);
        yield return null;
        EnterRoom(room);
    }

    static void Shuffle<T>(List<T> list)
    {
        for (int i = list.Count - 1; i > 0; i--)
        {
            int j = Random.Range(0, i + 1);
            (list[i], list[j]) = (list[j], list[i]);
        }
    }
}
