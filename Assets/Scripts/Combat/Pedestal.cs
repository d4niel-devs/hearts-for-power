using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

// An item on a stone pedestal. Walking onto it buys the item, paying its price in heart containers.
// The price is shown as red hearts on the pedestal's pillar (half heart = ½ container).
// Taking something the knight already has levels it up. In a treasure room (shopRoom set) every
// purchase raises the price of the other pedestals there by half a heart.
public class Pedestal : MonoBehaviour
{
    public static readonly List<Pedestal> All = new List<Pedestal>();

    public AbilityId item;
    [HideInInspector] public Room shopRoom;

    public bool Taken { get; private set; }
    public int CostHalfHearts { get; private set; }
    public AbilityInfo Info => PlayerAbilities.Info(item);

    const float Scale = 1.5f;

    private Transform icon;
    private Vector3 iconBase;
    private readonly List<GameObject> costIcons = new List<GameObject>();
    private PlayerHealth playerHealth;
    private PlayerAbilities playerAbilities;
    private bool armed;            // only takeable once the knight has stepped away from it
    private float messageCooldown;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetStatics() => All.Clear();

    public static Pedestal Spawn(Vector2 position, AbilityId item, int costHalfHearts)
    {
        var baseSprite = Fx.SpawnSprite("Pedestal", "Effects/Pedestal", position, 0, Color.white, Scale);
        // Keeps the pedestal, its price hearts and the item drawn together, sorted by height with the characters
        var group = baseSprite.gameObject.AddComponent<SortingGroup>();
        group.sortingOrder = Fx.CharacterOrder;

        var pedestal = baseSprite.gameObject.AddComponent<Pedestal>();
        pedestal.item = item;

        var iconSprite = Fx.SpawnSprite("ItemIcon", PlayerAbilities.Info(item).icon, position + new Vector2(0f, 1.6f), 3, Color.white, 1.2f);
        iconSprite.transform.SetParent(pedestal.transform, true);
        pedestal.icon = iconSprite.transform;
        pedestal.iconBase = iconSprite.transform.localPosition;
        pedestal.SetCost(costHalfHearts);

        Fx.Ring(position + new Vector2(0f, 0.8f), 1.5f, new Color(1f, 0.9f, 0.5f), 0.5f);
        Fx.Puff(position + new Vector2(0f, 0.8f), new Color(1f, 0.95f, 0.7f), 14, 4f);
        return pedestal;
    }

    void OnEnable() => All.Add(this);
    void OnDisable() => All.Remove(this);

    // Shows the price as red hearts on the pillar face: whole hearts, then a half heart if needed
    public void SetCost(int halfHearts)
    {
        CostHalfHearts = Mathf.Max(1, halfHearts);
        foreach (var go in costIcons) Destroy(go);
        costIcons.Clear();
        if (Taken) return;

        var hearts = new List<string>();
        for (int i = 0; i < CostHalfHearts / 2; i++) hearts.Add("Room/CostHeart_full");
        if (CostHalfHearts % 2 == 1) hearts.Add("Room/CostHeart_half");

        // Up to two per row on the pillar face (local units, before the pedestal's scale)
        const float spacing = 0.5f;
        const float faceCenterY = 0.12f;
        int rows = (hearts.Count + 1) / 2;
        for (int i = 0; i < hearts.Count; i++)
        {
            int row = i / 2;
            int inRow = Mathf.Min(2, hearts.Count - row * 2);
            float x = (i % 2 - (inRow - 1) / 2f) * spacing;
            float y = faceCenterY + ((rows - 1) / 2f - row) * 0.47f;
            var sr = Fx.SpawnSprite("CostHeart", hearts[i], Vector2.zero, 1, Color.white);
            sr.transform.SetParent(transform, false);
            sr.transform.localPosition = new Vector3(x, y, 0f);
            costIcons.Add(sr.gameObject);
        }
    }

    void Start()
    {
        var player = FindAnyObjectByType<PlayerMovement>();
        if (player != null)
        {
            playerHealth = player.GetComponent<PlayerHealth>();
            playerAbilities = player.GetComponent<PlayerAbilities>();
        }
    }

    void Update()
    {
        if (icon != null) icon.localPosition = iconBase + new Vector3(0f, Mathf.Sin(Time.time * 3f) * 0.06f, 0f);
        if (messageCooldown > 0f) messageCooldown -= Time.deltaTime;
        if (Taken || playerHealth == null || playerHealth.IsDead) return;

        float distance = DistanceToPlayer;
        if (!armed)
        {
            armed = distance > 1.6f;
            return;
        }
        if (distance < 1.05f) TryTake();
    }

    public float DistanceToPlayer => playerHealth == null ? float.MaxValue
        : Vector2.Distance(playerHealth.transform.position, (Vector2)transform.position + new Vector2(0f, 0.5f));

    public bool CanAfford => playerHealth != null && playerHealth.CanSacrifice(CostHalfHearts);

    void TryTake()
    {
        if (!CanAfford)
        {
            if (messageCooldown <= 0f)
            {
                GameUI.ShowBanner("NOT ENOUGH HEARTS", "You must keep at least half a heart container", 2f);
                Audio.Play("UiBack");
                messageCooldown = 2.5f;
            }
            return;
        }

        playerHealth.Sacrifice(CostHalfHearts);
        playerAbilities.LevelUp(item);
        Audio.Play("Purchase");
        Taken = true;

        int level = playerAbilities.Level(item);
        string title = level == 1 ? Info.name.ToUpper() : $"{Info.name.ToUpper()} LV {level}";
        GameUI.ShowBanner(title, Info.levels[level - 1], 3f);

        Vector2 at = icon != null ? (Vector2)icon.position : (Vector2)transform.position;
        Fx.Puff(at, new Color(0.9f, 0.15f, 0.25f), 16, 5f, 1.3f);   // the hearts it cost
        Fx.Ring(at, 1.8f, new Color(1f, 0.3f, 0.35f), 0.4f);
        Fx.Shake(0.15f, 0.15f);
        if (icon != null) Destroy(icon.gameObject);
        SetCost(CostHalfHearts);   // clears the price hearts now that it's bought

        if (shopRoom != null && GameManager.Instance != null) GameManager.Instance.OnShopPurchase(shopRoom);
    }
}
