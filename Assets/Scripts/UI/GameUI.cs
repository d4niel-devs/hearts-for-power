using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

// The on-screen HUD, built in code so it needs no scene setup:
//   hearts (top left, new containers bounce in and refill one by one), floor / best and the minimap
//   (top right), boss health bar (top), ability bar with keys and cooldowns (bottom left),
//   announcement banners, the pedestal item panel, "FULL" pop-ups and the stairs fade.
// The title, pause, settings and death screens are in GameUI.Menus.cs.
// Layout is in a 640x360 virtual screen that scales with the window, so it stays pixel-chunky.
public partial class GameUI : MonoBehaviour
{
    static GameUI instance;

    const float HeartScale = 2f;
    const float MapCellW = 14f, MapCellH = 9f, MapGap = 2f;

    private Font font;          // Pixelify Sans: all regular text
    private Font titleFont;     // Jacquard 24 (pixel blackletter): big headings
    private RectTransform root;
    private RectTransform hud;            // everything that's hidden on the title screen
    private CanvasGroup hudGroup;
    private float hurtFlash;              // hearts flash red and shake when the knight is hit
    private Vector2 heartsRowHome;
    private CanvasGroup deathTint;

    // hearts
    private RectTransform heartsRow;
    private readonly List<Image> heartImages = new List<Image>();
    private readonly List<float> heartBounce = new List<float>();
    private Sprite heartFull, heartHalf, heartEmpty, halfContainerFull, halfContainerEmpty;
    private int shownHealth = -1;
    private int shownContainers;
    private float refillTimer;

    private Text floorText, bestText;
    private GameObject bossBar;
    private Image bossFill;
    private Text bossName;

    // minimap
    private RectTransform minimap;
    private readonly List<GameObject> mapCells = new List<GameObject>();
    private string mapState = "";

    private RectTransform abilityBar;
    private readonly List<(AbilityId id, Image cooldown, Text level)> slots = new List<(AbilityId, Image, Text)>();
    private bool slotsDirty = true;

    private CanvasGroup bannerGroup;
    private Text bannerTitle, bannerSubtitle;
    private float bannerTime, bannerDuration;

    private GameObject pedestalPanel;
    private Text pedestalTitle, pedestalBody, pedestalCost;

    private CanvasGroup fadeGroup;
    private float fadeTarget, fadeSpeed = 1f;

    private class Floating { public RectTransform rt; public Vector2 velocity; public float life, age; public Vector3 world; public bool worldSpace; public Graphic graphic; }
    private readonly List<Floating> floating = new List<Floating>();

    private PlayerHealth playerHealth;
    private PlayerAbilities playerAbilities;

    // ---------------------------------------------------------------- public API

    public static void ShowBanner(string title, string subtitle, float seconds)
    {
        if (instance == null) return;
        instance.bannerTitle.text = TitleCase(title);
        instance.bannerSubtitle.text = subtitle ?? "";
        instance.bannerDuration = seconds;
        instance.bannerTime = 0f;
        instance.bannerGroup.alpha = 1f;
    }

    // Small text that rises from a point in the world and fades (e.g. "FULL" over a heart)
    public static void Popup(string text, Vector3 worldPosition)
    {
        if (instance == null) return;
        var label = instance.MakeLabel("Popup", instance.root, text, 10, TextAnchor.MiddleCenter, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(80f, 14f));
        label.rectTransform.pivot = new Vector2(0.5f, 0.5f);
        instance.floating.Add(new Floating { rt = label.rectTransform, life = 0.9f, world = worldPosition, worldSpace = true, graphic = label });
    }

    // Fades the screen to black (alpha 1) or back (alpha 0) over `seconds`
    public static void Fade(float alpha, float seconds)
    {
        if (instance == null) return;
        instance.fadeTarget = alpha;
        instance.fadeSpeed = 1f / Mathf.Max(0.01f, seconds);
    }

    // ---------------------------------------------------------------- building

    void Awake()
    {
        instance = this;
        font = Resources.Load<Font>("Fonts/PixelifySans");
        titleFont = Resources.Load<Font>("Fonts/Jacquard24-Regular");
        if (font == null) font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        if (titleFont == null) titleFont = font;
        heartFull = Fx.Sprite("UI/Heart_full");
        heartHalf = Fx.Sprite("UI/Heart_half");
        heartEmpty = Fx.Sprite("UI/Heart_empty");
        halfContainerFull = Fx.Sprite("UI/Heart_halfcontainer_full");
        halfContainerEmpty = Fx.Sprite("UI/Heart_halfcontainer_empty");
        Build();
    }

    void OnDestroy()
    {
        if (instance == this) instance = null;
        if (playerAbilities != null) playerAbilities.Changed -= MarkSlotsDirty;
    }

    void Start()
    {
        var player = FindAnyObjectByType<PlayerMovement>();
        if (player == null) return;
        playerHealth = player.GetComponent<PlayerHealth>();
        playerAbilities = player.GetComponent<PlayerAbilities>();
        playerAbilities.Changed += MarkSlotsDirty;
        playerHealth.Hurt += () => hurtFlash = 0.35f;
    }

    void MarkSlotsDirty() => slotsDirty = true;

    void Build()
    {
        var canvasObject = new GameObject("HUD");
        canvasObject.transform.SetParent(transform, false);
        var canvas = canvasObject.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;
        var scaler = canvasObject.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(640f, 360f);
        scaler.matchWidthOrHeight = 1f;
        root = (RectTransform)canvasObject.transform;

        // Red tint that creeps in while the knight dies (under everything else)
        var tint = MakeImage("DeathTint", root, Fx.Sprite("UI/White"), new Color(0.6f, 0f, 0.05f, 0.45f), Vector2.zero, Vector2.zero, Vector2.zero);
        Stretch(tint.rectTransform);
        deathTint = tint.gameObject.AddComponent<CanvasGroup>();
        deathTint.alpha = 0f;

        hud = MakeRect("HUD", root, Vector2.zero, Vector2.zero, Vector2.zero);
        Stretch(hud);
        hudGroup = hud.gameObject.AddComponent<CanvasGroup>();

        // Hearts
        heartsRow = MakeRect("Hearts", hud, new Vector2(0f, 1f), new Vector2(10f, -8f), new Vector2(300f, 24f));
        heartsRowHome = heartsRow.anchoredPosition;

        // Floor + best (right-aligned labels grow leftwards from the screen's right edge)
        floorText = MakeLabel("Floor", hud, "", 16, TextAnchor.UpperRight, new Vector2(1f, 1f), new Vector2(-10f, -6f), new Vector2(200f, 20f));
        bestText = MakeLabel("Best", hud, "", 9, TextAnchor.UpperRight, new Vector2(1f, 1f), new Vector2(-10f, -24f), new Vector2(200f, 14f));
        bestText.color = new Color(1f, 1f, 1f, 0.6f);
        floorText.rectTransform.pivot = new Vector2(1f, 1f);
        bestText.rectTransform.pivot = new Vector2(1f, 1f);

        // Minimap (cells are placed relative to its top-right corner)
        minimap = MakeRect("Minimap", hud, new Vector2(1f, 1f), new Vector2(-10f, -40f), new Vector2(120f, 80f));
        minimap.pivot = new Vector2(1f, 1f);

        // Boss bar
        var bar = MakeRect("BossBar", hud, new Vector2(0.5f, 1f), new Vector2(-130f, -22f), new Vector2(260f, 26f));
        bossBar = bar.gameObject;
        bossName = MakeLabel("BossName", bar, "", 10, TextAnchor.UpperCenter, new Vector2(0.5f, 1f), new Vector2(-130f, 0f), new Vector2(260f, 14f));
        var back = MakeImage("Back", bar, Fx.Sprite("UI/White"), new Color(0.05f, 0.03f, 0.05f, 0.85f), new Vector2(0f, 1f), new Vector2(0f, -14f), new Vector2(260f, 10f));
        bossFill = MakeImage("Fill", back.rectTransform, Fx.Sprite("UI/White"), new Color(0.85f, 0.15f, 0.2f), new Vector2(0f, 1f), new Vector2(1f, -1f), new Vector2(258f, 8f));
        bossFill.type = UnityEngine.UI.Image.Type.Filled;
        bossFill.fillMethod = UnityEngine.UI.Image.FillMethod.Horizontal;
        bossBar.SetActive(false);

        // Ability bar
        abilityBar = MakeRect("Abilities", hud, new Vector2(0f, 0f), new Vector2(10f, 10f), new Vector2(400f, 34f));
        abilityBar.pivot = Vector2.zero;

        // Banner
        var banner = MakeRect("Banner", root, new Vector2(0.5f, 0.5f), new Vector2(-250f, 95f), new Vector2(500f, 60f));
        bannerGroup = banner.gameObject.AddComponent<CanvasGroup>();
        bannerGroup.alpha = 0f;
        bannerTitle = MakeLabel("Title", banner, "", 34, TextAnchor.MiddleCenter, new Vector2(0f, 1f), new Vector2(0f, 4f), new Vector2(500f, 38f));
        UseTitleFont(bannerTitle);
        bannerSubtitle = MakeLabel("Subtitle", banner, "", 11, TextAnchor.MiddleCenter, new Vector2(0f, 1f), new Vector2(0f, -34f), new Vector2(500f, 20f));

        // Pedestal item panel
        var panel = MakeImage("PedestalPanel", hud, Fx.Sprite("UI/White"), new Color(0.05f, 0.03f, 0.06f, 0.85f),
                          new Vector2(0.5f, 0f), new Vector2(-150f, 74f), new Vector2(300f, 66f));
        pedestalPanel = panel.gameObject;
        pedestalTitle = MakeLabel("Title", panel.rectTransform, "", 12, TextAnchor.UpperCenter, new Vector2(0f, 1f), new Vector2(0f, -4f), new Vector2(300f, 16f));
        pedestalTitle.color = new Color(1f, 0.85f, 0.4f);
        pedestalBody = MakeLabel("Body", panel.rectTransform, "", 9, TextAnchor.UpperCenter, new Vector2(0f, 1f), new Vector2(0f, -20f), new Vector2(300f, 14f));
        pedestalCost = MakeLabel("Cost", panel.rectTransform, "", 9, TextAnchor.UpperCenter, new Vector2(0f, 1f), new Vector2(0f, -34f), new Vector2(300f, 14f));
        var hint = MakeLabel("Hint", panel.rectTransform, "Walk onto it to buy it with heart containers", 8, TextAnchor.UpperCenter,
                         new Vector2(0f, 1f), new Vector2(0f, -50f), new Vector2(300f, 12f));
        hint.color = new Color(1f, 1f, 1f, 0.6f);
        pedestalPanel.SetActive(false);

        BuildMenus();

        // Fade to black (stairs between floors); drawn over everything
        var fade = MakeImage("Fade", root, Fx.Sprite("UI/White"), Color.black, Vector2.zero, Vector2.zero, Vector2.zero);
        Stretch(fade.rectTransform);
        fadeGroup = fade.gameObject.AddComponent<CanvasGroup>();
        fadeGroup.alpha = 0f;
    }

    // ---------------------------------------------------------------- updating

    void Update()
    {
        var gm = GameManager.Instance;
        UpdateHearts();
        UpdateAbilities();
        UpdateFloating();

        if (gm != null)
        {
            floorText.text = gm.Floor > 0 ? $"FLOOR {gm.Floor}" : "";
            bestText.text = gm.BestFloor > 0 ? $"BEST {gm.BestFloor}" : "";
            UpdateMinimap(gm);

            bool bossAlive = gm.Boss != null && !gm.Boss.IsDead;
            bossBar.SetActive(bossAlive);
            if (bossAlive)
            {
                bossName.text = gm.BossName;
                bossFill.fillAmount = Mathf.Clamp01(gm.Boss.health / (float)gm.Boss.MaxHealth);
            }

            UpdatePedestalPanel();
            bool title = gm.CurrentPhase == GameManager.Phase.Title;
            hudGroup.alpha = Mathf.MoveTowards(hudGroup.alpha, title ? 0f : 1f, 3f * Time.unscaledDeltaTime);
            bool dying = gm.CurrentPhase == GameManager.Phase.GameOver;
            deathTint.alpha = Mathf.MoveTowards(deathTint.alpha, dying ? 1f : 0f, 1.2f * Time.unscaledDeltaTime);
            UpdateMenus(gm);
        }

        // Banner fades out over its last 0.4 seconds (and stays hidden behind menus)
        if (bannerGroup.alpha > 0f || bannerTime < bannerDuration)
        {
            bannerTime += Time.unscaledDeltaTime;
            bool menuOpen = gm != null && (gm.Paused || gm.CurrentPhase == GameManager.Phase.Title);
            bannerGroup.alpha = menuOpen ? 0f : Mathf.Clamp01((bannerDuration - bannerTime) / 0.4f);
        }
        fadeGroup.alpha = Mathf.MoveTowards(fadeGroup.alpha, fadeTarget, fadeSpeed * Time.unscaledDeltaTime);
    }

    // Hearts: new containers pop in with a bounce + sparkle; healing fills in half a heart at a time
    void UpdateHearts()
    {
        if (playerHealth == null) return;
        int containers = (playerHealth.MaxHealth + 1) / 2;
        while (heartImages.Count < containers)
        {
            var img = MakeImage("Heart", heartsRow, heartFull, Color.white, new Vector2(0f, 1f),
                            new Vector2(heartImages.Count * 12f * HeartScale + 11f * HeartScale / 2f, -10f * HeartScale / 2f),
                            new Vector2(11f * HeartScale, 10f * HeartScale));
            img.rectTransform.pivot = new Vector2(0.5f, 0.5f);
            heartImages.Add(img);
            heartBounce.Add(0f);
        }

        if (shownHealth < 0) { shownHealth = playerHealth.Health; shownContainers = containers; }
        if (containers > shownContainers)
        {
            for (int i = shownContainers; i < containers; i++)
            {
                heartBounce[i] = 0.5f;
                Sparkle(heartImages[i].rectTransform);
            }
        }
        shownContainers = containers;

        // Refill gradually, drop instantly
        if (playerHealth.Health < shownHealth) shownHealth = playerHealth.Health;
        else if (playerHealth.Health > shownHealth)
        {
            refillTimer -= Time.unscaledDeltaTime;
            if (refillTimer <= 0f)
            {
                shownHealth++;
                refillTimer = 0.08f;
            }
        }

        if (hurtFlash > 0f) hurtFlash -= Time.unscaledDeltaTime;
        float flash = Mathf.Clamp01(hurtFlash / 0.35f);
        heartsRow.anchoredPosition = heartsRowHome + (flash > 0f ? Random.insideUnitCircle * 3f * flash : Vector2.zero);
        Color heartTint = Color.Lerp(Color.white, Mathf.Repeat(hurtFlash * 14f, 1f) < 0.5f ? new Color(1f, 0.25f, 0.25f) : Color.white, flash);

        for (int i = 0; i < heartImages.Count; i++)
        {
            var img = heartImages[i];
            img.color = heartTint;
            img.gameObject.SetActive(i < containers);
            if (i >= containers) continue;

            int capacity = Mathf.Min(2, playerHealth.MaxHealth - i * 2);    // 2 = whole container, 1 = half container
            int filled = Mathf.Clamp(shownHealth - i * 2, 0, capacity);
            if (capacity == 2) img.sprite = filled == 2 ? heartFull : filled == 1 ? heartHalf : heartEmpty;
            else img.sprite = filled == 1 ? halfContainerFull : halfContainerEmpty;

            float scale = 1f;
            if (heartBounce[i] > 0f)
            {
                heartBounce[i] -= Time.unscaledDeltaTime;
                float t = 1f - heartBounce[i] / 0.5f;
                scale = 1f + 0.8f * Mathf.Sin(t * Mathf.PI) * (1f - t * 0.5f);
            }
            img.rectTransform.localScale = new Vector3(scale, scale, 1f);
        }
    }

    // Little white sparks flying out of a UI element
    void Sparkle(RectTransform around)
    {
        for (int i = 0; i < 10; i++)
        {
            var spark = MakeImage("Spark", root, Fx.Sprite("UI/White"), new Color(1f, 0.95f, 0.8f), new Vector2(0f, 1f), Vector2.zero, new Vector2(3f, 3f));
            spark.rectTransform.pivot = new Vector2(0.5f, 0.5f);
            spark.rectTransform.position = around.position;
            float a = Random.value * Mathf.PI * 2f;
            floating.Add(new Floating
            {
                rt = spark.rectTransform,
                velocity = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * Random.Range(40f, 90f),
                life = Random.Range(0.3f, 0.55f),
                graphic = spark,
            });
        }
    }

    void UpdateFloating()
    {
        var cam = Camera.main;
        for (int i = floating.Count - 1; i >= 0; i--)
        {
            var f = floating[i];
            f.age += Time.unscaledDeltaTime;
            float t = f.age / f.life;
            if (t >= 1f || f.rt == null)
            {
                if (f.rt != null) Destroy(f.rt.gameObject);
                floating.RemoveAt(i);
                continue;
            }
            if (f.worldSpace && cam != null)
            {
                Vector3 screen = cam.WorldToScreenPoint(f.world + Vector3.up * (0.6f * t));
                RectTransformUtility.ScreenPointToLocalPointInRectangle(root, screen, null, out Vector2 local);
                f.rt.anchorMin = f.rt.anchorMax = new Vector2(0.5f, 0.5f);
                f.rt.anchoredPosition = local;
            }
            else f.rt.anchoredPosition += f.velocity * Time.unscaledDeltaTime;
            var c = f.graphic.color;
            c.a = 1f - t;
            f.graphic.color = c;
        }
    }

    // Visited rooms grey, the current room white, rooms seen through a door dark;
    // treasure and boss rooms get an icon once seen
    void UpdateMinimap(GameManager gm)
    {
        var map = gm.Map;
        var current = Room.Current != null ? Room.Current.Info : null;
        if (map == null) return;

        // Only rebuild when something changed
        var sb = new System.Text.StringBuilder();
        sb.Append(gm.Floor).Append(current != null ? current.cell.ToString() : "-");
        foreach (var r in map.Rooms.Values) sb.Append(r.seen ? (r.visited ? 'v' : 's') : '.');
        string state = sb.ToString();
        if (state == mapState) return;
        mapState = state;

        foreach (var go in mapCells) Destroy(go);
        mapCells.Clear();

        int minX = int.MaxValue, minY = int.MaxValue, maxX = int.MinValue, maxY = int.MinValue;
        foreach (var r in map.Rooms.Values)
        {
            if (!r.seen) continue;
            minX = Mathf.Min(minX, r.cell.x);
            minY = Mathf.Min(minY, r.cell.y);
            maxX = Mathf.Max(maxX, r.cell.x);
            maxY = Mathf.Max(maxY, r.cell.y);
        }
        if (maxX == int.MinValue) return;

        // Dark backdrop so the map reads over the wall
        float width = (maxX - minX + 1) * (MapCellW + MapGap) + MapGap * 2f;
        float height = (maxY - minY + 1) * (MapCellH + MapGap) + MapGap * 2f;
        var backdrop = MakeImage("Backdrop", minimap, Fx.Sprite("UI/White"), new Color(0f, 0f, 0f, 0.6f),
                                 new Vector2(1f, 1f), new Vector2(-width + MapGap, MapGap * 2f), new Vector2(width, height));
        mapCells.Add(backdrop.gameObject);

        foreach (var r in map.Rooms.Values)
        {
            if (!r.seen) continue;
            Color color = r == current ? Color.white : r.visited ? new Color(0.62f, 0.62f, 0.68f, 0.95f) : new Color(0.32f, 0.32f, 0.38f, 0.95f);
            Vector2 pos = new Vector2(-(maxX - r.cell.x) * (MapCellW + MapGap) - MapCellW, (r.cell.y - maxY) * (MapCellH + MapGap));
            var cell = MakeImage("Room", minimap, Fx.Sprite("UI/White"), color, new Vector2(1f, 1f), pos, new Vector2(MapCellW, MapCellH));
            mapCells.Add(cell.gameObject);

            string icon = r.type == RoomType.Treasure ? "UI/Map_Crown" : r.type == RoomType.Boss ? "UI/Map_Skull" : null;
            if (icon != null)
            {
                var ic = MakeImage("Icon", cell.rectTransform, Fx.Sprite(icon), Color.white, new Vector2(0.5f, 0.5f), new Vector2(-5f, 4f), new Vector2(10f, 8f));
                ic.preserveAspect = true;
            }
        }
    }

    void UpdateAbilities()
    {
        if (playerAbilities == null) return;
        if (slotsDirty) RebuildSlots();
        foreach (var slot in slots)
        {
            slot.cooldown.fillAmount = playerAbilities.CooldownFraction(slot.id);
            int lv = playerAbilities.Level(slot.id);
            slot.level.text = lv > 1 ? lv.ToString() : "";
        }
    }

    void RebuildSlots()
    {
        slotsDirty = false;
        foreach (Transform child in abilityBar) Destroy(child.gameObject);
        slots.Clear();

        int index = 0;
        foreach (var info in PlayerAbilities.All)
        {
            if (!playerAbilities.Has(info.id)) continue;
            var slot = MakeImage(info.name, abilityBar, Fx.Sprite("UI/White"), new Color(0.05f, 0.03f, 0.06f, 0.75f),
                             new Vector2(0f, 0f), new Vector2(index * 36f, 0f), new Vector2(32f, 32f));
            ((RectTransform)slot.transform).pivot = Vector2.zero;
            var icon = MakeImage("Icon", slot.rectTransform, Fx.Sprite(info.icon), Color.white, new Vector2(0.5f, 0.5f), new Vector2(-12f, 14f), new Vector2(24f, 24f));
            icon.preserveAspect = true;
            var cooldown = MakeImage("Cooldown", slot.rectTransform, Fx.Sprite("UI/White"), new Color(0f, 0f, 0f, 0.65f), new Vector2(0f, 1f), Vector2.zero, new Vector2(32f, 32f));
            cooldown.type = UnityEngine.UI.Image.Type.Filled;
            cooldown.fillMethod = UnityEngine.UI.Image.FillMethod.Radial360;
            cooldown.fillOrigin = (int)UnityEngine.UI.Image.Origin360.Top;
            cooldown.fillClockwise = false;
            cooldown.fillAmount = 0f;
            MakeLabel("Key", slot.rectTransform, info.key, 7, TextAnchor.LowerCenter, new Vector2(0f, 1f), new Vector2(0f, -22f), new Vector2(32f, 10f));
            var level = MakeLabel("Level", slot.rectTransform, "", 8, TextAnchor.UpperRight, new Vector2(0f, 1f), new Vector2(0f, 0f), new Vector2(31f, 10f));
            level.color = new Color(1f, 0.85f, 0.4f);
            slots.Add((info.id, cooldown, level));
            index++;
        }
    }

    // Info for the pedestal the knight is standing near
    void UpdatePedestalPanel()
    {
        Pedestal nearest = null;
        float best = 3f;
        foreach (var p in Pedestal.All)
        {
            if (p.Taken) continue;
            float d = p.DistanceToPlayer;
            if (d < best) { best = d; nearest = p; }
        }
        pedestalPanel.SetActive(nearest != null && playerAbilities != null);
        if (nearest == null || playerAbilities == null) return;

        var info = nearest.Info;
        int next = playerAbilities.Level(info.id) + 1;
        pedestalTitle.text = next == 1 ? $"{info.name}  (new)" : $"{info.name}  Lv {next}";
        pedestalBody.text = info.levels[Mathf.Clamp(next - 1, 0, info.MaxLevel - 1)];
        string cost = CostText(nearest.CostHalfHearts);
        if (nearest.CanAfford)
        {
            pedestalCost.text = $"Costs {cost}";
            pedestalCost.color = new Color(1f, 0.45f, 0.5f);
        }
        else
        {
            pedestalCost.text = $"Costs {cost} - not enough hearts";
            pedestalCost.color = new Color(0.6f, 0.6f, 0.6f);
        }
    }

    static string CostText(int halfHearts)
    {
        int whole = halfHearts / 2;
        bool half = halfHearts % 2 == 1;
        if (whole == 0) return "half a heart container";
        string hearts = whole == 1 ? "1" : whole.ToString();
        return half ? $"{hearts} and a half heart containers" : whole == 1 ? "1 heart container" : $"{hearts} heart containers";
    }

    // ---------------------------------------------------------------- helpers

    // Blackletter headings: larger, and in Title Case (all-caps blackletter is hard to read)
    void UseTitleFont(Text label)
    {
        label.font = titleFont;
        label.text = TitleCase(label.text);
    }

    static string TitleCase(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;
        return System.Globalization.CultureInfo.InvariantCulture.TextInfo.ToTitleCase(text.ToLowerInvariant());
    }

    static RectTransform MakeRect(string name, Transform parent, Vector2 anchor, Vector2 position, Vector2 size)
    {
        var go = new GameObject(name, typeof(RectTransform));
        var rt = (RectTransform)go.transform;
        rt.SetParent(parent, false);
        rt.anchorMin = rt.anchorMax = anchor;
        rt.pivot = new Vector2(0f, 1f);
        rt.anchoredPosition = position;
        rt.sizeDelta = size;
        return rt;
    }

    static void Stretch(RectTransform rt)
    {
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = rt.offsetMax = Vector2.zero;
    }

    static Image MakeImage(string name, Transform parent, Sprite sprite, Color color, Vector2 anchor, Vector2 position, Vector2 size)
    {
        var rt = MakeRect(name, parent, anchor, position, size);
        var img = rt.gameObject.AddComponent<Image>();
        img.sprite = sprite;
        img.color = color;
        img.raycastTarget = false;
        return img;
    }

    Text MakeLabel(string name, Transform parent, string text, int size, TextAnchor alignment, Vector2 anchor, Vector2 position, Vector2 boxSize)
    {
        var rt = MakeRect(name, parent, anchor, position, boxSize);
        var label = rt.gameObject.AddComponent<Text>();
        label.font = font;
        label.text = text;
        label.fontSize = size;
        label.fontStyle = FontStyle.Normal;
        label.alignment = alignment;
        label.color = Color.white;
        label.raycastTarget = false;
        label.horizontalOverflow = HorizontalWrapMode.Overflow;
        label.verticalOverflow = VerticalWrapMode.Overflow;
        var outline = rt.gameObject.AddComponent<Outline>();
        outline.effectColor = new Color(0f, 0f, 0f, 0.9f);
        outline.effectDistance = new Vector2(1f, -1f);
        return label;
    }
}
