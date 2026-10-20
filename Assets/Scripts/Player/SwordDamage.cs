using System.Collections.Generic;
using UnityEngine;

// Damage dealt by the sword. SwordFollow calls BeginSwing() at the start of each swing and
// TryHit() for every enemy the blade passes over; each enemy is only hit once per swing.
public class SwordDamage : MonoBehaviour
{
    public int damage = 10;
    [Tooltip("How far enemies are knocked back by a hit.")]
    public float knockback = 6f;

    private readonly HashSet<EnemyHealth> hitThisSwing = new HashSet<EnemyHealth>();
    private PlayerAbilities abilities;

    // Base damage plus Stronger Sword upgrades
    public int Damage => damage + (abilities != null ? abilities.SwordBonusDamage : 0);

    public void SetAbilities(PlayerAbilities playerAbilities)
    {
        abilities = playerAbilities;
    }

    public void BeginSwing()
    {
        hitThisSwing.Clear();
    }

    public void TryHit(EnemyHealth enemy, Vector2 from)
    {
        if (enemy == null || enemy.IsDead || !hitThisSwing.Add(enemy)) return;
        enemy.TakeDamage(Damage, from, knockback);
        Fx.Shake(0.05f, 0.06f);
        Audio.Play("SwordHit", 0.8f);
        // Hit freeze: a split-second stop on contact makes the hit feel solid
        TimeControl.HitStop(enemy.isBoss ? 0.08f : 0.04f);
        // a little dust kicked up under the enemy as it's knocked back
        Fx.Puff((Vector2)enemy.transform.position + new Vector2(0f, -0.35f), new Color(0.6f, 0.56f, 0.5f), 5, 2.5f, 0.9f);
    }
}
