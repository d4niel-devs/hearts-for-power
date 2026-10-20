using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

// One room, built at runtime from its RoomInfo: stone floor and walls (Tilemaps), wall colliders,
// doors, torches and obstacles. Rooms stay in the scene (switched off) after the knight leaves,
// so anything left on the floor is still there when he comes back.
// Size: 13x7 floor tiles inside a ring of walls = 15x9 tiles of 2 units = 30x18 world units.
public class Room : MonoBehaviour
{
    public const float WidthUnits = (RoomGrid.Width + 2) * RoomGrid.TileSize;    // 30
    public const float HeightUnits = (RoomGrid.Height + 2) * RoomGrid.TileSize;  // 18

    public static Room Current { get; set; }

    public RoomInfo Info { get; private set; }
    public RoomGrid Grid { get; private set; }
    public Vector2 Center => transform.position;
    public Rect Interior => new Rect(Center - new Vector2(RoomGrid.Width, RoomGrid.Height) * RoomGrid.TileSize / 2f,
                                     new Vector2(RoomGrid.Width, RoomGrid.Height) * RoomGrid.TileSize);
    public Rect Outer => new Rect(Center - new Vector2(WidthUnits, HeightUnits) / 2f, new Vector2(WidthUnits, HeightUnits));

    // Treasure room shop: how many items were bought here (each one makes the rest cost ½ heart more)
    public int TreasurePurchases { get; set; }
    public bool ShopStocked { get; set; }

    private readonly Door[] doors = new Door[4];
    private readonly Dictionary<Vector2Int, Obstacle> obstacles = new Dictionary<Vector2Int, Obstacle>();
    private static readonly Dictionary<string, Tile> tileCache = new Dictionary<string, Tile>();

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetStatics()
    {
        Current = null;
        tileCache.Clear();
    }

    public static Vector2 WorldCenterFor(Vector2Int cell) => new Vector2(cell.x * WidthUnits, cell.y * HeightUnits);

    // ---------------------------------------------------------------- building

    public static Room Build(RoomInfo info, int seed)
    {
        var go = new GameObject($"Room {info.cell.x},{info.cell.y} ({info.type})");
        go.transform.position = WorldCenterFor(info.cell);
        var room = go.AddComponent<Room>();
        room.Info = info;
        room.Grid = new RoomGrid(go.transform.position);
        info.instance = room;
        room.BuildTiles(new System.Random(seed));
        room.BuildDoors();
        room.BuildObstacles(new System.Random(seed + 7));
        return room;
    }

    static Tile TileFor(string sprite)
    {
        string path = Theme.Path(sprite);          // the floor's theme decides the art
        if (tileCache.TryGetValue(path, out Tile tile) && tile != null) return tile;
        tile = ScriptableObject.CreateInstance<Tile>();
        tile.sprite = Fx.Sprite(path);
        tile.colliderType = Tile.ColliderType.None;
        tile.flags = TileFlags.None;   // lets walls be rotated per cell
        tileCache[path] = tile;
        return tile;
    }

    Tilemap MakeTilemap(Transform gridTransform, string name, int order)
    {
        var go = new GameObject(name);
        go.transform.SetParent(gridTransform, false);
        var map = go.AddComponent<Tilemap>();
        var renderer = go.AddComponent<TilemapRenderer>();
        renderer.sortingOrder = order;
        return map;
    }

    void BuildTiles(System.Random random)
    {
        var gridObject = new GameObject("Tiles");
        gridObject.transform.SetParent(transform, false);
        gridObject.transform.localPosition = new Vector3(-WidthUnits / 2f, -HeightUnits / 2f, 0f);
        gridObject.AddComponent<Grid>().cellSize = new Vector3(RoomGrid.TileSize, RoomGrid.TileSize, 0f);

        var floor = MakeTilemap(gridObject.transform, "Floor", -20);
        var walls = MakeTilemap(gridObject.transform, "Walls", -19);

        // Mostly plain slabs, sometimes cracked, mossy or wet
        int[] floorWeights = { 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 };
        for (int x = 1; x <= RoomGrid.Width; x++)
            for (int y = 1; y <= RoomGrid.Height; y++)
                floor.SetTile(new Vector3Int(x, y, 0), TileFor($"Floor_{floorWeights[random.Next(floorWeights.Length)]}"));

        int maxX = RoomGrid.Width + 1, maxY = RoomGrid.Height + 1;
        var wallColliders = new GameObject("WallColliders");
        wallColliders.transform.SetParent(transform, false);
        wallColliders.layer = LayerMask.NameToLayer("Obstacle");
        for (int x = 0; x <= maxX; x++)
        {
            for (int y = 0; y <= maxY; y++)
            {
                bool edge = x == 0 || y == 0 || x == maxX || y == maxY;
                if (!edge || IsDoorCell(x, y)) continue;
                // Every wall uses the brick face, turned so its shaded base faces the floor
                bool corner = (x == 0 || x == maxX) && (y == 0 || y == maxY);
                string sprite = corner ? "Wall_Corner_Inner" : $"Wall_N_{random.Next(3)}";
                float angle;
                if (corner)
                {
                    // The corner tile's shading sits where the two walls' bases meet
                    if (x == 0) angle = y == maxY ? 0f : 90f;      // top-left / bottom-left
                    else angle = y == maxY ? -90f : 180f;          // top-right / bottom-right
                }
                else if (y == maxY) angle = 0f;       // north
                else if (y == 0) angle = 180f;        // south
                else if (x == 0) angle = 90f;         // west: base faces right
                else angle = -90f;                    // east: base faces left
                var cell = new Vector3Int(x, y, 0);
                walls.SetTile(cell, TileFor(sprite));
                walls.SetTransformMatrix(cell, Matrix4x4.Rotate(Quaternion.Euler(0f, 0f, angle)));

                var box = wallColliders.AddComponent<BoxCollider2D>();
                box.offset = CellCenterLocal(x, y);
                box.size = new Vector2(RoomGrid.TileSize, RoomGrid.TileSize);
            }
        }

        // Soft shadow pooled on the floor in each corner (sprite drawn for the top-left, rotated for the rest)
        var corners = new[]
        {
            (new Vector2Int(1, maxY - 1), 0f), (new Vector2Int(maxX - 1, maxY - 1), -90f),
            (new Vector2Int(maxX - 1, 1), 180f), (new Vector2Int(1, 1), 90f),
        };
        foreach (var (cell, angle) in corners)
        {
            var shadow = Fx.SpawnSprite("CornerShadow", Theme.Path("Floor_CornerShadow"), (Vector2)transform.position + CellCenterLocal(cell.x, cell.y),
                                        -19, Color.white);
            shadow.transform.SetParent(transform, true);
            shadow.transform.rotation = Quaternion.Euler(0f, 0f, angle);
        }

        // A couple of torches on the back wall
        var torchSpots = new List<int> { 2, 4, 10, 12 };
        for (int i = 0; i < 2; i++)
        {
            int x = torchSpots[random.Next(torchSpots.Count)];
            torchSpots.Remove(x);
            var torch = Fx.SpawnSprite("Torch", Theme.Path("Torch_0"), (Vector2)transform.position + CellCenterLocal(x, maxY) + new Vector2(0f, 0.2f),
                                       -18, Color.white);
            torch.transform.SetParent(transform, true);
            torch.gameObject.AddComponent<TorchFlicker>();
        }
    }

    bool IsDoorCell(int x, int y)
    {
        for (int side = 0; side < 4; side++)
        {
            if (!Info.doors[side]) continue;
            var c = DoorCell((Side)side);
            if (c.x == x && c.y == y) return true;
        }
        return false;
    }

    // Door positions in the 15x9 cell grid (walls included)
    static Vector2Int DoorCell(Side side)
    {
        switch (side)
        {
            case Side.North: return new Vector2Int(7, RoomGrid.Height + 1);
            case Side.East: return new Vector2Int(RoomGrid.Width + 1, 4);
            case Side.South: return new Vector2Int(7, 0);
            default: return new Vector2Int(0, 4);
        }
    }

    static Vector2 CellCenterLocal(int x, int y) =>
        new Vector2((x + 0.5f) * RoomGrid.TileSize - WidthUnits / 2f, (y + 0.5f) * RoomGrid.TileSize - HeightUnits / 2f);

    void BuildDoors()
    {
        for (int side = 0; side < 4; side++)
        {
            if (!Info.doors[side]) continue;
            var cell = DoorCell((Side)side);
            doors[side] = Door.Create(this, (Side)side, (Vector2)transform.position + CellCenterLocal(cell.x, cell.y), DoorStyle((Side)side));
        }
    }

    // Boss and treasure rooms are marked by their doors: the doors leading into them, and all the
    // doors inside them, get the special look
    string DoorStyle(Side side)
    {
        var map = GameManager.Instance != null ? GameManager.Instance.Map : null;
        var other = map != null ? map.Neighbour(Info, side) : null;
        if (Info.type == RoomType.Boss || (other != null && other.type == RoomType.Boss)) return "Door_Boss";
        if (Info.type == RoomType.Treasure || (other != null && other.type == RoomType.Treasure)) return "Door_Treasure";
        return "Door";
    }

    void BuildObstacles(System.Random random)
    {
        for (int x = 0; x < RoomGrid.Width; x++)
        {
            for (int y = 0; y < RoomGrid.Height; y++)
            {
                var t = new Vector2Int(x, y);
                var kind = Info.tiles[x, y];
                Grid.Set(t, kind);
                if (kind == TileKind.Floor) continue;
                obstacles[t] = Obstacle.Create(this, t, kind, PitMask(t), random);
            }
        }
    }

    // Which sides of a pit tile border floor (so only those get a rim)
    int PitMask(Vector2Int t)
    {
        int mask = 0;
        if (!IsPit(t + Vector2Int.up)) mask |= 1;
        if (!IsPit(t + Vector2Int.right)) mask |= 2;
        if (!IsPit(t + Vector2Int.down)) mask |= 4;
        if (!IsPit(t + Vector2Int.left)) mask |= 8;
        return mask;
    }

    bool IsPit(Vector2Int t) => RoomGrid.InBounds(t) && Info.tiles[t.x, t.y] == TileKind.Pit;

    // ---------------------------------------------------------------- doors

    public bool HasDoor(Side side) => doors[(int)side] != null;
    public Door DoorOn(Side side) => doors[(int)side];

    public void SetDoorsOpen(bool open, bool effects)
    {
        foreach (var door in doors)
            if (door != null) door.SetOpen(open, effects);
        if (effects) Fx.Shake(open ? 0.08f : 0.2f, open ? 0.1f : 0.2f);
    }

    // Where the knight stands after walking in through the door on `side`
    public Vector2 EntryPoint(Side side)
    {
        var t = RoomLayouts.DoorTiles[(int)side];
        var p = Grid.TileCenter(t);
        // pull slightly toward the doorway so he appears to have just stepped in
        var outward = (Vector2)FloorMap.SideOffsets[(int)side];
        return p + outward * 0.4f;
    }

    // ---------------------------------------------------------------- obstacles

    public Obstacle ObstacleAt(Vector2Int t)
    {
        obstacles.TryGetValue(t, out Obstacle o);
        return o;
    }

    public void RemoveObstacle(Vector2Int t)
    {
        obstacles.Remove(t);
    }

    // A shot hit whatever is at `world`: pots break
    public void ShotHit(Vector2 world)
    {
        var o = ObstacleAt(Grid.ToTile(world));
        if (o != null && o.kind == TileKind.Pot) o.Break();
    }

    // Explosions break pots and (if smashRocks) rocks within the radius
    public void DamageArea(Vector2 center, float radius, bool smashRocks)
    {
        var hit = new List<Obstacle>();
        foreach (var pair in obstacles)
        {
            if (Vector2.Distance(Grid.TileCenter(pair.Key), center) > radius + 0.8f) continue;
            if (pair.Value.kind == TileKind.Pot || (smashRocks && pair.Value.kind == TileKind.Rock)) hit.Add(pair.Value);
        }
        foreach (var o in hit) o.Break();
    }

    // Floor tiles where monsters can appear: walkable, reachable, not on spikes, away from the knight
    public List<Vector2> SpawnPoints(Vector2 avoid, float minDistance)
    {
        var points = new List<Vector2>();
        for (int x = 0; x < RoomGrid.Width; x++)
        {
            for (int y = 0; y < RoomGrid.Height; y++)
            {
                var t = new Vector2Int(x, y);
                if (Grid.Get(t) != TileKind.Floor || Grid.DistanceTo(t) == int.MaxValue) continue;
                var p = Grid.TileCenter(t);
                if (Vector2.Distance(p, avoid) >= minDistance) points.Add(p);
            }
        }
        return points;
    }
}

// Swaps between the two torch flame frames
public class TorchFlicker : MonoBehaviour
{
    private SpriteRenderer sr;
    private Sprite a, b;
    private float timer;

    void Start()
    {
        sr = GetComponent<SpriteRenderer>();
        a = Theme.Sprite("Torch_0");
        b = Theme.Sprite("Torch_1");
        timer = Random.value * 0.2f;
    }

    void Update()
    {
        timer -= Time.deltaTime;
        if (timer > 0f) return;
        timer = Random.Range(0.1f, 0.22f);
        sr.sprite = sr.sprite == a ? b : a;
    }
}
