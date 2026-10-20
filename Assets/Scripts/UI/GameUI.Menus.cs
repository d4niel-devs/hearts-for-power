using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

// The title screen, pause menu, settings and death screen, in a dark-dungeon style: a vignette,
// embers drifting up, stone tablets with iron studs, and a bleeding heart run through by a sword
// beating on the title. The selected option just lights up (no arrows).
// All menus work with the keyboard (W/S or arrows to move, A/D or arrows to change a setting,
// Enter/Space to pick, Esc/Backspace to go back) and the mouse (hover to select, click to pick;
// click the left/right half of a setting to change it).
public partial class GameUI
{
    class MenuItem
    {
        public Text label;
        public Func<string> text;
        public Action select;
        public Action<int> adjust;     // settings: -1 / +1
    }

    class Menu
    {
        public GameObject panel;
        public readonly List<MenuItem> items = new List<MenuItem>();
        public int selected;
        public Action back;             // Esc
    }

    class Ember { public RectTransform rt; public Image img; public Vector2 velocity; public float life, age, sway; }

    static readonly Color MenuIdle = new Color(0.72f, 0.66f, 0.66f, 0.9f);
    static readonly Color MenuSelected = new Color(1f, 0.78f, 0.32f);
    static readonly Color BloodRed = new Color(0.9f, 0.16f, 0.22f);
    static readonly Color Parchment = new Color(0.95f, 0.86f, 0.78f);

    // While Settings is open, Esc goes back inside the menus instead of toggling pause
    public static bool MenuHandlesEscape => instance != null && instance.settingsOpen;

    private Menu titleMenu, pauseMenu, settingsMenu, deathMenu;
    private bool settingsOpen, controlsOpen;
    private GameObject controlsPanel;
    private Text titleBest, deathStats, deathBest, pauseInfo;
    private RectTransform emblem, titleWords;
    private float deathTimer, emberTimer;
    private Vector3 lastMouse;
    private Sprite vignette;
    private readonly List<Ember> embers = new List<Ember>();

    // ---------------------------------------------------------------- building

    void BuildMenus()
    {
        vignette = MakeVignette();

        // ---- title
        titleMenu = NewMenu("Title", new Color(0.03f, 0f, 0.03f, 0.8f));
        var t = titleMenu.panel.transform;
        emblem = MakeRect("Emblem", t, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(118f, 122f));
        emblem.pivot = new Vector2(0.5f, 0.5f);
        emblem.anchoredPosition = new Vector2(0f, 98f);
        var emblemImage = emblem.gameObject.AddComponent<Image>();
        emblemImage.sprite = Fx.Sprite("UI/TitleEmblem");
        emblemImage.raycastTarget = false;
        emblemImage.preserveAspect = true;

        titleWords = MakeRect("Words", t, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(600f, 60f));
        titleWords.pivot = new Vector2(0.5f, 0.5f);
        titleWords.anchoredPosition = new Vector2(0f, 46f);
        var words = MakeLabel("Text", titleWords, "Hearts for Power", 62, TextAnchor.MiddleCenter, new Vector2(0f, 1f), Vector2.zero, new Vector2(600f, 60f));
        words.font = titleFont;
        words.color = BloodRed;
        words.GetComponent<Outline>().effectDistance = new Vector2(2f, -2f);
        var shadow = words.gameObject.AddComponent<Shadow>();
        shadow.effectColor = new Color(0.25f, 0f, 0.04f, 1f);
        shadow.effectDistance = new Vector2(3f, -4f);

        var tagline = Centered(t, "Give up your heart.  Take its power.", 11, 14f, new Color(Parchment.r, Parchment.g, Parchment.b, 0.75f));
        tagline.fontStyle = FontStyle.Italic;
        MakePanel(t, new Vector2(0f, -50f), new Vector2(190f, 92f));
        AddItem(titleMenu, () => "PLAY", () => { Audio.Play("UiSelect"); GameManager.Instance.BeginRun(); }, y: -26f);
        AddItem(titleMenu, () => "SETTINGS", () => OpenSettings(), y: -50f);
        AddItem(titleMenu, () => "QUIT", () => GameManager.QuitGame(), y: -74f);
        titleBest = Centered(t, "", 10, -108f, new Color(1f, 0.85f, 0.4f, 0.75f));
        var footer = MakeLabel("Controls", t, "WASD move    SPACE sword    SHIFT dash    E bomb    Q R F C spells    ESC / P pause", 8,
                               TextAnchor.MiddleCenter, new Vector2(0.5f, 0f), new Vector2(-300f, 20f), new Vector2(600f, 12f));
        footer.color = new Color(1f, 1f, 1f, 0.35f);

        // ---- pause
        pauseMenu = NewMenu("Pause", new Color(0.02f, 0f, 0.03f, 0.62f));
        var p = pauseMenu.panel.transform;
        MakePanel(p, new Vector2(0f, 4f), new Vector2(230f, 214f));
        var paused = Centered(p, "Paused", 38, 84f, BloodRed);
        paused.font = titleFont;
        paused.gameObject.AddComponent<Shadow>().effectDistance = new Vector2(2f, -3f);
        MakeDivider(p, 62f);
        pauseInfo = Centered(p, "", 9, 46f, new Color(Parchment.r, Parchment.g, Parchment.b, 0.7f));
        pauseInfo.lineSpacing = 1.2f;
        AddItem(pauseMenu, () => "RESUME", () => GameManager.Instance.SetPaused(false), y: 16f);
        AddItem(pauseMenu, () => "RESTART", () => { Audio.Play("UiSelect"); GameManager.Instance.Restart(); }, y: -8f);
        AddItem(pauseMenu, () => "SETTINGS", () => OpenSettings(), y: -32f);
        AddItem(pauseMenu, () => "QUIT TO TITLE", () => { Audio.Play("UiSelect"); GameManager.Instance.QuitToTitle(); }, y: -56f);
        Centered(p, "ESC / P to resume", 8, -88f, new Color(1f, 1f, 1f, 0.35f));
        // (Esc itself is handled by the GameManager, which toggles pause)

        // ---- settings
        settingsMenu = NewMenu("Settings", new Color(0.02f, 0f, 0.03f, 0.72f));
        var st = settingsMenu.panel.transform;
        MakePanel(st, new Vector2(0f, 4f), new Vector2(290f, 236f));
        var settingsTitle = Centered(st, "Settings", 34, 94f, BloodRed);
        settingsTitle.font = titleFont;
        settingsTitle.gameObject.AddComponent<Shadow>().effectDistance = new Vector2(2f, -3f);
        MakeDivider(st, 74f);
        AddItem(settingsMenu, () => $"MUSIC   {Bar(Settings.MusicVolume)}", () => { },
                d => Settings.MusicVolume = Mathf.Round((Settings.MusicVolume + 0.1f * d) * 10f) / 10f, y: 50f);
        AddItem(settingsMenu, () => $"SOUND   {Bar(Settings.SfxVolume)}", () => { },
                d => { Settings.SfxVolume = Mathf.Round((Settings.SfxVolume + 0.1f * d) * 10f) / 10f; Audio.Play("SwordHit"); }, y: 26f);
        AddItem(settingsMenu, () => $"SCREEN SHAKE   {(Settings.ScreenShake ? "ON" : "OFF")}", () => Settings.ScreenShake = !Settings.ScreenShake,
                d => Settings.ScreenShake = !Settings.ScreenShake, y: 2f);
        AddItem(settingsMenu, () => $"HIT FREEZE   {(Settings.HitFreeze ? "ON" : "OFF")}", () => Settings.HitFreeze = !Settings.HitFreeze,
                d => Settings.HitFreeze = !Settings.HitFreeze, y: -22f);
        AddItem(settingsMenu, () => "CONTROLS", () => controlsOpen = true, y: -46f);
        AddItem(settingsMenu, () => "BACK", CloseSettings, y: -74f);
        Centered(st, "A / D to change    ESC to go back", 8, -100f, new Color(1f, 1f, 1f, 0.35f));
        settingsMenu.back = CloseSettings;

        // ---- controls (inside settings)
        var controls = MakeImage("Controls", root, Fx.Sprite("UI/White"), new Color(0.02f, 0f, 0.03f, 0.8f), Vector2.zero, Vector2.zero, Vector2.zero);
        Stretch(controls.rectTransform);
        AddVignette(controls.transform);
        controlsPanel = controls.gameObject;
        var c = controls.transform;
        MakePanel(c, new Vector2(0f, 0f), new Vector2(340f, 270f));
        var controlsTitle = Centered(c, "Controls", 32, 112f, BloodRed);
        controlsTitle.font = titleFont;
        controlsTitle.gameObject.AddComponent<Shadow>().effectDistance = new Vector2(2f, -3f);
        MakeDivider(c, 94f);
        string[,] keys =
        {
            { "W A S D", "Move" }, { "SPACE", "Swing your sword" }, { "SHIFT", "Dash (once unlocked)" }, { "E", "Drop a bomb (once unlocked)" },
            { "Q", "Magic Bolt" }, { "R", "Fireball" }, { "F", "Ice Shards" }, { "C", "Lightning" }, { "ESC / P", "Pause" },
        };
        for (int i = 0; i < keys.GetLength(0); i++)
        {
            var key = MakeLabel("Key", c, keys[i, 0], 11, TextAnchor.MiddleRight, new Vector2(0.5f, 0.5f), new Vector2(-150f, 84f - i * 17f), new Vector2(130f, 16f));
            key.color = MenuSelected;
            var what = MakeLabel("What", c, keys[i, 1], 11, TextAnchor.MiddleLeft, new Vector2(0.5f, 0.5f), new Vector2(-6f, 84f - i * 17f), new Vector2(170f, 16f));
            what.color = Parchment;
        }
        Centered(c, "Spells and upgrades are bought on pedestals with heart containers.", 8, -84f, new Color(1f, 0.55f, 0.6f, 0.9f));
        Centered(c, "Press any key to go back", 8, -112f, new Color(1f, 1f, 1f, 0.35f));
        controlsPanel.SetActive(false);

        // ---- death screen
        deathMenu = NewMenu("Death", new Color(0.12f, 0f, 0.02f, 0.62f));
        var dt = deathMenu.panel.transform;
        var died = Centered(dt, "You Died", 54, 128f, BloodRed);
        died.font = titleFont;
        died.GetComponent<Outline>().effectDistance = new Vector2(2f, -2f);
        died.gameObject.AddComponent<Shadow>().effectDistance = new Vector2(3f, -4f);
        MakePanel(dt, new Vector2(0f, -10f), new Vector2(240f, 208f));
        deathStats = MakeLabel("Stats", dt, "", 11, TextAnchor.UpperCenter, new Vector2(0.5f, 0.5f), new Vector2(-120f, 82f), new Vector2(240f, 100f));
        deathStats.color = Parchment;
        deathStats.lineSpacing = 1.25f;
        deathBest = Centered(dt, "", 15, -32f, Color.white);
        AddItem(deathMenu, () => "TRY AGAIN", () => { Audio.Play("UiSelect"); GameManager.Instance.Restart(); }, y: -60f);
        AddItem(deathMenu, () => "TITLE SCREEN", () => { Audio.Play("UiSelect"); GameManager.Instance.QuitToTitle(); }, y: -84f);
    }

    Menu NewMenu(string name, Color dim)
    {
        var bg = MakeImage(name, root, Fx.Sprite("UI/White"), dim, Vector2.zero, Vector2.zero, Vector2.zero);
        Stretch(bg.rectTransform);
        AddVignette(bg.transform);
        bg.gameObject.SetActive(false);
        return new Menu { panel = bg.gameObject };
    }

    void AddItem(Menu menu, Func<string> text, Action select, Action<int> adjust = null, float y = 0f)
    {
        var label = MakeLabel("Item", menu.panel.transform, text(), 15, TextAnchor.MiddleCenter, new Vector2(0.5f, 0.5f), new Vector2(-140f, y + 10f), new Vector2(280f, 20f));
        label.color = MenuIdle;
        menu.items.Add(new MenuItem { label = label, text = text, select = select, adjust = adjust });
    }

    // A label centred horizontally at height y (relative to the screen centre)
    Text Centered(Transform parent, string text, int size, float y, Color color)
    {
        var label = MakeLabel("Label", parent, text, size, TextAnchor.MiddleCenter, new Vector2(0.5f, 0.5f), new Vector2(-250f, y + 10f), new Vector2(500f, 20f));
        label.color = color;
        return label;
    }

    // A stone tablet with an iron rim (9-sliced, bricks tiled at the game's pixel size)
    void MakePanel(Transform parent, Vector2 center, Vector2 size)
    {
        var img = MakeImage("Panel", parent, Fx.Sprite("UI/Panel"), Color.white, new Vector2(0.5f, 0.5f),
                            new Vector2(center.x - size.x / 2f, center.y + size.y / 2f), size);
        img.type = Image.Type.Tiled;
        img.pixelsPerUnitMultiplier = 3.125f;     // 1 sprite pixel = 2 UI pixels (sprite 16 ppu vs canvas 100)
    }

    void MakeDivider(Transform parent, float y)
    {
        MakeImage("Divider", parent, Fx.Sprite("UI/Divider"), Color.white, new Vector2(0.5f, 0.5f), new Vector2(-90f, y + 7f), new Vector2(180f, 13.5f));
    }

    static string Bar(float value)
    {
        int filled = Mathf.RoundToInt(value * 10f);
        return new string('|', filled) + new string('.', 10 - filled) + $"  {filled * 10}%";
    }

    void AddVignette(Transform parent)
    {
        var img = MakeImage("Vignette", parent, vignette, Color.white, Vector2.zero, Vector2.zero, Vector2.zero);
        Stretch(img.rectTransform);
    }

    // Dark edges fading into a clear middle (built once, smooth-filtered)
    static Sprite MakeVignette()
    {
        const int w = 128, h = 72;
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
        var pixels = new Color32[w * h];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float dx = (x + 0.5f) / w * 2f - 1f, dy = (y + 0.5f) / h * 2f - 1f;
                float d = Mathf.Sqrt(dx * dx * 0.85f + dy * dy);
                float a = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.45f, 1.25f, d)) * 0.9f;
                pixels[y * w + x] = new Color(0.02f, 0f, 0.02f, a);
            }
        tex.SetPixels32(pixels);
        tex.Apply();
        return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 100f);
    }

    void OpenSettings()
    {
        Audio.Play("UiSelect");
        settingsOpen = true;
        settingsMenu.selected = 0;
    }

    void CloseSettings()
    {
        Audio.Play("UiBack");
        settingsOpen = false;
        controlsOpen = false;
    }

    // ---------------------------------------------------------------- per frame

    void UpdateMenus(GameManager gm)
    {
        bool title = gm.CurrentPhase == GameManager.Phase.Title;
        bool dead = gm.CurrentPhase == GameManager.Phase.GameOver;
        deathTimer = dead ? deathTimer + Time.unscaledDeltaTime : 0f;
        bool deathScreen = dead && deathTimer > 1.4f;         // after the knight's fall has played out
        if (!title && !gm.Paused && !dead) settingsOpen = controlsOpen = false;

        Menu active = null;
        if (settingsOpen) active = settingsMenu;
        else if (title) active = titleMenu;
        else if (deathScreen) active = deathMenu;
        else if (gm.Paused) active = pauseMenu;

        // Settings sit on top of the menu they were opened from
        titleMenu.panel.SetActive(title && !settingsOpen);
        pauseMenu.panel.SetActive(gm.Paused && !title && !dead && !settingsOpen);
        deathMenu.panel.SetActive(deathScreen && !settingsOpen);
        settingsMenu.panel.SetActive(settingsOpen && !controlsOpen);
        controlsPanel.SetActive(controlsOpen);

        if (title) AnimateTitle(gm);
        UpdateEmbers(title && !settingsOpen ? titleMenu.panel.transform : deathScreen ? deathMenu.panel.transform : null);
        if (pauseMenu.panel.activeSelf) FillPauseInfo(gm);
        if (deathScreen) FillDeathStats(gm);

        if (controlsOpen)
        {
            if (Input.anyKeyDown) { controlsOpen = false; Audio.Play("UiBack"); }
            return;
        }
        if (active != null) HandleMenu(active);
    }

    void AnimateTitle(GameManager gm)
    {
        titleBest.text = gm.BestFloor > 0 ? $"Deepest floor reached:  {gm.BestFloor}" : "";
        // the emblem beats like a heart: lub-dub ... lub-dub
        float beat = Mathf.Repeat(Time.unscaledTime, 1.15f);
        float pulse = Mathf.Exp(-Mathf.Pow((beat - 0.05f) / 0.05f, 2f)) * 0.07f + Mathf.Exp(-Mathf.Pow((beat - 0.27f) / 0.05f, 2f)) * 0.045f;
        emblem.localScale = new Vector3(1f + pulse, 1f + pulse, 1f);
        float bob = Mathf.Sin(Time.unscaledTime * 1.3f) * 2f;
        emblem.anchoredPosition = new Vector2(0f, 104f + bob);
        titleWords.anchoredPosition = new Vector2(0f, 46f + bob * 0.5f);
    }

    // Glowing embers drifting up the screen
    void UpdateEmbers(Transform parent)
    {
        if (parent != null)
        {
            emberTimer -= Time.unscaledDeltaTime;
            if (emberTimer <= 0f)
            {
                emberTimer = 0.09f;
                var img = MakeImage("Ember", parent, Fx.Sprite("UI/White"),
                                    UnityEngine.Random.value < 0.6f ? new Color(1f, 0.45f, 0.15f) : new Color(0.95f, 0.15f, 0.2f),
                                    new Vector2(0.5f, 0f), Vector2.zero, Vector2.one * UnityEngine.Random.Range(1.5f, 3f));
                img.rectTransform.anchoredPosition = new Vector2(UnityEngine.Random.Range(-330f, 330f), -4f);
                img.rectTransform.SetSiblingIndex(1);          // behind the logo and menus, above the dimming
                embers.Add(new Ember
                {
                    rt = img.rectTransform, img = img,
                    velocity = new Vector2(UnityEngine.Random.Range(-6f, 6f), UnityEngine.Random.Range(22f, 48f)),
                    life = UnityEngine.Random.Range(4f, 7f), sway = UnityEngine.Random.value * 6f,
                });
            }
        }
        for (int i = embers.Count - 1; i >= 0; i--)
        {
            var e = embers[i];
            e.age += Time.unscaledDeltaTime;
            if (e.rt == null || e.age >= e.life || parent == null || e.rt.parent != parent)
            {
                if (e.rt != null) Destroy(e.rt.gameObject);
                embers.RemoveAt(i);
                continue;
            }
            e.rt.anchoredPosition += (e.velocity + new Vector2(Mathf.Sin(e.age * 2f + e.sway) * 8f, 0f)) * Time.unscaledDeltaTime;
            var col = e.img.color;
            col.a = Mathf.Sin(Mathf.Clamp01(e.age / e.life) * Mathf.PI) * 0.85f;
            e.img.color = col;
        }
    }

    void FillPauseInfo(GameManager gm)
    {
        int seconds = Mathf.FloorToInt(gm.RunTime);
        pauseInfo.text = $"FLOOR {gm.Floor}  -  {Theme.DisplayName(Theme.Current).ToUpper()}\n" +
                         $"{seconds / 60}:{seconds % 60:00}  played     {gm.Kills}  slain";
    }

    void FillDeathStats(GameManager gm)
    {
        int seconds = Mathf.FloorToInt(gm.RunTime);
        deathStats.text =
            $"Floor reached:  {gm.Floor}\n" +
            $"Rooms cleared:  {gm.RoomsCleared}\n" +
            $"Monsters slain:  {gm.Kills}\n" +
            $"Champions slain:  {gm.ChampionsSlain}\n" +
            $"Bosses beaten:  {gm.BossesBeaten}\n" +
            $"Time:  {seconds / 60}:{seconds % 60:00}";
        if (gm.NewBest)
        {
            deathBest.text = "NEW BEST!";
            deathBest.color = Mathf.Repeat(Time.unscaledTime * 3f, 1f) < 0.5f ? MenuSelected : new Color(1f, 0.4f, 0.3f);
        }
        else
        {
            deathBest.text = $"Best: floor {gm.BestFloor}";
            deathBest.color = new Color(1f, 1f, 1f, 0.6f);
        }
    }

    void HandleMenu(Menu menu)
    {
        int count = menu.items.Count;
        bool up = Input.GetKeyDown(KeyCode.UpArrow) || Input.GetKeyDown(KeyCode.W);
        bool down = Input.GetKeyDown(KeyCode.DownArrow) || Input.GetKeyDown(KeyCode.S);
        bool left = Input.GetKeyDown(KeyCode.LeftArrow) || Input.GetKeyDown(KeyCode.A);
        bool right = Input.GetKeyDown(KeyCode.RightArrow) || Input.GetKeyDown(KeyCode.D);
        bool pick = Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter) || Input.GetKeyDown(KeyCode.Space);
        bool escape = Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.Backspace) ||
                      (menu == settingsMenu && Input.GetKeyDown(KeyCode.P));

        if (up) { menu.selected = (menu.selected + count - 1) % count; Audio.Play("UiMove"); }
        if (down) { menu.selected = (menu.selected + 1) % count; Audio.Play("UiMove"); }

        // Mouse: hovering selects, clicking picks (or changes a setting by clicking its left / right half)
        bool mouseMoved = (Input.mousePosition - lastMouse).sqrMagnitude > 0.5f;
        lastMouse = Input.mousePosition;
        int hovered = -1;
        for (int i = 0; i < count; i++)
        {
            if (RectTransformUtility.RectangleContainsScreenPoint(menu.items[i].label.rectTransform, Input.mousePosition, null))
                hovered = i;
        }
        if (hovered >= 0 && mouseMoved && hovered != menu.selected)
        {
            menu.selected = hovered;
            Audio.Play("UiMove", 0.6f);
        }

        var item = menu.items[menu.selected];
        if (Input.GetMouseButtonDown(0) && hovered >= 0)
        {
            menu.selected = hovered;
            item = menu.items[hovered];
            if (item.adjust != null)
            {
                RectTransformUtility.ScreenPointToLocalPointInRectangle(item.label.rectTransform, Input.mousePosition, null, out Vector2 local);
                item.adjust(local.x < item.label.rectTransform.rect.center.x ? -1 : 1);
                Audio.Play("UiMove");
            }
            else item.select();
        }
        else if (item.adjust != null && (left || right))
        {
            item.adjust(left ? -1 : 1);
            Audio.Play("UiMove");
        }
        else if (pick)
        {
            if (item.adjust != null) { item.adjust(1); Audio.Play("UiMove"); }
            else item.select();
        }
        else if (escape && menu.back != null) menu.back();

        // The selected option lights up; the rest stay muted
        for (int i = 0; i < menu.items.Count; i++)
        {
            var it = menu.items[i];
            it.label.text = it.text();
            it.label.color = i == menu.selected ? MenuSelected : MenuIdle;
        }
    }
}
