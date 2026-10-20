using System.Collections.Generic;
using UnityEngine;

public enum RoomType { Start, Fight, Treasure, Boss }
public enum Side { North, East, South, West }

// One room on the floor map and everything remembered about it
public class RoomInfo
{
    public Vector2Int cell;
    public RoomType type;
    public int depth;                     // rooms away from the start
    public readonly bool[] doors = new bool[4];
    public TileKind[,] tiles;
    public bool visited, seen, cleared;
    public Room instance;                 // built the first time the knight goes in
}

// An Isaac-style floor: rooms on a grid grown out from the start room. The boss room is the
// dead end furthest from the start; the treasure room is another dead end.
public class FloorMap
{
    public readonly Dictionary<Vector2Int, RoomInfo> Rooms = new Dictionary<Vector2Int, RoomInfo>();
    public RoomInfo Start { get; private set; }
    public RoomInfo BossRoom { get; private set; }
    public RoomInfo TreasureRoom { get; private set; }

    public static readonly Vector2Int[] SideOffsets = { Vector2Int.up, Vector2Int.right, Vector2Int.down, Vector2Int.left };
    public static Side Opposite(Side side) => (Side)(((int)side + 2) % 4);

    public RoomInfo Neighbour(RoomInfo room, Side side)
    {
        Rooms.TryGetValue(room.cell + SideOffsets[(int)side], out RoomInfo neighbour);
        return neighbour;
    }

    public static FloorMap Generate(int floor, System.Random random)
    {
        int target = Mathf.Min(13, random.Next(7, 10) + (floor - 1));
        for (int attempt = 0; attempt < 200; attempt++)
        {
            var map = new FloorMap();
            if (map.TryGenerate(target, random)) return map;
        }
        Debug.LogWarning("FloorMap: fell back to a minimal floor");
        var fallback = new FloorMap();
        fallback.TryGenerate(4, random);
        return fallback;
    }

    bool TryGenerate(int target, System.Random random)
    {
        Rooms.Clear();
        Add(Vector2Int.zero);
        int guard = 0;
        while (Rooms.Count < target && guard++ < 2000)
        {
            var cells = new List<Vector2Int>(Rooms.Keys);
            var from = cells[random.Next(cells.Count)];
            var cell = from + SideOffsets[random.Next(4)];
            if (Rooms.ContainsKey(cell) || NeighbourCount(cell) > 1) continue;   // keeps branches, no blobs
            Add(cell);
        }
        if (Rooms.Count < target) return false;

        // Depth (rooms from the start) by breadth-first search
        Start = Rooms[Vector2Int.zero];
        var queue = new Queue<RoomInfo>();
        foreach (var r in Rooms.Values) r.depth = -1;
        Start.depth = 0;
        queue.Enqueue(Start);
        while (queue.Count > 0)
        {
            var r = queue.Dequeue();
            foreach (var offset in SideOffsets)
            {
                if (Rooms.TryGetValue(r.cell + offset, out var n) && n.depth < 0)
                {
                    n.depth = r.depth + 1;
                    queue.Enqueue(n);
                }
            }
        }

        var deadEnds = new List<RoomInfo>();
        foreach (var r in Rooms.Values)
            if (r != Start && NeighbourCount(r.cell) == 1) deadEnds.Add(r);
        if (deadEnds.Count < 2) return false;

        deadEnds.Sort((a, b) => b.depth.CompareTo(a.depth));
        BossRoom = deadEnds[0];
        if (BossRoom.depth < 2) return false;
        TreasureRoom = deadEnds[1 + random.Next(deadEnds.Count - 1)];

        foreach (var r in Rooms.Values)
        {
            for (int side = 0; side < 4; side++) r.doors[side] = Rooms.ContainsKey(r.cell + SideOffsets[side]);
            r.type = r == Start ? RoomType.Start : r == BossRoom ? RoomType.Boss : r == TreasureRoom ? RoomType.Treasure : RoomType.Fight;
            r.tiles = PickLayout(r, random);
            r.cleared = r.type == RoomType.Start || r.type == RoomType.Treasure;
        }
        return true;
    }

    static TileKind[,] PickLayout(RoomInfo room, System.Random random)
    {
        switch (room.type)
        {
            case RoomType.Start: return RoomLayouts.Build(RoomLayouts.Empty, room.doors, random);
            case RoomType.Treasure: return RoomLayouts.Build(RoomLayouts.Treasure, room.doors, random);
            case RoomType.Boss: return RoomLayouts.Build(RoomLayouts.Boss, room.doors, random);
        }
        for (int i = 0; i < 20; i++)
        {
            var layout = RoomLayouts.Fight[random.Next(RoomLayouts.Fight.Length)];
            var tiles = RoomLayouts.Build(layout, room.doors, random);
            if (RoomLayouts.DoorsConnected(tiles, room.doors)) return tiles;
        }
        return RoomLayouts.Build(RoomLayouts.Empty, room.doors, random);
    }

    void Add(Vector2Int cell)
    {
        Rooms[cell] = new RoomInfo { cell = cell };
    }

    int NeighbourCount(Vector2Int cell)
    {
        int count = 0;
        foreach (var offset in SideOffsets)
            if (Rooms.ContainsKey(cell + offset)) count++;
        return count;
    }
}
