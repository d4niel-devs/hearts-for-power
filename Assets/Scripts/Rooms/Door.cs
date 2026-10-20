using UnityEngine;

// A door in a room's wall. Closed doors block the doorway; open ones let the knight walk through
// (the GameManager notices him stepping into the doorway and moves him to the next room).
// The art is drawn for the north wall and rotated for the other sides.
public class Door : MonoBehaviour
{
    public Side side;
    public bool IsOpen { get; private set; }
    // "Door" normally; "Door_Boss" / "Door_Treasure" when it leads to (or is in) a boss / treasure room
    public string spritePrefix = "Door";

    private SpriteRenderer spriteRenderer;
    private BoxCollider2D blocker;

    public static Door Create(Room room, Side side, Vector2 position, string spritePrefix = "Door")
    {
        var sr = Fx.SpawnSprite($"Door {side}", Theme.Path(spritePrefix + "_Open"), position, -18, Color.white);
        sr.transform.SetParent(room.transform, true);
        sr.transform.rotation = Quaternion.Euler(0f, 0f, -90f * (int)side);
        var door = sr.gameObject.AddComponent<Door>();
        door.side = side;
        door.spritePrefix = spritePrefix;
        door.spriteRenderer = sr;
        door.blocker = sr.gameObject.AddComponent<BoxCollider2D>();
        door.blocker.size = new Vector2(RoomGrid.TileSize, RoomGrid.TileSize);
        sr.gameObject.layer = LayerMask.NameToLayer("Obstacle");
        door.SetOpen(true, false);
        return door;
    }

    public void SetOpen(bool open, bool effects)
    {
        IsOpen = open;
        spriteRenderer.sprite = Theme.Sprite(spritePrefix + (open ? "_Open" : "_Closed"));
        blocker.enabled = !open;
        if (!effects) return;
        Fx.Puff(transform.position, new Color(0.45f, 0.4f, 0.38f), 10, 3f, 1.3f);
        Audio.Play(open ? "DoorOpen" : "DoorSlam", open ? 0.6f : 0.8f);
    }
}
