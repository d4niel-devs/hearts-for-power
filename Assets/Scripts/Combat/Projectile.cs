using System.Collections.Generic;
using UnityEngine;

// A flying shot: the knight's spells (hostile = false) or enemy bones and boss balls (hostile = true).
// Stopped by rocks, pillars and pots (breaking pots), flies over pits.
// Sprites are drawn pointing right and are turned to face their direction of travel.
// Disappears on hitting something, leaving the room, or running out of time.
public class Projectile : MonoBehaviour
{
    public int damage;
    public bool hostile;
    public float radius = 0.2f;
    [Tooltip("Extra enemies it can pass through after the first hit.")]
    public int pierce;
    public float knockback = 3f;
    public float slowFactor = 1f;
    public float slowTime;
    [Tooltip("When > 0, explodes on impact, damaging everything in this radius.")]
    public float explodeRadius;
    public int explodeDamage;
    public Color explodeColor = Color.white;
    public Color puffColor = Color.white;
    public float lifetime = 4f;
    public bool spin;

    private Vector2 velocity;
    private readonly HashSet<EnemyHealth> alreadyHit = new HashSet<EnemyHealth>();
    private bool finished;

    public static Projectile Spawn(string sprite, Vector2 position, Vector2 velocity, int damage, bool hostile)
    {
        var sr = Fx.SpawnSprite(hostile ? "EnemyShot" : "Spell", sprite, position, Fx.ProjectileOrder, Color.white);
        var p = sr.gameObject.AddComponent<Projectile>();
        p.velocity = velocity;
        p.damage = damage;
        p.hostile = hostile;
        p.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(velocity.y, velocity.x) * Mathf.Rad2Deg);
        return p;
    }

    // `count` hostile shots flying out in a circle (boss attacks)
    public static void Ring(string sprite, Vector2 center, int count, float speed, int damage, float angleOffset, Color puff)
    {
        for (int i = 0; i < count; i++)
        {
            float a = (angleOffset + 360f * i / count) * Mathf.Deg2Rad;
            var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            var p = Spawn(sprite, center + dir * 0.6f, dir * speed, damage, true);
            p.puffColor = puff;
            p.radius = 0.18f;
        }
    }

    void Update()
    {
        if (finished) return;
        transform.position += (Vector3)(velocity * Time.deltaTime);
        if (spin) transform.Rotate(0f, 0f, 720f * Time.deltaTime);

        lifetime -= Time.deltaTime;
        if (lifetime <= 0f || !RoomBounds.Contains(transform.position, -0.1f))
        {
            Finish();
            return;
        }

        // Rocks, pillars and pots stop shots (pots break); pits don't
        var room = Room.Current;
        if (room != null && room.Grid.BlocksShotsAt(transform.position))
        {
            room.ShotHit(transform.position);
            Audio.Play("ProjectileHit", 0.4f);
            Finish();
            return;
        }

        if (hostile) CheckPlayerHit();
        else CheckEnemyHits();
    }

    void CheckPlayerHit()
    {
        foreach (var col in Physics2D.OverlapCircleAll(transform.position, radius))
        {
            var playerHealth = col.GetComponentInParent<PlayerHealth>();
            if (playerHealth == null || playerHealth.IsDead) continue;
            playerHealth.TakeDamage(damage, transform.position);
            Finish();
            return;
        }
    }

    void CheckEnemyHits()
    {
        foreach (var col in Physics2D.OverlapCircleAll(transform.position, radius))
        {
            var enemy = col.GetComponentInParent<EnemyHealth>();
            if (enemy == null || enemy.IsDead || !alreadyHit.Add(enemy)) continue;

            Vector2 from = (Vector2)transform.position - velocity.normalized;
            enemy.TakeDamage(damage, from, knockback);
            if (slowTime > 0f)
            {
                var chase = enemy.GetComponent<EnemyChase>();
                if (chase != null) chase.Slow(slowFactor, slowTime);
            }
            if (pierce-- <= 0)
            {
                Finish();
                return;
            }
        }
    }

    void Finish()
    {
        finished = true;
        if (explodeRadius > 0f) Explosion.Blast(transform.position, explodeRadius, explodeDamage, explodeColor);
        Fx.Puff(transform.position, puffColor, 5, 2.5f);
        Destroy(gameObject);
    }
}

public static class Explosion
{
    // Damages and knocks back every enemy in the radius, breaks pots and smashes rocks.
    // Only hurts the knight when hurtsKnight is set (exploding champions).
    public static void Blast(Vector2 center, float radius, int damage, Color color, float knockback = 7f, bool hurtsKnight = false)
    {
        if (hurtsKnight)
        {
            foreach (var col in Physics2D.OverlapCircleAll(center, radius))
            {
                var knight = col.GetComponentInParent<PlayerHealth>();
                if (knight == null) continue;
                knight.TakeDamage(2, center);
                break;
            }
        }
        var hit = new HashSet<EnemyHealth>();
        foreach (var col in Physics2D.OverlapCircleAll(center, radius))
        {
            var enemy = col.GetComponentInParent<EnemyHealth>();
            if (enemy != null && !enemy.IsDead && hit.Add(enemy)) enemy.TakeDamage(damage, center, knockback);
        }
        if (Room.Current != null) Room.Current.DamageArea(center, radius, smashRocks: true);
        Fx.Ring(center, radius, color, 0.3f);
        Fx.Puff(center, color, 20, 6f, 1.5f);
        Audio.Play("Explosion", Mathf.Clamp(0.45f + radius * 0.2f, 0.5f, 1f), Mathf.Lerp(1.25f, 0.9f, Mathf.InverseLerp(1.2f, 2.7f, radius)));
        Fx.Puff(center, new Color(0.3f, 0.28f, 0.3f), 10, 3f, 2f);
        Fx.Shake(0.22f, 0.22f);
    }
}
