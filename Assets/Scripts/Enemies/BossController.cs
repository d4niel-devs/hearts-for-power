using System.Collections;
using UnityEngine;

public enum BossType { KingSlime, OrcWarlord, AncientLich }

// Attack patterns for the two bosses. Movement goes through EnemyChase (behaviour = Scripted),
// so bosses still stay inside the room and deal contact damage.
//   King Slime: winds up and leaps at the knight. Every landing is a slam that hurts him if he's
//               close; every 3rd landing also splashes a ring of slime balls, and every 10th
//               calls in small slimes.
//   Orc Warlord: stomps toward the knight, winds up and charges, then slams the ground
//                (ring of rocks) and calls in goblins every second slam.
//   The Ancient Lich: shuffles toward the knight, raises his staff and casts - an aimed fan of bones
//                  and a ring of bones on alternate casts. Every 4th cast raises two skeletons, and
//                  after every 3rd he sinks into the floor and rises again far from the knight.
// From the second boss loop on (tier 2+, floor 4 and deeper) they also enrage below half health:
// faster, with bigger rings.
[RequireComponent(typeof(EnemyChase))]
public class BossController : MonoBehaviour
{
    public BossType type;
    public int tier = 1;
    [Tooltip("King Slime: how far from where it lands the slam reaches.")]
    public float slamRadius = 2.6f;
    [Tooltip("King Slime: half hearts the slam costs the knight.")]
    public int slamDamage = 2;

    private EnemyChase chase;
    private EnemyHealth health;
    private MonsterAnimator anim;
    private int phase;
    private float timer = 1.2f;
    private int cycles;
    private Vector2 locked;
    private float stepTimer;

    public string DisplayName => type switch
    {
        BossType.KingSlime => "KING SLIME",
        BossType.AncientLich => "THE ANCIENT LICH",
        _ => "ORC WARLORD",
    };
    // Only from the second loop of bosses on (floor 4+); first-loop bosses never enrage
    bool Enraged => tier >= 2 && health != null && health.health * 2 < health.MaxHealth;

    void Start()
    {
        chase = GetComponent<EnemyChase>();
        health = GetComponent<EnemyHealth>();
        anim = GetComponent<MonsterAnimator>();
        if (anim != null) anim.alwaysWalk = false;   // bosses idle between attacks
        chase.behaviour = MonsterBehaviour.Scripted;
        chase.knockbackResist = 0.9f;
    }

    void Update()
    {
        if (chase.player == null || (health != null && health.IsDead) || chase.Emerging) return;
        timer -= Time.deltaTime;
        if (type == BossType.KingSlime) KingSlime();
        else if (type == BossType.AncientLich) AncientLich();
        else OrcWarlord();
    }

    void KingSlime()
    {
        Vector2 toPlayer = chase.ToPlayer;
        switch (phase)
        {
            case 0:     // resting
                chase.ScriptedVelocity = Vector2.zero;
                if (timer > 0f) return;
                phase = 1;
                timer = Enraged ? 0.35f : 0.55f;
                chase.SetTelegraph(true);
                chase.Face(toPlayer);
                if (anim != null) anim.SetAttacking(true);
                Audio.Play("KingSlimeWobble", 0.7f);
                break;
            case 1:     // winding up
                chase.ScriptedVelocity = Vector2.zero;
                if (timer > 0f) return;
                phase = 2;
                timer = 0.55f;
                Audio.Play("SlimeHop", 0.8f, 0.55f);
                chase.SetTelegraph(false);
                locked = toPlayer.normalized;
                chase.Face(locked);
                if (anim != null)
                {
                    anim.SetAttacking(false);
                    anim.ForceMoving = true;    // leap animation
                }
                break;
            case 2:     // leaping
                chase.ScriptedVelocity = locked * (Enraged ? 8.5f : 7f);
                if (timer > 0f) return;
                Land();
                break;
        }
    }

    void Land()
    {
        phase = 0;
        timer = Enraged ? 0.6f : 1.1f;
        cycles++;
        chase.ScriptedVelocity = Vector2.zero;
        if (anim != null)
        {
            anim.ForceMoving = null;
            anim.PlaySlam();
        }
        var slimeColor = new Color(0.45f, 0.7f, 1f);
        Fx.Shake(0.25f, 0.25f);
        Fx.Ring(transform.position, slamRadius, slimeColor, 0.35f);
        Fx.Puff(transform.position, slimeColor, 16, 5f, 1.4f);

        // Every landing is a slam that hurts the knight if he's close;
        // every 3rd also splashes a ring of slime balls, every 10th calls in small slimes
        SlamDamage(slamRadius);
        Audio.Play("KingSlimeSlam");
        if (cycles % 3 == 0)
        {
            Projectile.Ring("Effects/SlimeBall", transform.position, Enraged ? 14 : 8, 4f, 1, cycles * 13f, slimeColor);
            Audio.Play("KingSlimeSplash");
        }
        if (cycles % 10 == 0) Summon("Slime", 2);
    }

    // Half hearts lost if the knight is within `radius` of the boss when it lands
    void SlamDamage(float radius)
    {
        var playerHealth = chase.player != null ? chase.player.GetComponent<PlayerHealth>() : null;
        if (playerHealth == null) return;
        if (Vector2.Distance(chase.player.position, transform.position) <= radius)
            playerHealth.TakeDamage(slamDamage, transform.position);
    }

    void OrcWarlord()
    {
        Vector2 toPlayer = chase.ToPlayer;
        switch (phase)
        {
            case 0:     // stomping toward the knight
                chase.ScriptedVelocity = toPlayer.normalized * (Enraged ? 2.6f : 2f);
                chase.Face(toPlayer);
                stepTimer -= Time.deltaTime;
                if (stepTimer <= 0f)
                {
                    stepTimer = 0.33f;   // one thud per heavy footstep
                    Audio.Play("OrcStomp", 0.45f);
                }
                if (timer > 0f) return;
                phase = 1;
                timer = Enraged ? 0.45f : 0.7f;
                chase.SetTelegraph(true);
                locked = EnemyChase.CardinalDirection(toPlayer, Vector2.zero, 0f);
                chase.Face(locked);
                if (anim != null) anim.SetAttacking(true);
                Audio.Play("OrcAxeRaise");
                break;
            case 1:     // winding up
                chase.ScriptedVelocity = Vector2.zero;
                if (timer > 0f) return;
                phase = 2;
                timer = 0.9f;
                chase.SetTelegraph(false);
                if (anim != null)
                {
                    // straight from the windup into the charge run, axe still overhead
                    anim.SetCharging(true);
                    anim.SetAttacking(false);
                }
                Audio.Play("OrcCharge");
                break;
            case 2:     // charging
                chase.ScriptedVelocity = locked * 10f;
                var room = Room.Current;
                Vector2 ahead = (Vector2)transform.position + locked * 1.6f;
                bool hitWall = !RoomBounds.Contains(ahead) || (room != null && !room.Grid.AreaWalkable(ahead, 0.3f));
                if (timer > 0f && !hitWall) return;
                phase = 3;
                timer = 0.5f;
                Slam();
                break;
            case 3:     // recovering from the slam
                chase.ScriptedVelocity = Vector2.zero;
                if (timer > 0f) return;
                phase = 0;
                timer = Enraged ? 1.6f : 2.5f;
                break;
        }
    }

    void Slam()
    {
        cycles++;
        chase.ScriptedVelocity = Vector2.zero;
        if (anim != null)
        {
            anim.SetCharging(false);
            anim.PlaySlam();    // the raised axe comes crashing down
        }
        Audio.Play("OrcSlam");
        Fx.Shake(0.35f, 0.3f);
        Fx.Ring(transform.position, 2.5f, new Color(1f, 0.45f, 0.35f), 0.4f);
        Projectile.Ring("Effects/EnemyOrb", transform.position, Enraged ? 14 : 10, 5f, 1, cycles * 17f, new Color(1f, 0.45f, 0.35f));
        if (cycles % 2 == 0) Summon("Goblin", 2);
    }

    static readonly Color BoneGlow = new Color(0.45f, 1f, 0.55f);   // necrotic green

    void AncientLich()
    {
        Vector2 toPlayer = chase.ToPlayer;
        switch (phase)
        {
            case 0:     // shuffling toward the knight (keeps a little distance)
                chase.ScriptedVelocity = toPlayer.magnitude > 3f ? toPlayer.normalized * (Enraged ? 1.8f : 1.3f) : Vector2.zero;
                chase.Face(toPlayer);
                if (timer > 0f) return;
                phase = 1;
                timer = Enraged ? 0.45f : 0.65f;
                chase.ScriptedVelocity = Vector2.zero;
                chase.SetTelegraph(true);
                chase.Face(toPlayer);
                if (anim != null) anim.SetAttacking(true);
                Audio.Play("LichWhisper", 0.7f);
                break;
            case 1:     // raising the staff
                chase.ScriptedVelocity = Vector2.zero;
                if (timer > 0f) return;
                chase.SetTelegraph(false);
                if (anim != null)
                {
                    anim.SetAttacking(false);
                    anim.PlaySlam();
                }
                Cast(toPlayer);
                phase = 2;
                timer = 0.45f;
                break;
            case 2:     // recovering from the cast
                chase.ScriptedVelocity = Vector2.zero;
                if (timer > 0f) return;
                if (cycles % 3 == 0)
                {
                    phase = 3;
                    StartCoroutine(Burrow());
                }
                else
                {
                    phase = 0;
                    timer = Enraged ? 1.2f : 2f;
                }
                break;
            case 3:     // burrowing (driven by the coroutine)
                chase.ScriptedVelocity = Vector2.zero;
                break;
        }
    }

    void Cast(Vector2 toPlayer)
    {
        cycles++;
        Vector2 orb = (Vector2)transform.position + new Vector2(0f, 0.6f);
        Fx.Ring(orb, 1.2f, BoneGlow, 0.3f);
        Fx.Shake(0.12f, 0.15f);
        Audio.Play("LichCast");
        Audio.Play("LichBones", 0.6f);
        if (cycles % 2 == 1)
        {
            // aimed fan of bones
            int count = Enraged ? 7 : 5;
            float spread = 16f;
            float baseAngle = Mathf.Atan2(toPlayer.y, toPlayer.x) * Mathf.Rad2Deg;
            for (int i = 0; i < count; i++)
            {
                float a = (baseAngle + (i - (count - 1) / 2f) * spread) * Mathf.Deg2Rad;
                var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                Bone(orb + dir * 0.5f, dir * 6f);
            }
        }
        else
        {
            // ring of bones
            int count = Enraged ? 16 : 12;
            for (int i = 0; i < count; i++)
            {
                float a = (cycles * 11f + 360f * i / count) * Mathf.Deg2Rad;
                var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                Bone(orb + dir * 0.5f, dir * 4.2f);
            }
        }
        if (cycles % 4 == 0) Summon("Skeleton", 2);
    }

    void Bone(Vector2 position, Vector2 velocity)
    {
        var p = Projectile.Spawn("Effects/Bone", position, velocity, 1, true);
        p.puffColor = BoneGlow;
        p.radius = 0.18f;
        p.spin = true;
    }

    // Sinks into the floor, travels unseen, and rises again far from the knight with a ring of bones
    IEnumerator Burrow()
    {
        var dust = new Color(0.55f, 0.5f, 0.45f);
        Fx.Puff(transform.position, dust, 14, 3.5f, 1.3f);
        Audio.Play("LichSink");
        chase.BeginSink(0.5f);
        yield return new WaitForSeconds(0.5f);
        yield return new WaitForSeconds(Enraged ? 0.4f : 0.7f);

        Vector2 target = FarSpot();
        Fx.Puff(target, dust, 18, 4f, 1.5f);
        Fx.Shake(0.15f, 0.25f);
        Audio.Play("LichSink", 1f, 1.3f);
        chase.Resurface(target, 0.5f);
        yield return new WaitWhile(() => chase.Emerging);

        Projectile.Ring("Effects/Bone", (Vector2)transform.position + new Vector2(0f, 0.3f), Enraged ? 10 : 8, 3.8f, 1, Random.Range(0f, 45f), BoneGlow);
        Audio.Play("LichBones");
        phase = 0;
        timer = Enraged ? 0.9f : 1.4f;
    }

    // A walkable spot inside the room, as far from the knight as a few random tries allow
    Vector2 FarSpot()
    {
        var room = Room.Current;
        Rect area = RoomBounds.Interior;
        Vector2 player = chase.player != null ? (Vector2)chase.player.position : area.center;
        Vector2 best = transform.position;
        float bestDistance = -1f;
        for (int i = 0; i < 24; i++)
        {
            var p = new Vector2(Random.Range(area.xMin + 1.2f, area.xMax - 1.2f), Random.Range(area.yMin + 1.2f, area.yMax - 1.2f));
            if (room != null && !room.Grid.AreaWalkable(p, 0.6f)) continue;
            float d = Vector2.Distance(p, player);
            if (d > bestDistance)
            {
                bestDistance = d;
                best = p;
            }
        }
        return best;
    }

    void Summon(string monster, int count)
    {
        if (GameManager.Instance == null) return;
        Audio.Play("Emerge", 0.8f);
        MonsterVoice.Emerge(monster, 1f, 0.6f);
        for (int i = 0; i < count; i++)
        {
            Vector2 offset = Random.insideUnitCircle.normalized * 1.8f;
            GameManager.Instance.SpawnMinion(monster, RoomBounds.Clamp((Vector2)transform.position + offset, 0.6f));
        }
    }
}
