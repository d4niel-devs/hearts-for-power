using UnityEngine;

// The one place that sets Time.timeScale, so pause, hit freeze and slow motion never fight:
//   paused            -> 0
//   during a freeze   -> 0   (HitStop: a split-second stop when a hit lands, makes hits feel heavy)
//   otherwise         -> the slow-motion scale (1 normally; e.g. 0.3 while the knight dies)
public static class TimeControl
{
    static bool paused;
    static float freezeUntil;
    static float slowScale = 1f;
    static float slowUntil;
    static TimeRunner runner;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetStatics()
    {
        runner = null;
        Reset();
    }

    public static bool Paused
    {
        get => paused;
        set { paused = value; Apply(); }
    }

    // Back to normal speed (new run / restart)
    public static void Reset()
    {
        paused = false;
        freezeUntil = 0f;
        slowScale = 1f;
        slowUntil = 0f;
        Time.timeScale = 1f;
    }

    // Freeze the game for `seconds` of real time (if the Hit Freeze setting is on)
    public static void HitStop(float seconds)
    {
        if (!Settings.HitFreeze || paused) return;
        Ensure();
        freezeUntil = Mathf.Max(freezeUntil, Time.unscaledTime + seconds);
        Apply();
    }

    // Run at `scale` speed for `seconds` of real time
    public static void SlowMotion(float scale, float seconds)
    {
        Ensure();
        slowScale = scale;
        slowUntil = Time.unscaledTime + seconds;
        Apply();
    }

    static void Ensure()
    {
        if (runner != null) return;
        var go = new GameObject("TimeControl");
        Object.DontDestroyOnLoad(go);
        runner = go.AddComponent<TimeRunner>();
    }

    internal static void Tick()
    {
        if (slowUntil > 0f && Time.unscaledTime >= slowUntil)
        {
            slowScale = 1f;
            slowUntil = 0f;
        }
        Apply();
    }

    static void Apply()
    {
        bool frozen = Time.unscaledTime < freezeUntil;
        Time.timeScale = paused || frozen ? 0f : slowScale;
    }
}

// Updates TimeControl every frame on unscaled time (added at runtime)
public class TimeRunner : MonoBehaviour
{
    void Update() => TimeControl.Tick();
}
