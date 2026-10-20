using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class EnemyHealth : MonoBehaviour
{
    // Every living enemy, so the wave knows when the room is clear
    public static readonly List<EnemyHealth> Alive = new List<EnemyHealth>();

    public int health = 50;
    [Tooltip("How long the enemy flashes red after being hit.")]
    public float hitFlashTime = 0.1f;
    [Tooltip("Colour of the pixels that burst out when hit or killed.")]
    public Color puffColor = Color.white;

    [HideInInspector] public string kind;     // monster type name, set by the GameManager
    [HideInInspector] public bool isMini;     // small slime from a split
    [HideInInspector] public bool isBoss;
    [HideInInspector] public bool isChampion;

    public int MaxHealth { get; private set; }
    public bool IsDead { get; private set; }
    public event Action<EnemyHealth> Died;
    // Small monsters squeak higher, champions growl lower
    public float VoicePitch => isMini ? 1.3f : isChampion ? 0.8f : 1f;
    // Lets something else (e.g. a ghost while faded out) shrug off hits
    public Func<bool> Invulnerable;

    private SpriteRenderer spriteRenderer;
    private EnemyChase chase;
    private float flashTimer;
    private Color baseColor = Color.white;
    private static Material flashMaterial;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetStatics() => Alive.Clear();

    void Awake()
    {
        spriteRenderer = GetComponent<SpriteRenderer>();
        chase = GetComponent<EnemyChase>();
        if (spriteRenderer != null) baseColor = spriteRenderer.color;
        MaxHealth = health;
    }

    void OnEnable() { if (!IsDead) Alive.Add(this); }
    void OnDisable() => Alive.Remove(this);

    public void SetMaxHealth(int hp)
    {
        health = MaxHealth = Mathf.Max(1, hp);
    }

    public void SetBaseColor(Color color)
    {
        baseColor = color;
    }

    public Color BaseColor => baseColor;

    void Update()
    {
        if (IsDead) return;
        if (flashTimer > 0f) flashTimer -= Time.deltaTime;
        if (spriteRenderer == null) return;

        Color color = baseColor;
        if (flashTimer > 0f)
            color = new Color(1f, 0.3f, 0.3f);                                    // just hit
        else if (chase != null && chase.Telegraphing)
            color = Mathf.Repeat(Time.time * 10f, 1f) < 0.5f ? new Color(1f, 1f, 0.55f) : baseColor;   // about to attack
        else if (chase != null && chase.IsSlowed)
            color = baseColor * new Color(0.55f, 0.8f, 1f);                        // frozen
        spriteRenderer.color = color;
    }

    public void TakeDamage(int amount)
    {
        TakeDamage(amount, transform.position, 0f);
    }

    // knockback pushes the enemy away from `source`
    public void TakeDamage(int amount, Vector2 source, float knockback)
    {
        if (IsDead || amount <= 0) return;
        if (Invulnerable != null && Invulnerable())
        {
            // shrugs it off: a hollow ring, a few sparks and a little shove
            Audio.Play("SpiritImmune", 0.6f);
            Fx.Puff(transform.position, Color.white, 3, 2f, 0.8f);
            if (knockback > 0f && chase != null)
                chase.Knockback(((Vector2)transform.position - source).normalized * knockback * 0.5f);
            return;
        }

        health -= amount;
        flashTimer = hitFlashTime;
        Fx.Puff(transform.position, puffColor, 4, 2.5f);
        Audio.Play("MonsterHurt", 0.55f, VoicePitch);

        if (knockback > 0f && chase != null)
        {
            Vector2 away = (Vector2)transform.position - source;
            if (away.sqrMagnitude < 0.0001f) away = UnityEngine.Random.insideUnitCircle;
            chase.Knockback(away.normalized * knockback);
        }

        if (health <= 0) Die();
    }

    // Kills it even if it can't normally be hurt (spirits when their necromancer dies, debug keys)
    public void ForceKill()
    {
        if (IsDead) return;
        Invulnerable = null;
        TakeDamage(health + 99999);
    }

    void Die()
    {
        IsDead = true;
        Alive.Remove(this);
        MonsterVoice.Die(kind, VoicePitch);
        TimeControl.HitStop(isBoss ? 0.12f : 0.05f);

        // The body stops being part of the fight right away; it just plays its death
        foreach (var col in GetComponents<Collider2D>()) col.enabled = false;
        if (chase != null) chase.enabled = false;
        var animator = GetComponent<Animator>();
        if (animator != null) animator.speed = 0f;

        var champion = GetComponent<Champion>();
        if (isBoss) StartCoroutine(BossDeath());
        else if (champion != null && champion.trait == ChampionTrait.Volatile && spriteRenderer != null)
        {
            // the body stays behind as a ticking bomb (see VolatileFuse)
            Champion.StartFuse(transform.position, spriteRenderer.sprite, spriteRenderer.flipX, transform.localScale, spriteRenderer.sortingOrder);
            Died?.Invoke(this);
            Destroy(gameObject);
        }
        else
        {
            Fx.Shake(0.06f, 0.08f);
            Died?.Invoke(this);
            StartCoroutine(Pop());
        }
    }

    // Flash white, squash and stretch, then burst and fade
    IEnumerator Pop()
    {
        Vector3 scale = transform.localScale;
        Flash(true);
        yield return new WaitForSeconds(0.06f);
        Flash(false);
        for (float t = 0f; t < 0.18f; t += Time.deltaTime)
        {
            float k = t / 0.18f;
            float squash = Mathf.Sin(k * Mathf.PI);
            transform.localScale = new Vector3(scale.x * (1f + 0.35f * squash), scale.y * (1f - 0.45f * k), scale.z);
            if (spriteRenderer != null) spriteRenderer.color = new Color(baseColor.r, baseColor.g, baseColor.b, 1f - k);
            yield return null;
        }
        Fx.Puff(transform.position, puffColor, 14, 5f, 1.2f);
        Fx.Puff(transform.position, Color.white, 4, 3f, 0.8f);
        Destroy(gameObject);
    }

    // A boss shakes, flashes and bursts a few times before going up in one big puff
    IEnumerator BossDeath()
    {
        Vector3 start = transform.position;
        Fx.Shake(0.3f, 1.4f);
        for (int i = 0; i < 7; i++)
        {
            Flash(i % 2 == 0);
            Vector2 burst = (Vector2)start + UnityEngine.Random.insideUnitCircle * 0.9f;
            Fx.Puff(burst, puffColor, 12, 5f, 1.4f);
            Fx.Ring(burst, 1.2f, Color.white, 0.25f);
            Audio.Play("Explosion", 0.5f, 1.3f);
            for (float t = 0f; t < 0.17f; t += Time.deltaTime)
            {
                transform.position = start + (Vector3)(UnityEngine.Random.insideUnitCircle * 0.08f);
                yield return null;
            }
        }
        Flash(false);
        transform.position = start;
        Fx.Puff(start, puffColor, 45, 9f, 2f);
        Fx.Puff(start, Color.white, 16, 6f, 1.4f);
        Fx.Ring(start, 3f, puffColor, 0.5f);
        Fx.Shake(0.5f, 0.5f);
        Audio.Play("Explosion");
        Died?.Invoke(this);
        Destroy(gameObject);
    }

    // Draws the sprite as a solid white silhouette (or back to normal)
    void Flash(bool on)
    {
        if (spriteRenderer == null) return;
        if (flashMaterial == null)
        {
            var shader = Shader.Find("GUI/Text Shader");
            if (shader == null) return;
            flashMaterial = new Material(shader);
        }
        if (on)
        {
            if (!originalMaterialSaved)
            {
                originalMaterial = spriteRenderer.sharedMaterial;
                originalMaterialSaved = true;
            }
            spriteRenderer.sharedMaterial = flashMaterial;
            spriteRenderer.color = Color.white;
        }
        else if (originalMaterialSaved)
        {
            spriteRenderer.sharedMaterial = originalMaterial;
            spriteRenderer.color = baseColor;
        }
    }

    private Material originalMaterial;
    private bool originalMaterialSaved;
}
