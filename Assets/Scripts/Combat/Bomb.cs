using UnityEngine;

// A bomb dropped at the knight's feet. Its blast radius is shown on the floor; it blinks faster
// and swells as the fuse runs down, then explodes (enemies only).
public class Bomb : MonoBehaviour
{
    public float fuse = 1.2f;
    public int damage = 40;
    public float radius = 1.6f;

    private float timer;
    private SpriteRenderer spriteRenderer;
    private SpriteRenderer rangeMarker;
    private Vector3 baseScale;

    public static Bomb Drop(Vector2 position, int damage, float radius)
    {
        var sr = Fx.SpawnSprite("Bomb", "Effects/Bomb", position, Fx.CharacterOrder, Color.white, 1.4f);
        var bomb = sr.gameObject.AddComponent<Bomb>();
        bomb.damage = damage;
        bomb.radius = radius;

        // Faint ring on the floor showing how far the blast reaches (ring sprite is 2 units across)
        bomb.rangeMarker = Fx.SpawnSprite("BlastRange", "Effects/Ring", position, Fx.FloorOrder, new Color(1f, 0.5f, 0.3f, 0.35f), radius);
        bomb.rangeMarker.transform.SetParent(bomb.transform, true);
        return bomb;
    }

    void Start()
    {
        spriteRenderer = GetComponent<SpriteRenderer>();
        baseScale = transform.localScale;
        Audio.Play("BombFuse", 0.6f);
    }

    void Update()
    {
        timer += Time.deltaTime;
        float t = timer / fuse;
        if (t >= 1f)
        {
            Explosion.Blast(transform.position, radius, damage, new Color(1f, 0.6f, 0.2f), 8f);
            Destroy(gameObject);
            return;
        }

        // Blink red, faster and faster, and swell slightly
        float blinkRate = Mathf.Lerp(4f, 18f, t);
        spriteRenderer.color = Mathf.Repeat(timer * blinkRate, 1f) < 0.5f ? Color.white : new Color(1f, 0.45f, 0.45f);
        transform.localScale = baseScale * (1f + 0.15f * t);
    }
}
