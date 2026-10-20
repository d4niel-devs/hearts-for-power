using System;
using System.Collections;
using UnityEngine;

// The knight's hearts, counted in half hearts (Health 5 = two and a half hearts).
// MaxHealth is the heart containers; sacrificing for items removes containers.
// Taking damage knocks him back and makes him briefly invulnerable (he flickers).
public class PlayerHealth : MonoBehaviour
{
    [Tooltip("Heart containers at the start of a run.")]
    public int startingHearts = 3;
    [Tooltip("Most heart containers the knight can ever have.")]
    public int heartCap = 12;
    [Tooltip("Seconds of invulnerability after being hit.")]
    public float invulnerableTime = 1f;
    [Tooltip("How hard the knight is knocked away from whatever hit him.")]
    public float knockbackForce = 8f;

    public int MaxHealth { get; private set; }   // half hearts
    public int Health { get; private set; }      // half hearts
    public bool IsDead { get; private set; }
    public bool IsInvulnerable => hurtTimer > 0f || graceTimer > 0f || GodMode;
    public bool GodMode { get; set; }   // testing only (GameManager debug key F8)

    public event Action Changed;
    public event Action Hurt;     // took damage (the HUD flashes)
    public event Action Died;

    private SpriteRenderer spriteRenderer;
    private PlayerMovement movement;
    private float hurtTimer;    // after a hit: invulnerable and flickering
    private float graceTimer;   // e.g. while dashing: invulnerable, no flicker

    void Awake()
    {
        spriteRenderer = GetComponent<SpriteRenderer>();
        movement = GetComponent<PlayerMovement>();
        MaxHealth = Health = Mathf.Max(1, startingHearts) * 2;
    }

    void Update()
    {
        if (graceTimer > 0f) graceTimer -= Time.deltaTime;
        if (hurtTimer <= 0f) return;

        hurtTimer -= Time.deltaTime;
        if (spriteRenderer != null)
            spriteRenderer.enabled = hurtTimer <= 0f || Mathf.FloorToInt(hurtTimer * 15f) % 2 == 0;
    }

    // Returns true if the damage landed (false while invulnerable or dead). Damage is in half hearts.
    public bool TakeDamage(int halfHearts, Vector2 source)
    {
        if (IsDead || IsInvulnerable || halfHearts <= 0) return false;

        Health = Mathf.Max(0, Health - halfHearts);
        Vector2 away = (Vector2)transform.position - source;
        if (movement != null && away.sqrMagnitude > 0.0001f) movement.Knockback(away.normalized * knockbackForce);
        Fx.Puff(transform.position, new Color(0.9f, 0.15f, 0.25f), 12, 5f);
        Fx.Shake(0.18f, 0.2f);

        if (Health == 0) Die();
        else
        {
            hurtTimer = invulnerableTime;
            Audio.Play("PlayerHurt");
            TimeControl.HitStop(0.1f);
        }
        Hurt?.Invoke();
        Changed?.Invoke();
        return true;
    }

    public void Heal(int halfHearts)
    {
        if (IsDead || halfHearts <= 0) return;
        Health = Mathf.Min(MaxHealth, Health + halfHearts);
        Audio.Play("HeartPickup", 0.8f);
        Changed?.Invoke();
    }

    // New heart containers (in half hearts). fullHeal also refills every container.
    public void AddContainers(int halfHearts, bool fullHeal)
    {
        if (IsDead) return;
        MaxHealth = Mathf.Min(heartCap * 2, MaxHealth + halfHearts);
        Health = fullHeal ? MaxHealth : Mathf.Min(MaxHealth, Health + halfHearts);
        Audio.Play("ContainerGain", 0.9f);
        Changed?.Invoke();
    }

    // At least half a container must always remain
    public bool CanSacrifice(int halfHearts) => !IsDead && MaxHealth - halfHearts >= 1;

    // Permanently gives up heart containers; any health in them is lost too
    public bool Sacrifice(int halfHearts)
    {
        if (!CanSacrifice(halfHearts)) return false;
        MaxHealth -= halfHearts;
        Health = Mathf.Min(Health, MaxHealth);
        Audio.Play("Sacrifice");
        Changed?.Invoke();
        return true;
    }

    public void GrantInvulnerability(float seconds)
    {
        graceTimer = Mathf.Max(graceTimer, seconds);
    }

    void Die()
    {
        IsDead = true;
        hurtTimer = 0f;
        if (spriteRenderer != null) spriteRenderer.enabled = true;
        Fx.Puff(transform.position, new Color(0.9f, 0.15f, 0.25f), 30, 7f, 1.5f);
        Fx.Shake(0.4f, 0.4f);
        Audio.Play("PlayerDeath");
        TimeControl.SlowMotion(0.3f, 1.2f);   // the last moment plays out in slow motion
        StartCoroutine(DeathFall());
        Died?.Invoke();
    }

    // Spins round, topples over and greys out
    IEnumerator DeathFall()
    {
        var animator = GetComponent<Animator>();
        if (animator != null) animator.speed = 0f;
        foreach (var r in GetComponentsInChildren<SpriteRenderer>())
            if (r != spriteRenderer) r.enabled = false;              // the sword drops away
        Vector3 start = transform.position;
        const float spin = 0.55f, fall = 0.3f;
        for (float t = 0f; t < spin + fall; t += Time.deltaTime)
        {
            if (t < spin)
            {
                float k = t / spin;
                transform.rotation = Quaternion.Euler(0f, 0f, 720f * k * (2f - k));   // two turns, slowing down
                transform.position = start + new Vector3(0f, Mathf.Sin(k * Mathf.PI) * 0.35f, 0f);
            }
            else
            {
                float k = (t - spin) / fall;
                transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Lerp(0f, 90f, k));
                transform.position = start + new Vector3(0f, -0.25f * k, 0f);
            }
            if (spriteRenderer != null)
                spriteRenderer.color = Color.Lerp(Color.white, new Color(0.45f, 0.45f, 0.5f), t / (spin + fall));
            yield return null;
        }
        transform.rotation = Quaternion.Euler(0f, 0f, 90f);
        Fx.Puff(transform.position + new Vector3(0f, -0.3f, 0f), new Color(0.55f, 0.5f, 0.45f), 10, 3f, 1.2f);
    }
}
