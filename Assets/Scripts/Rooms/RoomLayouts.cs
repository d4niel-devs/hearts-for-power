using System.Collections.Generic;
using UnityEngine;

// Hand-made obstacle layouts for the 13x7 room floor. Row 0 of each layout is the TOP of the room.
//   .  floor     R  rock (bombs smash it)     P  pillar (indestructible)
//   O  pit       ^  spike trap                p  breakable pot
// Layouts are randomly mirrored, and the tiles in front of every door are always cleared.
public static class RoomLayouts
{
    public static readonly string[] Empty =
    {
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    };

    public static readonly string[] Treasure =
    {
        ".............",
        ".p.........p.",
        ".............",
        ".............",
        ".............",
        ".p.........p.",
        ".............",
    };

    public static readonly string[] Boss =
    {
        ".............",
        ".P.........P.",
        ".............",
        ".............",
        ".............",
        ".P.........P.",
        ".............",
    };

    public static readonly string[][] Fight =
    {
        new[] {
            ".............",
            "..R.......R..",
            ".............",
            ".....p.p.....",
            ".............",
            "..R.......R..",
            ".............",
        },
        new[] {
            ".............",
            "...P.....P...",
            ".............",
            ".............",
            ".............",
            "...P.....P...",
            ".............",
        },
        new[] {
            ".............",
            ".............",
            "....OOOOO....",
            "....OOOOO....",
            "....OOOOO....",
            ".............",
            ".............",
        },
        new[] {
            ".............",
            "..^..^..^..^.",
            ".............",
            ".^..^..^..^..",
            ".............",
            "..^..^..^..^.",
            ".............",
        },
        new[] {
            ".............",
            ".RRR.....RRR.",
            ".R.........R.",
            ".....ppp.....",
            ".R.........R.",
            ".RRR.....RRR.",
            ".............",
        },
        new[] {
            ".............",
            ".OOOO...OOOO.",
            ".............",
            ".............",
            ".............",
            ".OOOO...OOOO.",
            ".............",
        },
        new[] {
            "pp.........pp",
            "p...........p",
            ".....R.R.....",
            ".............",
            ".....R.R.....",
            "p...........p",
            "pp.........pp",
        },
        new[] {
            ".............",
            ".............",
            "......^......",
            ".....^^^.....",
            "......^......",
            ".............",
            ".............",
        },
        new[] {
            ".............",
            "..OO.....OO..",
            "..OO.....OO..",
            ".............",
            "..OO.....OO..",
            "..OO.....OO..",
            ".............",
        },
        new[] {
            ".............",
            "....R...R....",
            "..R.......R..",
            ".............",
            "..R.......R..",
            "....R...R....",
            ".............",
        },
        new[] {
            ".............",
            ".P..P...P..P.",
            ".............",
            ".............",
            ".............",
            ".P..P...P..P.",
            ".............",
        },
        new[] {
            ".............",
            ".^^^.....^^^.",
            ".....R.R.....",
            ".............",
            ".....R.R.....",
            ".^^^.....^^^.",
            ".............",
        },
        new[] {
            ".............",
            ".OOOOO.OOOOO.",
            ".OOOOO.OOOOO.",
            ".............",
            ".OOOOO.OOOOO.",
            ".OOOOO.OOOOO.",
            ".............",
        },
        new[] {
            ".p.........p.",
            ".............",
            "...R..p..R...",
            ".............",
            "...R..p..R...",
            ".............",
            ".p.........p.",
        },
    };

    // The interior tile in front of each door (Side order: North, East, South, West)
    public static readonly Vector2Int[] DoorTiles =
    {
        new Vector2Int(6, 6), new Vector2Int(12, 3), new Vector2Int(6, 0), new Vector2Int(0, 3),
    };

    public static TileKind KindFor(char c)
    {
        switch (c)
        {
            case 'R': return TileKind.Rock;
            case 'P': return TileKind.Pillar;
            case 'O': return TileKind.Pit;
            case '^': return TileKind.Spikes;
            case 'p': return TileKind.Pot;
            default: return TileKind.Floor;
        }
    }

    // Converts a layout to a tile array [x, y] (y = 0 at the bottom), mirrored at random,
    // with the tiles in front of each door cleared.
    public static TileKind[,] Build(string[] layout, bool[] doors, System.Random random)
    {
        bool flipX = random.Next(2) == 0;
        bool flipY = random.Next(2) == 0;
        var result = new TileKind[RoomGrid.Width, RoomGrid.Height];
        for (int row = 0; row < RoomGrid.Height; row++)
        {
            for (int col = 0; col < RoomGrid.Width; col++)
            {
                int x = flipX ? RoomGrid.Width - 1 - col : col;
                int y = RoomGrid.Height - 1 - row;
                if (flipY) y = RoomGrid.Height - 1 - y;
                result[x, y] = KindFor(layout[row][col]);
            }
        }

        for (int side = 0; side < 4; side++)
        {
            if (!doors[side]) continue;
            var t = DoorTiles[side];
            var inward = new[] { Vector2Int.down, Vector2Int.left, Vector2Int.up, Vector2Int.right }[side];
            result[t.x, t.y] = TileKind.Floor;
            var next = t + inward;
            result[next.x, next.y] = TileKind.Floor;
        }
        return result;
    }

    // True if every door can reach every other door (over walkable tiles)
    public static bool DoorsConnected(TileKind[,] tiles, bool[] doors)
    {
        Vector2Int? start = null;
        for (int side = 0; side < 4; side++) if (doors[side]) { start = DoorTiles[side]; break; }
        if (start == null) return true;

        var seen = new bool[RoomGrid.Width, RoomGrid.Height];
        var queue = new Queue<Vector2Int>();
        queue.Enqueue(start.Value);
        seen[start.Value.x, start.Value.y] = true;
        while (queue.Count > 0)
        {
            var t = queue.Dequeue();
            foreach (var n in RoomGrid.Neighbours(t))
            {
                if (!RoomGrid.InBounds(n) || seen[n.x, n.y]) continue;
                var k = tiles[n.x, n.y];
                if (k != TileKind.Floor && k != TileKind.Spikes) continue;
                seen[n.x, n.y] = true;
                queue.Enqueue(n);
            }
        }
        for (int side = 0; side < 4; side++)
        {
            if (doors[side] && !seen[DoorTiles[side].x, DoorTiles[side].y]) return false;
        }
        return true;
    }
}
