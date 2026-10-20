using System.Collections.Generic;
using UnityEngine;

public enum MonsterBehaviour
{
    Chase,      // walks straight at the player (4 directions)
    Hop,        // waits, then hops toward the player (slimes)
    Lunge,      // chases, then winds up and lunges when close (kobolds)
    Archer,     // keeps its distance and shoots bones (skeletons)
    Charger,    // chases, then winds up and charges in a straight line (orcs)
    Scripted,   // moved by another script, e.g. BossController
    Flutter,    // weaves erratically toward the player and swoops at him (bats)
    Haunt,      // drifts straight at the player, fading out now and then (ghosts)
    Summoner,   // keeps its distance, calls up spirits (necromancers)
    Spirit      // circles the player at a distance, spitting slow soul-fire (necromancer summons)
}

// How a monster gets around obstacles
public enum MonsterMovement
{
    Walk,       // blocked by rocks, pillars, pots and pits
    Fly,        // crosses pits (bats)
    Phase       // drifts through everything (ghosts); still stays inside the room
}

// Monster movement and attacks. Monsters are kinematic, so the knight can't push them;
// touching one costs him `contactDamage` half hearts. They head straight for him (diagonals too),
// walk around rocks, pits and pots using the room's flow field, push apart so they never stack,
// and are kept inside the room.
public class EnemyChase : MonoBehaviour
{
    // Every active monster, so they can keep their distance from each other
    public static readonly List<EnemyChase> Active = new List<EnemyChase>();

    public Transform player;
    public float speed = 3f;
    public MonsterBehaviour behaviour = MonsterBehaviour.Chase;
    [Tooltip("Half hearts the player loses when touching this monster.")]
    public int contactDamage = 1;
    [Range(0f, 1f)] public float knockbackResist = 0f;
    public MonsterMovement movement = MonsterMovement.Walk;

    [Header("Hop (slimes)")]
    [Tooltip("Speed while in the air, as a multiple of speed. Slimes only move during part of each hop.")]
    public float hopSpeedMultiplier = 1.8f;

    [Header("Archer")]
    public float shootInterval = 3.5f;
    [Tooltip("Random +/- added to each shot's wait so a group of archers doesn't fire in sync.")]
    public float shootIntervalJitter = 0.5f;
    [Tooltip("Only shoots when the player is at most this far away (and not behind a rock).")]
    public float shootRange = 6f;
    public int projectileDamage = 1;
    public float projectileSpeed = 5f;

    private Vector2 moveDirection;
    private Vector2 desiredVelocity;
    private Vector2 knockback;
    private float stunTimer;
    private float slowTimer;
    private float slowFactor = 1f;

    // Simple state machine for hops, lunges and charges
    private int state;
    private float stateTimer;
    private float attackCooldown;
    private Vector2 lockedDirection;

    // Rising out of the ground when spawned
    private float emergeTimer, emergeDuration;
    private float sinkTimer, sinkDuration;
    private Vector3 emergeScale;
    private Vector2 emergePosition;

    private MonsterAnimator monsterAnimator;
    private Rigidbody2D rb;
    private Collider2D ownCollider;
    private Collider2D playerCollider;
    private PlayerHealth playerHealth;
    private EnemyHealth ownHealth;
    private Vector2 footOffset;   // collider center relative to the pivot
    private float footRadius;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetStatics() => Active.Clear();

    void OnEnable() => Active.Add(this);
    void OnDisable() => Active.Remove(this);

    public bool Telegraphing { get; private set; }
    public bool IsSlowed => slowTimer > 0f;
    // Emerging also covers sinking into the floor and staying hidden under it (Ancient Lich):
    // no movement, no contact damage, no knockback
    public bool Emerging => emergeTimer > 0f || Sinking || Burrowed;
    public bool Sinking => sinkTimer > 0f;
    public bool Burrowed { get; private set; }
    // Velocity used when behaviour is Scripted (set by BossController)
    public Vector2 ScriptedVelocity { get; set; }
    public Vector2 ToPlayer => player != null ? (Vector2)(player.position - transform.position) : Vector2.zero;

    void Awake()
    {
        monsterAnimator = GetComponent<MonsterAnimator>();
        ownCollider = ActiveCollider(gameObject);
        ownHealth = GetComponent<EnemyHealth>();
        rb = GetComponent<Rigidbody2D>();
    }

    void Start()
    {
        // Prefabs can't store scene references, so find the player when none is assigned
        if (player == null)
        {
            PlayerMovement found = FindAnyObjectByType<PlayerMovement>();
            if (found != null) player = found.transform;
        }
        if (player != null)
        {
            playerCollider = ActiveCollider(player.gameObject);
            playerHealth = player.GetComponent<PlayerHealth>();
        }

        // Kinematic: the player can't shove monsters around, he just bumps into them
        if (rb != null)
        {
            rb.bodyType = RigidbodyType2D.Kinematic;
            rb.useFullKinematicContacts = true;
        }
        MeasureFeet();

        attackCooldown = Random.Range(1.2f, shootInterval);
        stateTimer = Random.Range(0.2f, 0.6f);
    }

    void MeasureFeet()
    {
        if (ownCollider == null || Emerging) return;
        Bounds b = ownCollider.bounds;
        footOffset = (Vector2)(b.center - transform.position);
        footRadius = Mathf.Clamp(Mathf.Min(b.extents.x, b.extents.y) * 0.8f, 0.2f, 0.9f);
    }

    // Rise out of the ground over `duration` seconds; harmless and still until fully out
    public void BeginEmerge(float duration)
    {
        emergeDuration = emergeTimer = duration;
        emergeScale = transform.localScale;
        emergePosition = transform.position;
        UpdateEmerge();
    }

    // Sink into the floor over `duration` seconds, then stay hidden (no collider) until Resurface
    public void BeginSink(float duration)
    {
        sinkDuration = sinkTimer = duration;
        emergeScale = transform.localScale;
        emergePosition = transform.position;
    }

    // Come back up out of the floor at `position`
    public void Resurface(Vector2 position, float duration)
    {
        Burrowed = false;
        SetPresent(true);
        transform.localScale = emergeScale;
        transform.position = position;
        if (rb != null) rb.position = position;
        BeginEmerge(duration);
    }

    void SetPresent(bool present)
    {
        foreach (var r in GetComponentsInChildren<Renderer>()) r.enabled = present;
        if (ownCollider != null) ownCollider.enabled = present;
    }

    void UpdateEmerge() => ApplyRise(1f - Mathf.Clamp01(emergeTimer / emergeDuration));

    // k = 0: under the floor, k = 1: fully out
    void ApplyRise(float k)
    {
        float eased = 1f - (1f - k) * (1f - k);
        transform.localScale = new Vector3(emergeScale.x * (1f + 0.25f * (1f - eased)), emergeScale.y * Mathf.Max(0.05f, eased), 1f);
        // feet stay on the floor while the body grows upwards
        var sr = GetComponent<SpriteRenderer>();
        float spriteHalf = sr != null && sr.sprite != null ? sr.sprite.bounds.extents.y : 0.5f;
        float halfHeight = spriteHalf * Mathf.Abs(emergeScale.y);
        transform.position = emergePosition + new Vector2(0f, -halfHeight * (1f - eased));
    }

    public void SetTelegraph(bool on) => Telegraphing = on;

    public void Knockback(Vector2 velocity)
    {
        if (Emerging) return;
        float k = 1f - knockbackResist;
        knockback = velocity * k;
        stunTimer = Mathf.Max(stunTimer, 0.12f * k);
    }

    public void Slow(float factor, float duration)
    {
        slowFactor = Mathf.Min(slowTimer > 0f ? slowFactor : 1f, factor);
        slowTimer = Mathf.Max(slowTimer, duration);
    }

    public void Face(Vector2 direction)
    {
        if (monsterAnimator != null) monsterAnimator.Face(direction);
    }

    void Update()
    {
        if (Sinking)
        {
            sinkTimer -= Time.deltaTime;
            ApplyRise(Mathf.Clamp01(sinkTimer / sinkDuration));
            desiredVelocity = Vector2.zero;
            if (!Sinking)
            {
                Burrowed = true;
                SetPresent(false);
            }
            return;
        }
        if (Burrowed)
        {
            desiredVelocity = Vector2.zero;
            return;
        }
        if (Emerging)
        {
            emergeTimer -= Time.deltaTime;
            UpdateEmerge();
            desiredVelocity = Vector2.zero;
            if (!Emerging)
            {
                transform.localScale = emergeScale;
                transform.position = emergePosition;
                if (rb != null) rb.position = emergePosition;
                MeasureFeet();
            }
            return;
        }

        if (player == null) return;
        if (slowTimer > 0f) slowTimer -= Time.deltaTime;

        if (playerHealth != null && playerHealth.IsDead)
        {
            desiredVelocity = Vector2.zero;
            Telegraphing = false;
            return;
        }

        if (stunTimer > 0f)
        {
            stunTimer -= Time.deltaTime;
            desiredVelocity = Vector2.zero;
        }
        else
        {
            switch (behaviour)
            {
                case MonsterBehaviour.Chase: Chase(); break;
                case MonsterBehaviour.Hop: Hop(); break;
                case MonsterBehaviour.Lunge: Lunge(); break;
                case MonsterBehaviour.Archer: Archer(); break;
                case MonsterBehaviour.Charger: Charger(); break;
                case MonsterBehaviour.Scripted: desiredVelocity = ScriptedVelocity; break;
                case MonsterBehaviour.Flutter: Flutter(); break;
                case MonsterBehaviour.Haunt: Haunt(); break;
                case MonsterBehaviour.Summoner: Summoner(); break;
                case MonsterBehaviour.Spirit: Spirit(); break;
            }
        }

        DamagePlayerOnContact();
    }

    void FixedUpdate()
    {
        if (Emerging) return;
        Vector2 velocity = desiredVelocity * (IsSlowed ? slowFactor : 1f) + knockback;
        knockback = Vector2.MoveTowards(knockback, Vector2.zero, 30f * Time.fixedDeltaTime);

        Vector2 current = rb != null ? rb.position : (Vector2)transform.position;
        Vector2 next = current + velocity * Time.fixedDeltaTime + Separation();
        next = KeepInsideRoom(next);

        // Don't walk into rocks, pillars, pits or pots: slide along them instead
        if (!Passable(next + footOffset))
        {
            var slideX = new Vector2(next.x, current.y);
            var slideY = new Vector2(current.x, next.y);
            if (Passable(slideX + footOffset)) next = slideX;
            else if (Passable(slideY + footOffset)) next = slideY;
            else if (Passable(current + footOffset)) next = current;
            // (if already overlapping an obstacle, let it move so it can get free)
        }

        if (rb != null) rb.MovePosition(next);
        else transform.position = next;
    }

    // Pushes this monster out of any monster it overlaps (each takes half the push; bosses barely budge)
    Vector2 Separation()
    {
        Vector2 push = Vector2.zero;
        Vector2 feet = Feet;
        foreach (var other in Active)
        {
            if (other == this) continue;
            Vector2 d = feet - other.Feet;
            float minDistance = footRadius + other.footRadius;
            float distance = d.magnitude;
            if (distance >= minDistance) continue;
            if (distance < 0.001f)
            {
                d = Random.insideUnitCircle;
                distance = 0.001f;
            }
            // The lighter one moves: a boss shoves minions aside instead of being shoved
            float share = Mathf.Clamp01(0.5f + (other.knockbackResist - knockbackResist) * 0.5f);
            push += d / distance * (minDistance - distance) * share;
        }
        return Vector2.ClampMagnitude(push, 0.25f);
    }

    // The collider that's actually switched on (a prefab may keep a disabled spare)
    public static Collider2D ActiveCollider(GameObject go)
    {
        foreach (var col in go.GetComponents<Collider2D>())
            if (col.enabled && !col.isTrigger) return col;
        return go.GetComponent<Collider2D>();
    }

    // Keeps the monster's whole body (its collider, however big) inside the room's floor
    Vector2 KeepInsideRoom(Vector2 position)
    {
        if (ownCollider == null) return RoomBounds.Clamp(position, 0.4f);
        Rect r = RoomBounds.Interior;
        Vector2 e = ownCollider.bounds.extents;
        float x = Mathf.Clamp(position.x + footOffset.x, r.xMin + e.x, r.xMax - e.x) - footOffset.x;
        float y = Mathf.Clamp(position.y + footOffset.y, r.yMin + e.y, r.yMax - e.y) - footOffset.y;
        return new Vector2(x, y);
    }

    // ---------------------------------------------------------------- path finding

    Vector2 Feet => (Vector2)transform.position + footOffset;

    bool Passable(Vector2 feet)
    {
        var room = Room.Current;
        if (room == null || movement == MonsterMovement.Phase) return true;
        return movement == MonsterMovement.Fly ? room.Grid.AreaFlyable(feet, footRadius) : room.Grid.AreaWalkable(feet, footRadius);
    }

    bool LinePassable(Vector2 from, Vector2 to)
    {
        var room = Room.Current;
        if (room == null || movement == MonsterMovement.Phase) return true;
        return movement == MonsterMovement.Fly ? room.Grid.LineFlyable(from, to, footRadius) : room.Grid.LineWalkable(from, to, footRadius);
    }

    // The direction to walk toward the knight (any angle): straight at him when the way is clear,
    // otherwise toward the next tiles on the flow field around obstacles.
    Vector2 PathDirection()
    {
        var room = Room.Current;
        Vector2 toPlayer = ToPlayer;
        if (room == null || LinePassable(Feet, (Vector2)player.position + footOffset))
            return toPlayer.sqrMagnitude > 0.0001f ? toPlayer.normalized : Vector2.zero;

        var grid = room.Grid;
        var here = grid.ToTile(Feet);
        var next = grid.NextStep(here);
        if (next == here) return toPlayer.normalized;

        // Aim for the tile after next when it's in a clear straight line, so the path cuts corners smoothly
        var after = grid.NextStep(next);
        Vector2 target = grid.TileCenter(next);
        if (after != next && grid.LineWalkable(Feet, grid.TileCenter(after), footRadius)) target = grid.TileCenter(after);
        Vector2 delta = target - Feet;
        return delta.sqrMagnitude > 0.0001f ? delta.normalized : Vector2.zero;
    }

    bool ClearLineTo(Vector2 point) => LinePassable(Feet, point + footOffset);

    // ---------------------------------------------------------------- behaviours

    string Kind => ownHealth != null ? ownHealth.kind : null;
    float Pitch => ownHealth != null ? ownHealth.VoicePitch : 1f;

    // Zombies groan now and then while they shamble about
    float ambientTimer = -1f;
    void AmbientSound()
    {
        if (Kind != "Zombie") return;
        if (ambientTimer < 0f) ambientTimer = Random.Range(2f, 6f);
        ambientTimer -= Time.deltaTime;
        if (ambientTimer > 0f) return;
        ambientTimer = Random.Range(4f, 9f);
        Audio.Play("ZombieGroan", 0.4f, Pitch);
    }

    void Chase()
    {
        AmbientSound();
        if (ToPlayer.sqrMagnitude < 0.0025f)
        {
            desiredVelocity = Vector2.zero; // on top of the player
            return;
        }
        moveDirection = PathDirection();
        Face(moveDirection);
        desiredVelocity = moveDirection * speed;
    }

    // Hops back to back, each one matching the 6-frame hop animation (0.5 s): crouch, leap, splat
    void Hop()
    {
        stateTimer -= Time.deltaTime;
        if (stateTimer <= 0f)
        {
            stateTimer = 0.5f;
            moveDirection = PathDirection();
            Face(moveDirection);
            if (monsterAnimator != null) monsterAnimator.RestartWalk();   // keep the leap in time with the movement
            if (Kind == "Mimic")
            {
                if (ToPlayer.magnitude < 2.5f) MonsterVoice.Attack(Kind, Pitch, 0.6f);   // snapping its jaws
            }
            else Audio.Play("SlimeHop", 0.25f, Pitch);
        }
        bool wasAirborne = stateTimer + Time.deltaTime < 0.42f && stateTimer + Time.deltaTime > 0.08f;
        bool airborne = stateTimer < 0.42f && stateTimer > 0.08f;          // not while crouching / landing
        if (wasAirborne && !airborne && stateTimer <= 0.08f) Audio.Play("SlimeLand", 0.25f, Pitch);
        desiredVelocity = airborne ? moveDirection * speed * hopSpeedMultiplier : Vector2.zero;
    }

    void Lunge()
    {
        attackCooldown -= Time.deltaTime;
        Vector2 toPlayer = ToPlayer;
        switch (state)
        {
            case 0:                              // chasing
                Chase();
                if (attackCooldown <= 0f && toPlayer.magnitude < 3.2f && ClearLineTo(player.position))
                {
                    state = 1;
                    stateTimer = 0.45f;
                    Telegraphing = true;
                    Face(toPlayer);
                    MonsterVoice.Attack(Kind, Pitch, 0.6f);
                }
                break;
            case 1:                              // winding up
                desiredVelocity = Vector2.zero;
                stateTimer -= Time.deltaTime;
                if (stateTimer <= 0f)
                {
                    state = 2;
                    stateTimer = 0.3f;
                    Telegraphing = false;
                    lockedDirection = toPlayer.normalized;
                }
                break;
            case 2:                              // lunging
                desiredVelocity = lockedDirection * speed * 4f;
                stateTimer -= Time.deltaTime;
                if (stateTimer <= 0f)
                {
                    state = 0;
                    attackCooldown = 2f;
                }
                break;
        }
    }

    void Archer()
    {
        Vector2 toPlayer = ToPlayer;
        float distance = toPlayer.magnitude;
        var room = Room.Current;
        bool canSee = room == null || room.Grid.LineClearForShots(transform.position, player.position);
        bool inRange = distance <= shootRange && canSee;

        if (!inRange) moveDirection = PathDirection();                       // get closer
        else if (distance < 3.5f) moveDirection = -toPlayer.normalized;      // back off
        else moveDirection = Vector2.zero;
        desiredVelocity = moveDirection * speed;
        Face(toPlayer);   // always looks at the player, even when backing away

        attackCooldown -= Time.deltaTime;
        Telegraphing = inRange && attackCooldown < 0.4f;
        if (attackCooldown > 0f || !inRange) return;

        attackCooldown = shootInterval + Random.Range(-shootIntervalJitter, shootIntervalJitter);
        Telegraphing = false;
        MonsterVoice.Attack(Kind, Pitch, 0.6f);
        Vector2 from = (Vector2)transform.position + toPlayer.normalized * 0.4f;
        var bone = Projectile.Spawn("Effects/Bone", from, toPlayer.normalized * projectileSpeed, projectileDamage, true);
        bone.spin = true;
        bone.puffColor = new Color(0.95f, 0.93f, 0.85f);
    }

    void Charger()
    {
        attackCooldown -= Time.deltaTime;
        Vector2 toPlayer = ToPlayer;
        switch (state)
        {
            case 0:                              // chasing
                Chase();
                if (attackCooldown <= 0f && toPlayer.magnitude < 7f && ClearLineTo(player.position))
                {
                    state = 1;
                    stateTimer = 0.6f;
                    Telegraphing = true;
                    lockedDirection = toPlayer.normalized;
                    Face(lockedDirection);
                    MonsterVoice.Attack(Kind, Pitch, 0.7f);
                }
                break;
            case 1:                              // winding up
                desiredVelocity = Vector2.zero;
                stateTimer -= Time.deltaTime;
                if (stateTimer <= 0f)
                {
                    state = 2;
                    stateTimer = 0.75f;
                    Telegraphing = false;
                }
                break;
            case 2:                              // charging until it runs out of time or hits something
                desiredVelocity = lockedDirection * speed * 4.5f;
                stateTimer -= Time.deltaTime;
                Vector2 ahead = Feet + lockedDirection * (footRadius + 0.2f);
                var room = Room.Current;
                bool hitWall = !RoomBounds.Contains(ahead) || (room != null && !room.Grid.AreaWalkable(ahead, 0.1f));
                if (stateTimer <= 0f || hitWall)
                {
                    if (hitWall)
                    {
                        Fx.Shake(0.12f, 0.15f);
                        Audio.Play("OrcStomp", 0.6f);
                    }
                    state = 0;
                    attackCooldown = 3.5f;
                }
                break;
        }
    }

    // Bats: weave erratically toward the knight, and every few seconds swoop straight at him
    private float weaveTime = -1f;
    private float weaveSeed;
    void Flutter()
    {
        if (weaveTime < 0f)
        {
            weaveTime = Random.value * 10f;
            weaveSeed = Random.value * 100f;
            attackCooldown = Random.Range(1.5f, 3f);
        }
        weaveTime += Time.deltaTime;
        attackCooldown -= Time.deltaTime;
        Vector2 toPlayer = ToPlayer;

        if (state == 1)                          // swooping
        {
            desiredVelocity = lockedDirection * speed * 2.4f;
            stateTimer -= Time.deltaTime;
            if (stateTimer <= 0f)
            {
                state = 0;
                attackCooldown = Random.Range(2f, 3.5f);
            }
            return;
        }

        Vector2 dir = PathDirection();
        Vector2 side = new Vector2(-dir.y, dir.x);
        float jitter = (Mathf.PerlinNoise(weaveTime * 1.7f, weaveSeed) - 0.5f) * 1.4f;
        moveDirection = (dir + side * (Mathf.Sin(weaveTime * 5f) * 0.8f + jitter)).normalized;
        Face(moveDirection);
        desiredVelocity = moveDirection * speed;

        if (attackCooldown <= 0f && toPlayer.magnitude < 4f && ClearLineTo(player.position))
        {
            state = 1;
            stateTimer = 0.35f;
            lockedDirection = toPlayer.normalized;
            MonsterVoice.Attack(Kind, Pitch, 0.5f);
        }
        else if (Random.value < Time.deltaTime * 0.5f) Audio.Play("BatFlap", 0.25f, Pitch);
    }

    // Ghosts: drift straight at the knight through everything; every few seconds they fade out
    // (can't be hit, don't hurt) and drift a little faster, then fade back in with a "wooo"
    private float hauntTimer = -1f;
    private int hauntState;                       // 0 visible, 1 fading out, 2 faded, 3 fading in
    public bool Faded => hauntState == 2 || hauntState == 3;
    void Haunt()
    {
        if (hauntTimer < 0f) hauntTimer = Random.Range(2.5f, 4.5f);
        hauntTimer -= Time.deltaTime;
        Vector2 toPlayer = ToPlayer;
        moveDirection = toPlayer.sqrMagnitude > 0.01f ? toPlayer.normalized : Vector2.zero;
        Face(moveDirection);
        desiredVelocity = moveDirection * speed * (hauntState == 2 ? 1.4f : 1f);

        float visible = 1f;
        switch (hauntState)
        {
            case 0:
                if (hauntTimer <= 0f) { hauntState = 1; hauntTimer = 0.4f; }
                break;
            case 1:
                visible = Mathf.Clamp01(hauntTimer / 0.4f);
                if (hauntTimer <= 0f)
                {
                    hauntState = 2;
                    hauntTimer = 1.5f;
                    if (ownCollider != null) ownCollider.enabled = false;   // swords and spells pass through
                }
                break;
            case 2:
                visible = 0f;
                if (hauntTimer <= 0f)
                {
                    hauntState = 3;
                    hauntTimer = 0.4f;
                    MonsterVoice.Attack(Kind, Pitch, 0.5f);
                }
                break;
            case 3:
                visible = 1f - Mathf.Clamp01(hauntTimer / 0.4f);
                if (hauntTimer <= 0f)
                {
                    hauntState = 0;
                    hauntTimer = Random.Range(3.5f, 5f);
                    if (ownCollider != null) ownCollider.enabled = true;
                }
                break;
        }
        if (ownHealth != null)
        {
            var c = ownHealth.BaseColor;
            c.a = Mathf.Lerp(0.12f, 1f, visible);
            ownHealth.SetBaseColor(c);
        }
    }

    // Necromancers: keep 4-6 units away; every few seconds chant (telegraphed) and call up a
    // Spirit (where a monster died, if any; two at most). Spirits can't be killed - they fade
    // away when their necromancer dies. With two spirits already out, it flings a slow green orb.
    private readonly List<EnemyHealth> raised = new List<EnemyHealth>();
    void Summoner()
    {
        Vector2 toPlayer = ToPlayer;
        float distance = toPlayer.magnitude;
        attackCooldown -= Time.deltaTime;
        if (state == 1)                          // chanting
        {
            desiredVelocity = Vector2.zero;
            stateTimer -= Time.deltaTime;
            if (stateTimer <= 0f)
            {
                state = 0;
                Telegraphing = false;
                attackCooldown = Random.Range(4.5f, 6f);
                FinishCast(toPlayer);
            }
            return;
        }

        if (distance > 6f || !ClearLineTo(player.position)) moveDirection = PathDirection();
        else if (distance < 4f) moveDirection = -toPlayer.normalized;
        else moveDirection = Vector2.zero;
        desiredVelocity = moveDirection * speed;
        Face(toPlayer);

        if (attackCooldown <= 0f && distance < 9f)
        {
            state = 1;
            stateTimer = 0.8f;
            Telegraphing = true;
            MonsterVoice.Attack(Kind, Pitch, 0.6f);
        }
    }

    void FinishCast(Vector2 toPlayer)
    {
        raised.RemoveAll(h => h == null || h.IsDead);
        var gm = GameManager.Instance;
        var glow = new Color(0.45f, 1f, 0.55f);
        if (gm != null && raised.Count < 2)
        {
            if (!gm.TakeCorpse(out Vector2 spot))
                spot = RoomBounds.Clamp((Vector2)transform.position + Random.insideUnitCircle.normalized * 1.3f, 0.8f);
            var spirit = gm.SpawnMinion("Spirit", spot);
            if (spirit != null)
            {
                raised.Add(spirit);
                spirit.Invulnerable = () => true;
                if (raised.Count == 1 && ownHealth != null) ownHealth.Died += ReleaseSpirits;
            }
            Fx.Puff(spot, glow, 12, 3.5f, 1.2f);
            Fx.Ring(spot, 1.2f, glow, 0.35f);
            MonsterVoice.Emerge("Spirit", 1f, 0.8f);
            return;
        }
        if (toPlayer.sqrMagnitude < 0.01f) return;
        var orb = Projectile.Spawn("Effects/SoulFire", (Vector2)transform.position + toPlayer.normalized * 0.4f, toPlayer.normalized * 3.5f, projectileDamage, true);
        orb.puffColor = glow;
        Audio.Play("EnemyShot", 0.6f, 0.8f);
    }

    // The necromancer died: its spirits go with it
    void ReleaseSpirits(EnemyHealth necromancer)
    {
        foreach (var spirit in raised)
            if (spirit != null && !spirit.IsDead) spirit.ForceKill();
        raised.Clear();
    }

    // Spirits: drift around the knight at 3-5 units (circling), spitting slow soul-fire every few seconds
    private float orbitSign;
    void Spirit()
    {
        if (orbitSign == 0f)
        {
            orbitSign = Random.value < 0.5f ? -1f : 1f;
            attackCooldown = Random.Range(1.5f, 3f);
        }
        Vector2 toPlayer = ToPlayer;
        float distance = toPlayer.magnitude;
        Vector2 dir = distance > 0.01f ? toPlayer / distance : Vector2.right;
        Vector2 around = new Vector2(-dir.y, dir.x) * orbitSign;
        Vector2 radial = distance > 5f ? dir : distance < 3f ? -dir : Vector2.zero;
        moveDirection = (around * 0.8f + radial).normalized;
        Face(toPlayer);
        desiredVelocity = moveDirection * speed;

        attackCooldown -= Time.deltaTime;
        Telegraphing = attackCooldown < 0.35f;
        if (attackCooldown > 0f) return;
        attackCooldown = 3f + Random.Range(-0.5f, 0.5f);
        Telegraphing = false;
        var shot = Projectile.Spawn("Effects/SoulFire", (Vector2)transform.position + dir * 0.4f, dir * 3f, projectileDamage, true);
        shot.puffColor = new Color(0.5f, 1f, 0.6f);
        MonsterVoice.Attack(Kind, Pitch, 0.6f);
        if (Random.value < 0.25f) orbitSign = -orbitSign;   // changes direction now and then
    }

    void DamagePlayerOnContact()
    {
        if (playerHealth == null || contactDamage <= 0 || ownCollider == null || playerCollider == null) return;
        if (ownHealth != null && ownHealth.IsDead) return;
        // A distance Unity can't measure (e.g. a disabled collider) must never count as touching
        var gap = ownCollider.Distance(playerCollider);
        if (gap.isValid && gap.distance <= 0.02f)
            playerHealth.TakeDamage(contactDamage, transform.position);
    }

    // Player angle around the monster (0° = right, counter-clockwise):
    // 315°-45° right, 45°-135° up, 135°-225° left, 225°-315° down.
    // The current direction is kept until the player is `hysteresis` degrees past its boundary.
    public static Vector2 CardinalDirection(Vector2 toPlayer, Vector2 current, float hysteresis)
    {
        float angle = Mathf.Atan2(toPlayer.y, toPlayer.x) * Mathf.Rad2Deg;
        if (angle < 0f) angle += 360f;

        if (current != Vector2.zero)
        {
            float currentAngle = Mathf.Atan2(current.y, current.x) * Mathf.Rad2Deg;
            if (Mathf.Abs(Mathf.DeltaAngle(angle, currentAngle)) <= 45f + hysteresis) return current;
        }

        if (angle >= 315f || angle < 45f) return Vector2.right;
        if (angle < 135f) return Vector2.up;
        if (angle < 225f) return Vector2.left;
        return Vector2.down;
    }
}
