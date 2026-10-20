using UnityEngine;

// A heart lying on the floor. Normal hearts heal one heart, and (like Isaac) are only picked up when
// the knight is missing health; at full health a "FULL" note pops up instead. A heart container
// (dropped by bosses) is always picked up: it adds a container and fully heals.
public class HeartPickup : MonoBehaviour
{
    public int halfHearts = 2;
    public bool container;

    private PlayerHealth playerHealth;
    private Vector3 basePosition;
    private float age;
    private float fullNoteCooldown;

    public static HeartPickup Spawn(Vector2 position, int halfHearts, bool container)
    {
        var sr = Fx.SpawnSprite(container ? "HeartContainer" : "Heart", "UI/Heart_full", RoomBounds.Clamp(position, 0.5f),
                                Fx.CharacterOrder, Color.white, container ? 1.8f : 1.2f);
        // Belongs to the room it fell in, so it's still there if the knight leaves and comes back
        if (Room.Current != null) sr.transform.SetParent(Room.Current.transform, true);
        var pickup = sr.gameObject.AddComponent<HeartPickup>();
        pickup.halfHearts = halfHearts;
        pickup.container = container;
        Fx.Puff(position, new Color(1f, 0.4f, 0.5f), container ? 16 : 6, 3f);
        return pickup;
    }

    void Start()
    {
        basePosition = transform.position;
        var player = FindAnyObjectByType<PlayerMovement>();
        if (player != null) playerHealth = player.GetComponent<PlayerHealth>();
    }

    void Update()
    {
        age += Time.deltaTime;
        if (fullNoteCooldown > 0f) fullNoteCooldown -= Time.deltaTime;
        if (playerHealth == null || playerHealth.IsDead)
        {
            Bob();
            return;
        }

        bool wanted = container || playerHealth.Health < playerHealth.MaxHealth;
        Vector2 toPlayer = playerHealth.transform.position - transform.position;
        float distance = toPlayer.magnitude;

        if (distance < 0.7f)
        {
            if (wanted)
            {
                Collect();
                return;
            }
            if (fullNoteCooldown <= 0f)
            {
                GameUI.Popup("FULL", transform.position + Vector3.up * 0.6f);
                Audio.Play("Full", 0.5f);
                fullNoteCooldown = 1.5f;
            }
        }
        else if (wanted && distance < 1.8f)
        {
            // Drawn toward the knight when he's close
            basePosition += (Vector3)(toPlayer.normalized * 6f * Time.deltaTime);
        }
        Bob();
    }

    void Bob()
    {
        transform.position = basePosition + new Vector3(0f, Mathf.Sin(age * 4f) * 0.07f, 0f);
    }

    void Collect()
    {
        if (container)
        {
            playerHealth.AddContainers(halfHearts, true);
            GameUI.ShowBanner("HEART CONTAINER", "+1 heart, fully healed", 2.5f);
        }
        else
        {
            playerHealth.Heal(halfHearts);
        }
        Fx.Puff(transform.position, new Color(1f, 0.35f, 0.45f), 14, 4f, 1.3f);
        Fx.Ring(transform.position, 1f, new Color(1f, 0.4f, 0.5f), 0.3f);
        Destroy(gameObject);
    }
}
