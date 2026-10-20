using System.Collections.Generic;
using UnityEngine;

// Instant bolt of lightning from the knight to the wall, hitting every enemy along the line.
public static class LightningStrike
{
    const float HitWidth = 0.8f;

    public static void Fire(Vector2 origin, Vector2 direction, int damage)
    {
        direction = direction.normalized;
        float length = Mathf.Max(0.5f, RoomBounds.DistanceToEdge(origin, direction));
        // Stops at the first rock, pillar or pot (breaking pots)
        var room = Room.Current;
        if (room != null)
        {
            float blocked = room.Grid.ShotDistance(origin, direction, length);
            if (blocked < length)
            {
                length = Mathf.Max(0.5f, blocked);
                room.ShotHit(origin + direction * (blocked + 0.1f));
            }
        }
        Vector2 end = origin + direction * length;

        // Everything inside a long thin box along the bolt
        float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
        var hit = new HashSet<EnemyHealth>();
        foreach (var col in Physics2D.OverlapBoxAll(origin + direction * length / 2f, new Vector2(length, HitWidth), angle))
        {
            var enemy = col.GetComponentInParent<EnemyHealth>();
            if (enemy != null && !enemy.IsDead && hit.Add(enemy))
                enemy.TakeDamage(damage, (Vector2)enemy.transform.position - direction, 2f);
        }

        // A wide yellow glow with a thin white core, both jagged and fading fast
        Vector3[] points = Jagged(origin, end);
        MakeLine(points, 0.32f, new Color(1f, 0.85f, 0.25f, 0.8f));
        MakeLine(points, 0.12f, Color.white);
        Fx.Puff(end, new Color(1f, 0.9f, 0.4f), 10, 4f);
        Fx.Shake(0.12f, 0.12f);
    }

    static Vector3[] Jagged(Vector2 from, Vector2 to)
    {
        int segments = Mathf.Max(2, Mathf.CeilToInt(Vector2.Distance(from, to) / 0.45f));
        Vector2 side = Vector2.Perpendicular((to - from).normalized);
        var points = new Vector3[segments + 1];
        for (int i = 0; i <= segments; i++)
        {
            Vector2 p = Vector2.Lerp(from, to, i / (float)segments);
            if (i > 0 && i < segments) p += side * Random.Range(-0.18f, 0.18f);
            points[i] = p;
        }
        return points;
    }

    static void MakeLine(Vector3[] points, float width, Color color)
    {
        var go = new GameObject("Lightning");
        var line = go.AddComponent<LineRenderer>();
        line.material = Fx.LineMaterial;
        line.positionCount = points.Length;
        line.SetPositions(points);
        line.widthMultiplier = width;
        line.startColor = line.endColor = color;
        line.sortingOrder = Fx.EffectOrder;
        line.numCapVertices = 2;
        go.AddComponent<FxLineFade>().life = 0.18f;
    }
}
