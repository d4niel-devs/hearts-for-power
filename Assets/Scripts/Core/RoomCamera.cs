using UnityEngine;

// Keeps the whole current room in view: centers the orthographic camera on it and zooms so it fits
// the screen at any aspect ratio. When the knight walks into another room the camera slides over,
// like Isaac. Runs in the editor too (framing a default room-sized area), and provides screen shake.
[ExecuteAlways]
[RequireComponent(typeof(Camera))]
public class RoomCamera : MonoBehaviour
{
    [Tooltip("Objects whose name starts with this are treated as walls when no rooms are built (editor).")]
    public string wallNamePrefix = "Wall";
    [Tooltip("Extra space (world units) shown around the outside of the walls.")]
    public float padding = 0.25f;
    [Tooltip("Used when no rooms or walls exist.")]
    public Rect fallbackRoom = new Rect(-15f, -9f, 30f, 18f);
    [Tooltip("Camera depth. Must be in front of the sprites (negative), or they get clipped.")]
    public float cameraZ = -10f;
    [Tooltip("Seconds the camera takes to slide to the next room.")]
    public float slideTime = 0.35f;

    private static RoomCamera instance;
    private Camera cam;
    private float shakeAmount, shakeTime, shakeDuration;

    private Vector2 slideFrom;
    private Vector2 currentCenter;
    private Room lastRoom;
    private float slideTimer;

    void OnEnable()
    {
        cam = GetComponent<Camera>();
        cam.orthographic = true;
        instance = this;
        currentCenter = transform.position;
    }

    public static void Shake(float amount, float duration)
    {
        if (instance == null || !Application.isPlaying || !Settings.ScreenShake) return;
        if (amount >= instance.shakeAmount * (instance.shakeTime / Mathf.Max(0.0001f, instance.shakeDuration)))
        {
            instance.shakeAmount = amount;
            instance.shakeDuration = duration;
            instance.shakeTime = duration;
        }
    }

    // Jump straight to the current room (new floor) instead of sliding
    public static void Snap()
    {
        if (instance == null) return;
        instance.lastRoom = Room.Current;
        instance.slideTimer = 0f;
        if (Room.Current != null) instance.currentCenter = Room.Current.Outer.center;
    }

    void LateUpdate()
    {
        Rect room;
        if (Application.isPlaying && Room.Current != null) room = Room.Current.Outer;
        else RoomBounds.Measure(wallNamePrefix, fallbackRoom, out _, out room);

        room.xMin -= padding;
        room.xMax += padding;
        room.yMin -= padding;
        room.yMax += padding;

        // Fit whichever of width/height is the limiting side for the current screen shape
        float sizeForHeight = room.height / 2f;
        float sizeForWidth = room.width / 2f / cam.aspect;
        cam.orthographicSize = Mathf.Max(sizeForHeight, sizeForWidth);

        // Slide to a newly entered room
        if (Application.isPlaying && Room.Current != lastRoom)
        {
            if (lastRoom != null)
            {
                slideFrom = currentCenter;
                slideTimer = slideTime;
            }
            else currentCenter = room.center;
            lastRoom = Room.Current;
        }
        if (slideTimer > 0f)
        {
            slideTimer -= Time.unscaledDeltaTime;
            float t = Mathf.SmoothStep(0f, 1f, 1f - Mathf.Clamp01(slideTimer / slideTime));
            currentCenter = Vector2.Lerp(slideFrom, room.center, t);
        }
        else currentCenter = room.center;

        Vector2 shake = Vector2.zero;
        if (shakeTime > 0f && Application.isPlaying)
        {
            shakeTime -= Time.unscaledDeltaTime;
            shake = Random.insideUnitCircle * shakeAmount * Mathf.Clamp01(shakeTime / shakeDuration);
        }

        // A scaled camera distorts its view and one at the sprites' depth clips them, so keep both fixed
        transform.position = new Vector3(currentCenter.x + shake.x, currentCenter.y + shake.y, cameraZ);
        transform.localScale = Vector3.one;
    }
}
