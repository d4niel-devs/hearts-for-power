using UnityEngine;

// Something standing on a room tile:
//   Rock    blocks walking and shots; bombs smash it into rubble
//   Pillar  blocks walking and shots; indestructible
//   Pot     blocks walking and shots; breaks to the sword, spells and bombs (small chance of a heart)
//   Pit     blocks walking only; shots fly over
//   Spikes  a trap that pops up on a timer and hurts only the knight (see SpikeTrap)
public class Obstacle : MonoBehaviour
{
    public TileKind kind;
    public Vector2Int tile;
    public Room room;

    // Chance a broken pot drops a heart
    public static float PotHeartChance = 0.04f;
    // Chance a pot is really a mimic (set per floor by the GameManager)
    public static float MimicChance = 0f;
    public bool isMimic;

    public static Obstacle Create(Room room, Vector2Int tile, TileKind kind, int pitMask, System.Random random)
    {
        Vector2 position = room.Grid.TileCenter(tile);
        string sprite;
        int order = Fx.CharacterOrder;    // sorted by height with the characters, so they can stand behind it
        switch (kind)
        {
            case TileKind.Rock: sprite = Theme.Path(random.Next(2) == 0 ? "Rock_0" : "Rock_1"); break;
            case TileKind.Pillar: sprite = Theme.Path("Pillar"); break;
            case TileKind.Pot: sprite = Theme.Path("Pot"); break;   // (mimics swap in their own crack below)
            case TileKind.Pit: sprite = Theme.Path($"Pit_{pitMask}"); order = -18; break;
            default: sprite = Theme.Path("Spikes_down"); order = -18; break;
        }

        var sr = Fx.SpawnSprite(kind.ToString(), sprite, position, order, Color.white);
        sr.transform.SetParent(room.transform, true);
        var obstacle = sr.gameObject.AddComponent<Obstacle>();
        obstacle.kind = kind;
        obstacle.tile = tile;
        obstacle.room = room;
        if (kind == TileKind.Pot && random.NextDouble() < MimicChance)
        {
            obstacle.isMimic = true;
            var tell = Theme.Sprite("Pot_Mimic");   // the only tell: a slightly different crack
            if (tell != null) sr.sprite = tell;
        }

        if (kind == TileKind.Spikes)
        {
            sr.gameObject.AddComponent<SpikeTrap>();
            return obstacle;
        }
        if (kind == TileKind.Pit && Theme.GlowingPits) sr.gameObject.AddComponent<LavaGlow>();

        // Blocks the knight (monsters use the room grid instead)
        sr.gameObject.layer = LayerMask.NameToLayer("Obstacle");
        var box = sr.gameObject.AddComponent<BoxCollider2D>();
        switch (kind)
        {
            case TileKind.Pit: box.size = new Vector2(1.9f, 1.9f); break;
            case TileKind.Pot: box.size = new Vector2(1.1f, 1.0f); box.offset = new Vector2(0f, -0.4f); break;
            default: box.size = new Vector2(1.7f, 1.4f); box.offset = new Vector2(0f, -0.25f); break;
        }
        return obstacle;
    }

    private bool broken;

    public void Break()
    {
        if (broken || (kind != TileKind.Pot && kind != TileKind.Rock)) return;
        broken = true;
        room.Grid.Set(tile, TileKind.Floor);
        room.RemoveObstacle(tile);

        if (kind == TileKind.Pot)
        {
            Fx.Puff(transform.position, new Color(0.72f, 0.42f, 0.24f), 14, 4f, 1.4f);
            Audio.Play("PotBreak", 0.7f);
            if (isMimic && GameManager.Instance != null) GameManager.Instance.SpawnMimic(transform.position);
            else if (Random.value < PotHeartChance) HeartPickup.Spawn(transform.position, 2, false);
        }
        else
        {
            Fx.Puff(transform.position, new Color(0.55f, 0.54f, 0.58f), 18, 5f, 1.6f);
            Audio.Play("RockBreak", 0.8f);
            var rubble = Fx.SpawnSprite("Rubble", Theme.Path("Rubble"), transform.position, -18, Color.white);
            rubble.transform.SetParent(room.transform, true);
        }
        Destroy(gameObject);
    }
}

// Spikes cycle: down (safe) -> rattling tips (warning) -> up (½ heart to the knight if he's on it). All traps share one clock.
public class SpikeTrap : MonoBehaviour
{
    public float downTime = 2f;
    public float warnTime = 0.5f;
    public float upTime = 1f;

    private SpriteRenderer sr;
    private PlayerHealth player;

    public bool IsUp { get; private set; }

    void Start()
    {
        sr = GetComponent<SpriteRenderer>();
        var movement = FindAnyObjectByType<PlayerMovement>();
        if (movement != null) player = movement.GetComponent<PlayerHealth>();
    }

    void Update()
    {
        // Every trap reads the same clock, so all the spikes in a room rise and fall together
        float cycle = downTime + warnTime + upTime;
        float timer = Time.time % cycle;
        string state = timer < downTime ? "down" : timer < downTime + warnTime ? "warn" : "up";
        bool wasUp = IsUp;
        IsUp = state == "up";
        sr.sprite = Theme.Sprite("Spikes_" + state);
        if (IsUp && !wasUp)
        {
            Fx.Puff(transform.position, new Color(0.8f, 0.8f, 0.85f), 4, 2f);
            Audio.Play("Spike", 0.35f);   // all traps rise together, so this plays once
        }

        if (!IsUp || player == null || player.IsDead) return;
        // The knight's feet are a little below his center
        Vector2 feet = (Vector2)player.transform.position + new Vector2(0f, -0.5f);
        Vector2 d = feet - (Vector2)transform.position;
        if (Mathf.Abs(d.x) < 0.9f && Mathf.Abs(d.y) < 0.9f) player.TakeDamage(1, transform.position);
    }
}

// Lava pits (caves): the molten glow slowly pulses
public class LavaGlow : MonoBehaviour
{
    private SpriteRenderer sr;
    private float phase;

    void Start()
    {
        sr = GetComponent<SpriteRenderer>();
        phase = transform.position.x * 0.7f + transform.position.y * 0.3f;   // neighbouring tiles ripple
    }

    void Update()
    {
        float k = 0.5f + 0.5f * Mathf.Sin(Time.time * 2.2f + phase);
        sr.color = Color.Lerp(new Color(0.82f, 0.8f, 0.8f), Color.white, k);
    }
}

// Stairs down to the next floor, revealed after the boss
public class Stairs : MonoBehaviour
{
    private Transform player;
    private bool used;

    public static Stairs Spawn(Room room, Vector2 position)
    {
        var sr = Fx.SpawnSprite("Stairs", Theme.Path("Stairs"), position, -18, Color.white);
        sr.transform.SetParent(room.transform, true);
        Fx.Puff(position, new Color(0.5f, 0.45f, 0.4f), 16, 4f, 1.4f);
        return sr.gameObject.AddComponent<Stairs>();
    }

    void Start()
    {
        var movement = FindAnyObjectByType<PlayerMovement>();
        if (movement != null) player = movement.transform;
    }

    void Update()
    {
        if (used || player == null || GameManager.Instance == null) return;
        Vector2 feet = (Vector2)player.position + new Vector2(0f, -0.5f);
        if (Vector2.Distance(feet, transform.position) < 0.8f)
        {
            used = true;
            GameManager.Instance.GoDownStairs();
        }
    }
}
