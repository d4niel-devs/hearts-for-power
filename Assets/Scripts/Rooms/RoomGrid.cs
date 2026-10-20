using System.Collections.Generic;
using UnityEngine;

public enum TileKind { Floor, Rock, Pillar, Pit, Spikes, Pot }

// The 13x7 tile floor of one room: what's on each tile, world <-> tile conversion, line checks,
// and a flow field (distance to the knight) that monsters follow to walk around obstacles.
public class RoomGrid
{
    public const int Width = 13;
    public const int Height = 7;
    public const float TileSize = 2f;

    private readonly TileKind[,] tiles = new TileKind[Width, Height];
    private readonly int[,] distance = new int[Width, Height];
    private readonly Vector2 origin;   // world position of the bottom-left corner of tile (0,0)

    public RoomGrid(Vector2 roomCenter)
    {
        origin = roomCenter - new Vector2(Width * TileSize / 2f, Height * TileSize / 2f);
        ClearFlow();
    }

    public TileKind Get(Vector2Int t) => InBounds(t) ? tiles[t.x, t.y] : TileKind.Rock;
    public void Set(Vector2Int t, TileKind kind)
    {
        if (InBounds(t)) tiles[t.x, t.y] = kind;
    }

    public static bool InBounds(Vector2Int t) => t.x >= 0 && t.y >= 0 && t.x < Width && t.y < Height;

    public Vector2Int ToTile(Vector2 world)
    {
        Vector2 local = (world - origin) / TileSize;
        return new Vector2Int(Mathf.FloorToInt(local.x), Mathf.FloorToInt(local.y));
    }

    public Vector2 TileCenter(Vector2Int t) => origin + new Vector2((t.x + 0.5f) * TileSize, (t.y + 0.5f) * TileSize);

    // Monsters can stand here (spike traps only hurt the knight)
    public bool Walkable(Vector2Int t)
    {
        if (!InBounds(t)) return false;
        var k = tiles[t.x, t.y];
        return k == TileKind.Floor || k == TileKind.Spikes;
    }

    // Shots stop here (they fly over pits)
    public bool BlocksShots(Vector2Int t)
    {
        if (!InBounds(t)) return false;
        var k = tiles[t.x, t.y];
        return k == TileKind.Rock || k == TileKind.Pillar || k == TileKind.Pot;
    }

    public bool BlocksShotsAt(Vector2 world) => BlocksShots(ToTile(world));

    // Is a square of half-size `radius` around `center` entirely on walkable tiles?
    public bool AreaWalkable(Vector2 center, float radius)
    {
        return Walkable(ToTile(center + new Vector2(-radius, -radius))) &&
               Walkable(ToTile(center + new Vector2(radius, -radius))) &&
               Walkable(ToTile(center + new Vector2(-radius, radius))) &&
               Walkable(ToTile(center + new Vector2(radius, radius)));
    }

    // Flying monsters (bats) cross pits but not rocks, pillars or pots
    public bool Flyable(Vector2Int t)
    {
        if (!InBounds(t)) return false;
        var k = tiles[t.x, t.y];
        return k != TileKind.Rock && k != TileKind.Pillar && k != TileKind.Pot;
    }

    public bool AreaFlyable(Vector2 center, float radius)
    {
        return Flyable(ToTile(center + new Vector2(-radius, -radius))) &&
               Flyable(ToTile(center + new Vector2(radius, -radius))) &&
               Flyable(ToTile(center + new Vector2(-radius, radius))) &&
               Flyable(ToTile(center + new Vector2(radius, radius)));
    }

    public bool LineFlyable(Vector2 from, Vector2 to, float radius = 0.3f)
    {
        float length = Vector2.Distance(from, to);
        int steps = Mathf.Max(1, Mathf.CeilToInt(length / 0.4f));
        for (int i = 0; i <= steps; i++)
        {
            if (!AreaFlyable(Vector2.Lerp(from, to, i / (float)steps), radius)) return false;
        }
        return true;
    }

    public bool LineWalkable(Vector2 from, Vector2 to, float radius = 0.3f)
    {
        float length = Vector2.Distance(from, to);
        int steps = Mathf.Max(1, Mathf.CeilToInt(length / 0.4f));
        for (int i = 0; i <= steps; i++)
        {
            if (!AreaWalkable(Vector2.Lerp(from, to, i / (float)steps), radius)) return false;
        }
        return true;
    }

    public bool LineClearForShots(Vector2 from, Vector2 to)
    {
        float length = Vector2.Distance(from, to);
        int steps = Mathf.Max(1, Mathf.CeilToInt(length / 0.4f));
        for (int i = 1; i < steps; i++)
        {
            var t = ToTile(Vector2.Lerp(from, to, i / (float)steps));
            if (InBounds(t) && BlocksShots(t)) return false;
        }
        return true;
    }

    // Distance along `direction` until the first shot-blocking tile (or maxDistance)
    public float ShotDistance(Vector2 origin, Vector2 direction, float maxDistance)
    {
        for (float d = 0.25f; d < maxDistance; d += 0.25f)
        {
            var t = ToTile(origin + direction * d);
            if (InBounds(t) && BlocksShots(t)) return d;
        }
        return maxDistance;
    }

    // ---------------------------------------------------------------- flow field

    void ClearFlow()
    {
        for (int x = 0; x < Width; x++)
            for (int y = 0; y < Height; y++)
                distance[x, y] = int.MaxValue;
    }

    // Breadth-first distances (in tiles) from the knight's tile over walkable tiles
    public void UpdateFlow(Vector2 playerPosition)
    {
        ClearFlow();
        var start = ToTile(playerPosition);
        if (!Walkable(start)) start = NearestWalkable(start);
        if (!InBounds(start)) return;

        var queue = new Queue<Vector2Int>();
        distance[start.x, start.y] = 0;
        queue.Enqueue(start);
        while (queue.Count > 0)
        {
            var t = queue.Dequeue();
            foreach (var n in Neighbours(t))
            {
                if (!Walkable(n) || distance[n.x, n.y] != int.MaxValue) continue;
                distance[n.x, n.y] = distance[t.x, t.y] + 1;
                queue.Enqueue(n);
            }
        }
    }

    public int DistanceTo(Vector2Int t) => InBounds(t) ? distance[t.x, t.y] : int.MaxValue;

    // The neighbouring tile that gets closer to the knight, or `from` if there isn't one
    public Vector2Int NextStep(Vector2Int from)
    {
        if (!InBounds(from) || !Walkable(from)) from = NearestWalkable(from);
        Vector2Int best = from;
        int bestDistance = DistanceTo(from);
        foreach (var n in Neighbours(from))
        {
            int d = DistanceTo(n);
            if (d < bestDistance)
            {
                best = n;
                bestDistance = d;
            }
        }
        return best;
    }

    public Vector2Int NearestWalkable(Vector2Int from)
    {
        Vector2Int best = new Vector2Int(-1, -1);
        float bestDistance = float.MaxValue;
        for (int x = 0; x < Width; x++)
        {
            for (int y = 0; y < Height; y++)
            {
                var t = new Vector2Int(x, y);
                if (!Walkable(t)) continue;
                float d = (t - from).sqrMagnitude;
                if (d < bestDistance) { best = t; bestDistance = d; }
            }
        }
        return best;
    }

    public static IEnumerable<Vector2Int> Neighbours(Vector2Int t)
    {
        yield return t + Vector2Int.up;
        yield return t + Vector2Int.right;
        yield return t + Vector2Int.down;
        yield return t + Vector2Int.left;
    }
}
