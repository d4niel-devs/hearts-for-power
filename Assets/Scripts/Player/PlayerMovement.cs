using System.Collections.Generic;
using UnityEngine;

public class PlayerMovement : MonoBehaviour
{
    public float moveSpeed = 5f; // Movement speed
    [Tooltip("How quickly knockback wears off (units/sec per sec).")]
    public float knockbackDecay = 40f;

    [Header("Dash (unlocked from a pedestal)")]
    public float dashSpeed = 16f;
    public float dashDuration = 0.16f;

    private Rigidbody2D rb;
    private Animator animator;
    private SpriteRenderer spriteRenderer;
    private int playerLayer, enemyLayer;
    private PlayerHealth health;
    private PlayerAbilities abilities;
    private Vector2 movement;
    private Vector2 knockback;
    private Vector2 facing = Vector2.down;

    private float dashTimer;
    private Vector2 dashDirection;
    private float ghostTimer;
    private readonly HashSet<EnemyHealth> dashHits = new HashSet<EnemyHealth>();

    // The 4-way direction the knight is facing (kept while standing still)
    public Vector2 Facing => facing;
    public bool IsDashing => dashTimer > 0f;

    // Parameters in Knight.controller
    private static readonly int MoveX = Animator.StringToHash("MoveX");
    private static readonly int MoveY = Animator.StringToHash("MoveY");
    private static readonly int IsMoving = Animator.StringToHash("IsMoving");

    void Awake()
    {
        // The knight always needs hearts and an ability list; add them if they were never set up
        health = GetComponent<PlayerHealth>();
        if (health == null) health = gameObject.AddComponent<PlayerHealth>();
        abilities = GetComponent<PlayerAbilities>();
        if (abilities == null) abilities = gameObject.AddComponent<PlayerAbilities>();

        playerLayer = LayerMask.NameToLayer("Player");
        enemyLayer = LayerMask.NameToLayer("Enemy");
        if (playerLayer >= 0) gameObject.layer = playerLayer;
        // Monsters can't shove the knight (or pin him against walls); touching one hurts and knocks him back instead
        if (playerLayer >= 0 && enemyLayer >= 0) Physics2D.IgnoreLayerCollision(playerLayer, enemyLayer, true);
    }

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        animator = GetComponent<Animator>();
        spriteRenderer = GetComponent<SpriteRenderer>();
    }

    void Update()
    {
        if (health.IsDead || (GameManager.InputLocked && !(GameManager.Instance != null && GameManager.Instance.Paused)))
        {
            movement = Vector2.zero;   // dead, or sliding into the next room
        }
        else
        {
            // Get input
            movement.x = Input.GetAxisRaw("Horizontal"); // A/D or Left/Right
            movement.y = Input.GetAxisRaw("Vertical");   // W/S or Up/Down
            movement.Normalize(); // prevents faster diagonal movement

            bool dashPressed = Input.GetKeyDown(KeyCode.LeftShift) || Input.GetKeyDown(KeyCode.RightShift);
            if (dashPressed && !IsDashing && !GameManager.InputLocked && abilities.TryUseDash()) StartDash();
        }

        if (IsDashing) WhileDashing();
        UpdateAnimation();
    }

    void FixedUpdate()
    {
        if (health.IsDead) return;   // the death animation moves him now
        // Move the player (plus any knockback from being hit); the room's walls stop him
        Vector2 velocity = IsDashing ? dashDirection * dashSpeed : movement * moveSpeed + knockback;
        rb.MovePosition(rb.position + velocity * Time.fixedDeltaTime);
        knockback = Vector2.MoveTowards(knockback, Vector2.zero, knockbackDecay * Time.fixedDeltaTime);

        if (IsDashing)
        {
            dashTimer -= Time.fixedDeltaTime;
            if (!IsDashing) EndDash();
        }
    }

    // Pushes the knight in a direction for a moment (used when he gets hit)
    public void Knockback(Vector2 velocity)
    {
        knockback = velocity;
    }

    void StartDash()
    {
        dashDirection = movement.sqrMagnitude > 0.01f ? movement.normalized : facing;
        dashTimer = dashDuration;
        Audio.Play("Dash", 0.7f);
        dashHits.Clear();
        knockback = Vector2.zero;
        health.GrantInvulnerability(dashDuration + 0.1f);
        Fx.Puff(transform.position + Vector3.down * 0.5f, new Color(0.8f, 0.8f, 0.9f), 6, 3f);
    }

    void WhileDashing()
    {
        ghostTimer -= Time.deltaTime;
        if (ghostTimer <= 0f)
        {
            ghostTimer = 0.03f;
            Fx.Ghost(spriteRenderer, new Color(0.5f, 0.75f, 1f, 0.6f), 0.25f);
        }

        int damage = abilities.DashDamage;
        if (damage <= 0) return;
        foreach (var col in Physics2D.OverlapCircleAll(transform.position, 0.7f))
        {
            var enemy = col.GetComponentInParent<EnemyHealth>();
            if (enemy != null && !enemy.IsDead && dashHits.Add(enemy))
                enemy.TakeDamage(damage, transform.position, 4f);
        }
    }

    void EndDash()
    {
    }

    void UpdateAnimation()
    {
        if (animator == null) return;

        bool moving = movement.sqrMagnitude > 0.01f || IsDashing;
        if (movement.sqrMagnitude > 0.01f)
        {
            // Snap to one of 4 directions so the blend trees pick a single clip (horizontal wins on diagonals)
            facing = Mathf.Abs(movement.x) >= Mathf.Abs(movement.y)
                ? new Vector2(Mathf.Sign(movement.x), 0f)
                : new Vector2(0f, Mathf.Sign(movement.y));
        }

        // Facing is kept while idle, so the idle tree faces the last move direction
        animator.SetFloat(MoveX, facing.x);
        animator.SetFloat(MoveY, facing.y);
        animator.SetBool(IsMoving, moving);
    }
}
