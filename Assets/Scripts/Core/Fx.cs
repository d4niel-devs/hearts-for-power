using System.Collections.Generic;
using UnityEngine;

// Small visual effects (puffs, rings, afterimages, screen shake) and sprite loading.
// Sprites live in Assets/Resources/Sprites and are made by Visuals/fx_generator/fx.py.
public static class Fx
{
    // Sorting orders. Characters, bombs and pedestals share an order and are sorted by height on screen.
    public const int FloorOrder = 0;
    public const int CharacterOrder = 1;
    public const int ProjectileOrder = 3;
    public const int EffectOrder = 4;

    static readonly Dictionary<string, Sprite> sprites = new Dictionary<string, Sprite>();
    static Material lineMaterial;

    public static Sprite Sprite(string path)
    {
        if (!sprites.TryGetValue(path, out Sprite sprite) || sprite == null)
        {
            sprite = Resources.Load<Sprite>("Sprites/" + path);
            if (sprite == null) Debug.LogWarning($"Fx: missing sprite Resources/Sprites/{path}");
            sprites[path] = sprite;
        }
        return sprite;
    }

    public static Material LineMaterial
    {
        get
        {
            if (lineMaterial == null) lineMaterial = new Material(Shader.Find("Sprites/Default"));
            return lineMaterial;
        }
    }

    public static SpriteRenderer SpawnSprite(string name, string spritePath, Vector2 position, int order, Color color, float scale = 1f)
    {
        var go = new GameObject(name);
        go.transform.position = position;
        go.transform.localScale = new Vector3(scale, scale, 1f);
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = Sprite(spritePath);
        sr.sortingOrder = order;
        sr.color = color;
        return sr;
    }

    // A burst of little square pixels flying outwards
    public static void Puff(Vector2 position, Color color, int count = 10, float speed = 4f, float size = 1f)
    {
        for (int i = 0; i < count; i++)
        {
            var sr = SpawnSprite("Puff", "Effects/Pixel", position, EffectOrder, color, size * Random.Range(0.8f, 1.6f));
            var p = sr.gameObject.AddComponent<FxParticle>();
            p.velocity = Random.insideUnitCircle.normalized * speed * Random.Range(0.35f, 1f);
            p.life = Random.Range(0.25f, 0.5f);
            p.shrink = true;
        }
    }

    // An expanding outline circle, e.g. for explosions
    public static void Ring(Vector2 position, float radius, Color color, float life = 0.3f)
    {
        // The ring sprite is 2 units across, so scale = radius
        var sr = SpawnSprite("Ring", "Effects/Ring", position, EffectOrder, color, radius * 0.2f);
        var p = sr.gameObject.AddComponent<FxParticle>();
        p.life = life;
        p.endScale = radius;
    }

    // A fading copy of a sprite (dash afterimages)
    public static void Ghost(SpriteRenderer source, Color color, float life)
    {
        if (source == null || source.sprite == null) return;
        var go = new GameObject("Ghost");
        go.transform.SetPositionAndRotation(source.transform.position, source.transform.rotation);
        go.transform.localScale = source.transform.lossyScale;
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = source.sprite;
        sr.flipX = source.flipX;
        sr.color = color;
        sr.sortingOrder = source.sortingOrder - 1;
        go.AddComponent<FxParticle>().life = life;
    }

    public static void Shake(float amount, float duration) => RoomCamera.Shake(amount, duration);
}

// Moves, shrinks/grows and fades a sprite, then removes it
public class FxParticle : MonoBehaviour
{
    public Vector2 velocity;
    public float life = 0.4f;
    public float drag = 3f;
    public bool shrink;
    public bool fade = true;
    public bool blink;
    public float endScale = -1f;   // when >= 0 the scale moves towards this over the particle's life

    float age;
    Vector3 startScale;
    SpriteRenderer sr;
    Color startColor;

    void Start()
    {
        startScale = transform.localScale;
        sr = GetComponent<SpriteRenderer>();
        if (sr != null) startColor = sr.color;
    }

    void Update()
    {
        age += Time.deltaTime;
        float t = age / life;
        if (t >= 1f)
        {
            Destroy(gameObject);
            return;
        }

        transform.position += (Vector3)(velocity * Time.deltaTime);
        velocity *= Mathf.Max(0f, 1f - drag * Time.deltaTime);

        if (endScale >= 0f) transform.localScale = Vector3.Lerp(startScale, new Vector3(endScale, endScale, 1f), t);
        else if (shrink) transform.localScale = startScale * (1f - t);

        if (sr == null) return;
        Color c = startColor;
        if (fade) c.a *= 1f - t;
        if (blink) c.a *= Mathf.Repeat(age * 8f, 1f) < 0.6f ? 1f : 0.35f;
        sr.color = c;
    }
}

// Fades out a LineRenderer (lightning) and removes it
public class FxLineFade : MonoBehaviour
{
    public float life = 0.2f;
    float age;
    LineRenderer line;
    Color start, end;

    void Start()
    {
        line = GetComponent<LineRenderer>();
        start = line.startColor;
        end = line.endColor;
    }

    void Update()
    {
        age += Time.deltaTime;
        float k = 1f - age / life;
        if (k <= 0f)
        {
            Destroy(gameObject);
            return;
        }
        line.startColor = new Color(start.r, start.g, start.b, start.a * k);
        line.endColor = new Color(end.r, end.g, end.b, end.a * k);
    }
}
