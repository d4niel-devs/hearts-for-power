using UnityEngine;

// Drives Monster.controller / Boss.controller (MoveX, MoveY, IsMoving, plus Attacking / Slam for
// bosses) and flips the sprite so the right-facing Side art also covers walking left.
// Monsters always play their walk cycle; bosses (alwaysWalk off) idle when standing still.
// Facing comes from Face() when another script (e.g. EnemyChase) calls it; otherwise it
// follows the monster's actual movement. IsMoving follows actual movement unless ForceMoving is set.
[RequireComponent(typeof(Animator))]
public class MonsterAnimator : MonoBehaviour
{
    [Tooltip("The Side sprites are drawn facing right. Untick if a monster's art faces left.")]
    public bool artFacesRight = true;
    [Tooltip("Monsters are always chasing, so they always play their walk cycle. Bosses turn this off.")]
    public bool alwaysWalk = true;
    [Tooltip("Speed (units/sec) below which the monster counts as standing still (when alwaysWalk is off).")]
    public float moveThreshold = 0.1f;
    [Tooltip("How much stronger the other axis must be before the facing switches (stops flicker on diagonals).")]
    public float facingHysteresis = 1.3f;

    private static readonly int MoveX = Animator.StringToHash("MoveX");
    private static readonly int MoveY = Animator.StringToHash("MoveY");
    private static readonly int IsMoving = Animator.StringToHash("IsMoving");
    private static readonly int Attacking = Animator.StringToHash("Attacking");
    private static readonly int Slam = Animator.StringToHash("Slam");
    private static readonly int Charging = Animator.StringToHash("Charging");

    private Animator animator;
    private SpriteRenderer spriteRenderer;
    private Vector2 lastPosition;
    private Vector2 facing = Vector2.down;
    private bool facingControlled; // true once another script has called Face()
    private bool hasAttackParameters;
    private bool hasChargeParameter;

    public Vector2 Facing => facing;
    // When set, overrides whether the walk animation plays (e.g. a slime's whole hop, crouch included)
    public bool? ForceMoving { get; set; }

    void Awake()
    {
        animator = GetComponent<Animator>();
        spriteRenderer = GetComponent<SpriteRenderer>();
        lastPosition = transform.position;
        foreach (var p in animator.parameters)
        {
            if (p.nameHash == Attacking) hasAttackParameters = true;
            if (p.nameHash == Charging) hasChargeParameter = true;
        }
    }

    void LateUpdate()
    {
        Vector2 position = transform.position;
        Vector2 velocity = Time.deltaTime > 0f ? (position - lastPosition) / Time.deltaTime : Vector2.zero;
        lastPosition = position;

        bool moving = ForceMoving ?? (alwaysWalk || velocity.magnitude > moveThreshold);
        if (moving && !facingControlled && velocity.sqrMagnitude > 0.0001f) ApplyFacing(velocity);

        animator.SetBool(IsMoving, moving);
    }

    // Turns the monster toward a direction. Once called, facing is left to the caller
    // instead of being worked out from movement.
    public void Face(Vector2 direction)
    {
        facingControlled = true;
        ApplyFacing(direction);
    }

    // Starts the walk cycle from its first frame (slimes: lines the hop up with the leap)
    public void RestartWalk()
    {
        animator.Play("Walk", 0, 0f);
    }

    // Bosses: hold the attack windup pose
    public void SetAttacking(bool attacking)
    {
        if (hasAttackParameters) animator.SetBool(Attacking, attacking);
    }

    // Bosses: the charge run (Orc Warlord: axe held overhead)
    public void SetCharging(bool charging)
    {
        if (hasChargeParameter) animator.SetBool(Charging, charging);
    }

    // Bosses: play the slam once
    public void PlaySlam()
    {
        if (hasAttackParameters) animator.SetTrigger(Slam);
    }

    // Mirrors the sprite horizontally. faceLeft = true makes the monster look left.
    public void Flip(bool faceLeft)
    {
        if (spriteRenderer != null) spriteRenderer.flipX = artFacesRight ? faceLeft : !faceLeft;
    }

    void ApplyFacing(Vector2 direction)
    {
        if (direction.sqrMagnitude < 0.0001f) return;

        // Snap to 4 directions so the blend trees pick one clip. Keep the current axis until the
        // other one is clearly stronger, so walking diagonally doesn't flicker between views.
        float ax = Mathf.Abs(direction.x), ay = Mathf.Abs(direction.y);
        bool horizontal = facing.x != 0f ? ax * facingHysteresis >= ay : ax > ay * facingHysteresis;
        facing = horizontal
            ? new Vector2(Mathf.Sign(direction.x), 0f)
            : new Vector2(0f, Mathf.Sign(direction.y));

        animator.SetFloat(MoveX, facing.x);
        animator.SetFloat(MoveY, facing.y);

        // Only side views flip; up/down art keeps its last orientation
        if (facing.x != 0f) Flip(facing.x < 0f);
    }
}
