using System.Collections;
using UnityEngine;

public enum ChampionTrait { Tough, Swift, Volatile, Splitting }

// A rare, tougher version of a monster: tinted, a little bigger, with a faint coloured aura and
// one trait. Added by the GameManager at spawn time.
//   Tough      (red)     double health
//   Swift      (yellow)  half again as fast
//   Volatile   (orange)  on death it swells and flashes for ~0.8 s (with a warning ring), then
//                        explodes; the blast hurts the knight if he's still inside the ring
//   Splitting  (purple)  splits into two half-size copies when it dies
public class Champion : MonoBehaviour
{
    public ChampionTrait trait;

    public const float FuseTime = 0.8f;
    public const float BlastRadius = 1.8f;

    public Color Tint => TintOf(trait);

    public static Color TintOf(ChampionTrait trait) => trait switch
    {
        ChampionTrait.Tough => new Color(1f, 0.45f, 0.45f),
        ChampionTrait.Swift => new Color(1f, 0.95f, 0.4f),
        ChampionTrait.Volatile => new Color(1f, 0.62f, 0.28f),
        _ => new Color(0.78f, 0.5f, 1f),
    };

    float auraTimer;

    void Update()
    {
        // A few coloured motes drifting up around it
        auraTimer -= Time.deltaTime;
        if (auraTimer > 0f) return;
        auraTimer = 0.12f;
        var sr = Fx.SpawnSprite("Aura", "Effects/Pixel", (Vector2)transform.position + Random.insideUnitCircle * 0.5f,
                                Fx.EffectOrder, new Color(Tint.r, Tint.g, Tint.b, 0.8f), Random.Range(0.8f, 1.3f));
        var p = sr.gameObject.AddComponent<FxParticle>();
        p.velocity = new Vector2(Random.Range(-0.2f, 0.2f), Random.Range(0.8f, 1.4f));
        p.life = 0.6f;
        p.drag = 0.5f;
        p.shrink = true;
    }

    // Volatile champions: the body stays put, swells and flashes faster and faster, then blows up
    public static void StartFuse(Vector2 position, Sprite sprite, bool flipX, Vector3 scale, int sortingOrder)
    {
        var go = new GameObject("VolatileFuse");
        go.transform.position = position;
        go.transform.localScale = scale;
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = sprite;
        sr.flipX = flipX;
        sr.sortingOrder = sortingOrder;
        go.AddComponent<VolatileFuse>();
    }
}

public class VolatileFuse : MonoBehaviour
{
    IEnumerator Start()
    {
        var sr = GetComponent<SpriteRenderer>();
        Vector3 scale = transform.localScale;
        var ring = Fx.SpawnSprite("BlastWarning", "Effects/Ring", transform.position, Fx.FloorOrder, new Color(1f, 0.15f, 0.1f, 0.55f), Champion.BlastRadius);
        Audio.Play("BombFuse", 0.8f, 1.4f);
        for (float t = 0f; t < Champion.FuseTime; t += Time.deltaTime)
        {
            float k = t / Champion.FuseTime;
            float rate = Mathf.Lerp(5f, 22f, k);
            sr.color = Mathf.Repeat(t * rate, 1f) < 0.5f ? new Color(1f, 0.55f, 0.2f) : Color.white;
            transform.localScale = scale * (1f + 0.35f * k);
            ring.color = new Color(1f, 0.15f, 0.1f, 0.35f + 0.4f * Mathf.Repeat(t * rate, 1f));
            yield return null;
        }
        Destroy(ring.gameObject);
        Explosion.Blast(transform.position, Champion.BlastRadius, 30, new Color(1f, 0.55f, 0.2f), 8f, hurtsKnight: true);
        Destroy(gameObject);
    }
}
