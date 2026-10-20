using UnityEngine;

// Press Space to swing the sword in an arc in front of the way the knight is facing.
// The grip stays in the knight's hand while the blade sweeps across the arc with white swing
// lines trailing behind it, damaging every enemy it passes over (see SwordDamage).
// The sword sprite should point right with its pivot on the grip (Knight_Sword.png).
public class SwordFollow : MonoBehaviour
{
    public Transform player;
    public Vector3 offset = Vector3.zero;   // extra world offset added to the hand position

    [Header("Hand position (player-local units; the knight sprite is 1 unit = 32px)")]
    [Tooltip("Facing down: the knight's right hand, on the left of the screen.")]
    public Vector2 handDown = new Vector2(-0.27f, -0.28f);
    [Tooltip("Facing up: the knight's right hand, on the right of the screen.")]
    public Vector2 handUp = new Vector2(0.27f, -0.28f);
    [Tooltip("Facing right. Mirrored automatically when facing left.")]
    public Vector2 handRight = new Vector2(-0.03f, -0.25f);
    [Tooltip("How far (world units) the grip is held out from the hand, in the facing direction.")]
    public float handReach = 0.3f;

    [Header("Swing")]
    public KeyCode swingKey = KeyCode.Space;
    [Tooltip("Total angle the blade sweeps through, centered on the facing direction.")]
    public float arcDegrees = 150f;
    public float swingDuration = 0.18f;
    [Tooltip("Time after a swing ends before the next one can start.")]
    public float swingCooldown = 0.12f;
    [Tooltip("Gap between the hand and the grip, along the blade.")]
    public float gripOffset = 0f;
    [Tooltip("World size of one sword pixel. 2/32 matches the knight (32px sprite at scale 2).")]
    public float worldUnitsPerPixel = 2f / 32f;
    public bool hideWhenIdle = true;

    [Header("Swing lines")]
    public Color trailColor = new Color(1f, 1f, 1f, 0.85f);
    public float trailTime = 0.12f;
    [Tooltip("Where along the blade each white line starts (0 = grip, 1 = tip).")]
    public float[] trailPoints = { 1f, 0.75f, 0.5f };

    private SpriteRenderer spriteRenderer;
    private SpriteRenderer playerRenderer;
    private PlayerMovement playerMovement;
    private PlayerHealth playerHealth;
    private PlayerAbilities playerAbilities;
    private SwordDamage swordDamage;
    private TrailRenderer[] trails;
    private float baseBladeLength;  // before Stronger Sword upgrades

    private float bladeLength;      // world units from grip to tip
    private float swingTimer;       // > 0 while swinging
    private float nextSwingTime;
    private float startAngle, endAngle, lastAngle;
    private Vector2 swingFacing = Vector2.down;
    private bool clockwise = true;  // alternates each swing

    public bool IsSwinging => swingTimer > 0f;

    void Start()
    {
        if (player == null) Debug.LogError("Player not assigned!");
        spriteRenderer = GetComponent<SpriteRenderer>();
        playerRenderer = player != null ? player.GetComponent<SpriteRenderer>() : null;
        playerMovement = player != null ? player.GetComponent<PlayerMovement>() : null;
        playerHealth = player != null ? player.GetComponent<PlayerHealth>() : null;
        playerAbilities = player != null ? player.GetComponent<PlayerAbilities>() : null;
        swordDamage = GetComponent<SwordDamage>();
        if (swordDamage == null) swordDamage = gameObject.AddComponent<SwordDamage>();
        swordDamage.SetAbilities(playerAbilities);

        // Hits are found by sweeping the arc, so a trigger collider isn't needed
        foreach (var col in GetComponents<Collider2D>()) col.enabled = false;

        ApplyPixelScale(1f);
        baseBladeLength = spriteRenderer.sprite != null
            ? spriteRenderer.sprite.bounds.max.x * transform.lossyScale.x
            : 1.3f;
        bladeLength = baseBladeLength;
        trails = CreateTrails();
        SetVisible(!hideWhenIdle);
    }

    void Update()
    {
        if (player == null) return;

        bool dead = playerHealth != null && playerHealth.IsDead;
        bool canSwing = !dead && !GameManager.InputLocked && !IsSwinging && Time.time >= nextSwingTime;
        if (canSwing && Input.GetKeyDown(swingKey)) StartSwing();

        if (IsSwinging)
        {
            swingTimer -= Time.deltaTime;
            float t = 1f - Mathf.Clamp01(swingTimer / swingDuration);
            float eased = 1f - (1f - t) * (1f - t);   // fast start, slows at the end
            float angle = Mathf.Lerp(startAngle, endAngle, eased);
            PlaceSword(angle);
            HitEnemiesSweptBetween(lastAngle, angle);
            lastAngle = angle;

            if (!IsSwinging) EndSwing();
        }
        else if (!hideWhenIdle)
        {
            // Resting: held low, pointing a little to the side of the facing direction
            swingFacing = CurrentFacing();
            PlaceSword(FacingAngle() - 60f);
        }
    }

    void StartSwing()
    {
        swingFacing = CurrentFacing();   // locked for the whole swing

        // Stronger Sword upgrades make the blade longer and the swing wider
        float lengthMultiplier = playerAbilities != null ? playerAbilities.SwordLengthMultiplier : 1f;
        ApplyPixelScale(lengthMultiplier);
        bladeLength = baseBladeLength * lengthMultiplier;

        float center = FacingAngle();
        float half = (arcDegrees + (playerAbilities != null ? playerAbilities.SwordArcBonus : 0f)) / 2f;
        startAngle = clockwise ? center + half : center - half;
        endAngle = clockwise ? center - half : center + half;
        clockwise = !clockwise;

        lastAngle = startAngle;
        swingTimer = swingDuration;
        Audio.Play("SwordSwing", 0.55f);
        swordDamage.BeginSwing();

        PlaceSword(startAngle);
        SetVisible(true);
        foreach (var trail in trails)
        {
            trail.Clear();          // no streak from wherever the sword was before
            trail.emitting = true;
        }
    }

    void EndSwing()
    {
        nextSwingTime = Time.time + swingCooldown;
        foreach (var trail in trails) trail.emitting = false;
        if (hideWhenIdle) SetVisible(false);
    }

    Vector2 CurrentFacing()
    {
        return playerMovement != null ? playerMovement.Facing : Vector2.down;
    }

    float FacingAngle()
    {
        return Mathf.Atan2(swingFacing.y, swingFacing.x) * Mathf.Rad2Deg;
    }

    // World position of the knight's sword hand for the facing used by this swing
    Vector3 HandPosition()
    {
        Vector2 local;
        if (swingFacing.y > 0.5f) local = handUp;
        else if (swingFacing.y < -0.5f) local = handDown;
        else local = new Vector2(handRight.x * Mathf.Sign(swingFacing.x), handRight.y);
        return player.TransformPoint(local) + offset + (Vector3)(swingFacing * handReach);
    }

    void PlaceSword(float angle)
    {
        Vector3 dir = new Vector3(Mathf.Cos(angle * Mathf.Deg2Rad), Mathf.Sin(angle * Mathf.Deg2Rad), 0f);
        transform.position = HandPosition() + dir * gripOffset;
        transform.rotation = Quaternion.Euler(0f, 0f, angle);

        // Behind the knight when facing away or when the blade is above him, in front otherwise
        if (playerRenderer != null)
        {
            bool behind = swingFacing.y > 0.5f || dir.y > 0.3f;
            int order = behind ? playerRenderer.sortingOrder - 1 : playerRenderer.sortingOrder + 1;
            spriteRenderer.sortingOrder = order;
            foreach (var trail in trails) trail.sortingOrder = order;
        }
    }

    // Damages enemies whose direction from the hand lies in the slice the blade just crossed
    void HitEnemiesSweptBetween(float fromAngle, float toAngle)
    {
        Vector2 center = HandPosition();
        float reach = gripOffset + bladeLength;
        float swept = Mathf.DeltaAngle(fromAngle, toAngle);
        const float padding = 12f;   // a little forgiveness for enemies at the edge of the blade

        foreach (var col in Physics2D.OverlapCircleAll(center, reach))
        {
            EnemyHealth enemy = col.GetComponentInParent<EnemyHealth>();
            Obstacle pot = enemy == null ? col.GetComponent<Obstacle>() : null;
            if (enemy == null && (pot == null || pot.kind != TileKind.Pot)) continue;

            Vector2 toEnemy = (Vector2)col.bounds.center - center;
            float enemyAngle = Mathf.Atan2(toEnemy.y, toEnemy.x) * Mathf.Rad2Deg;
            float fromStart = Mathf.DeltaAngle(fromAngle, enemyAngle);

            // Is the enemy between fromAngle and toAngle (in the swing's direction)?
            bool inSlice = swept >= 0f
                ? fromStart >= -padding && fromStart <= swept + padding
                : fromStart <= padding && fromStart >= swept - padding;
            // Right up against the knight: always hit
            bool touching = Vector2.Distance(col.bounds.center, player.position) < 0.5f;
            if (!inSlice && !touching) continue;
            if (enemy != null) swordDamage.TryHit(enemy, player.position);
            else pot.Break();   // pots shatter
        }
    }

    void ApplyPixelScale(float multiplier)
    {
        if (spriteRenderer.sprite == null) return;
        float ppu = spriteRenderer.sprite.pixelsPerUnit;
        float worldScale = worldUnitsPerPixel * ppu * multiplier;
        Vector3 parentScale = transform.parent != null ? transform.parent.lossyScale : Vector3.one;
        transform.localScale = new Vector3(worldScale / parentScale.x, worldScale / parentScale.y, 1f);
    }

    TrailRenderer[] CreateTrails()
    {
        var material = new Material(Shader.Find("Sprites/Default"));
        var result = new TrailRenderer[trailPoints.Length];
        float tipLocal = spriteRenderer.sprite != null ? spriteRenderer.sprite.bounds.max.x : 0.6f;

        for (int i = 0; i < trailPoints.Length; i++)
        {
            var point = new GameObject($"SwingLine{i}");
            point.transform.SetParent(transform, false);
            point.transform.localPosition = new Vector3(tipLocal * trailPoints[i], 0f, 0f);

            var trail = point.AddComponent<TrailRenderer>();
            trail.material = material;
            trail.time = trailTime;
            trail.minVertexDistance = 0.02f;
            trail.emitting = false;
            trail.numCapVertices = 2;
            // Outer line is the boldest; inner lines are thinner and fainter
            float strength = Mathf.Lerp(0.45f, 1f, trailPoints[i]);
            trail.widthCurve = new AnimationCurve(new Keyframe(0f, 0.09f * strength), new Keyframe(1f, 0f));
            var gradient = new Gradient();
            gradient.SetKeys(
                new[] { new GradientColorKey(trailColor, 0f), new GradientColorKey(trailColor, 1f) },
                new[] { new GradientAlphaKey(trailColor.a * strength, 0f), new GradientAlphaKey(0f, 1f) });
            trail.colorGradient = gradient;
            result[i] = trail;
        }
        return result;
    }

    void SetVisible(bool visible)
    {
        spriteRenderer.enabled = visible;
    }
}
