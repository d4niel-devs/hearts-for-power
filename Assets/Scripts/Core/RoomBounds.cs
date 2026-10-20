using UnityEngine;

// The current room's floor area (Interior) and full size including walls (Outer).
// Used to keep monsters and projectiles inside the room and to frame the camera.
// Comes from Room.Current while playing; in the editor (no rooms built) it falls back to measuring
// objects named "Wall..." or a default room-sized rectangle.
public static class RoomBounds
{
    public const string DefaultWallPrefix = "Wall";
    public static readonly Rect FallbackOuter = new Rect(-Room.WidthUnits / 2f, -Room.HeightUnits / 2f, Room.WidthUnits, Room.HeightUnits);

    public static Rect Interior
    {
        get
        {
            if (Room.Current != null) return Room.Current.Interior;
            Measure(DefaultWallPrefix, FallbackOuter, out Rect inner, out _);
            return inner;
        }
    }

    public static Rect Outer
    {
        get
        {
            if (Room.Current != null) return Room.Current.Outer;
            Measure(DefaultWallPrefix, FallbackOuter, out _, out Rect outer);
            return outer;
        }
    }

    public static Vector2 Center => Interior.center;

    // Keeps a point inside the floor area, `margin` units away from the walls
    public static Vector2 Clamp(Vector2 point, float margin)
    {
        Rect r = Interior;
        return new Vector2(
            Mathf.Clamp(point.x, r.xMin + margin, r.xMax - margin),
            Mathf.Clamp(point.y, r.yMin + margin, r.yMax - margin));
    }

    public static bool Contains(Vector2 point, float margin = 0f)
    {
        Rect r = Interior;
        return point.x >= r.xMin + margin && point.x <= r.xMax - margin &&
               point.y >= r.yMin + margin && point.y <= r.yMax - margin;
    }

    // Distance from `origin` along `direction` to the inside of the walls
    public static float DistanceToEdge(Vector2 origin, Vector2 direction)
    {
        Rect r = Interior;
        float best = float.PositiveInfinity;
        if (direction.x > 0.0001f) best = Mathf.Min(best, (r.xMax - origin.x) / direction.x);
        if (direction.x < -0.0001f) best = Mathf.Min(best, (r.xMin - origin.x) / direction.x);
        if (direction.y > 0.0001f) best = Mathf.Min(best, (r.yMax - origin.y) / direction.y);
        if (direction.y < -0.0001f) best = Mathf.Min(best, (r.yMin - origin.y) / direction.y);
        return float.IsInfinity(best) ? 0f : Mathf.Max(0f, best);
    }

    // Editor fallback: walls taller than wide are left/right walls, wider than tall are top/bottom walls.
    public static bool Measure(string wallPrefix, Rect fallbackOuter, out Rect inner, out Rect outerRect)
    {
        var colliders = Object.FindObjectsByType<Collider2D>();
        Bounds all = default;
        bool any = false;
        foreach (var col in colliders)
        {
            if (!col.enabled || !col.name.StartsWith(wallPrefix)) continue;
            if (!any) { all = col.bounds; any = true; } else all.Encapsulate(col.bounds);
        }
        if (!any)
        {
            outerRect = fallbackOuter;
            inner = new Rect(fallbackOuter.x + RoomGrid.TileSize, fallbackOuter.y + RoomGrid.TileSize,
                             fallbackOuter.width - 2f * RoomGrid.TileSize, fallbackOuter.height - 2f * RoomGrid.TileSize);
            return false;
        }

        float left = float.NegativeInfinity, right = float.PositiveInfinity;
        float bottom = float.NegativeInfinity, top = float.PositiveInfinity;
        float leftOuter = all.min.x, rightOuter = all.max.x, bottomOuter = all.min.y, topOuter = all.max.y;
        foreach (var col in colliders)
        {
            if (!col.enabled || !col.name.StartsWith(wallPrefix)) continue;
            Bounds b = col.bounds;
            if (b.size.y >= b.size.x)
            {
                if (b.center.x < all.center.x) { if (b.max.x > left) { left = b.max.x; leftOuter = b.min.x; } }
                else if (b.min.x < right) { right = b.min.x; rightOuter = b.max.x; }
            }
            else
            {
                if (b.center.y < all.center.y) { if (b.max.y > bottom) { bottom = b.max.y; bottomOuter = b.min.y; } }
                else if (b.min.y < top) { top = b.min.y; topOuter = b.max.y; }
            }
        }

        inner = Rect.MinMaxRect(
            float.IsInfinity(left) ? all.min.x : left,
            float.IsInfinity(bottom) ? all.min.y : bottom,
            float.IsInfinity(right) ? all.max.x : right,
            float.IsInfinity(top) ? all.max.y : top);
        outerRect = Rect.MinMaxRect(leftOuter, bottomOuter, rightOuter, topOuter);
        if (inner.width <= 0f || inner.height <= 0f) inner = outerRect;
        return true;
    }
}
