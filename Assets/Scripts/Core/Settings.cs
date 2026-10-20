using UnityEngine;

// Player options, saved in PlayerPrefs. Changed from the Settings menu.
public static class Settings
{
    const string MusicKey = "Settings.MusicVolume";
    const string SfxKey = "Settings.SfxVolume";
    const string ShakeKey = "Settings.ScreenShake";
    const string FreezeKey = "Settings.HitFreeze";

    public static float MusicVolume
    {
        get => PlayerPrefs.GetFloat(MusicKey, 0.6f);
        set { PlayerPrefs.SetFloat(MusicKey, Mathf.Clamp01(value)); PlayerPrefs.Save(); Audio.RefreshVolume(); }
    }

    public static float SfxVolume
    {
        get => PlayerPrefs.GetFloat(SfxKey, 0.8f);
        set { PlayerPrefs.SetFloat(SfxKey, Mathf.Clamp01(value)); PlayerPrefs.Save(); }
    }

    public static bool ScreenShake
    {
        get => PlayerPrefs.GetInt(ShakeKey, 1) == 1;
        set { PlayerPrefs.SetInt(ShakeKey, value ? 1 : 0); PlayerPrefs.Save(); }
    }

    public static bool HitFreeze
    {
        get => PlayerPrefs.GetInt(FreezeKey, 1) == 1;
        set { PlayerPrefs.SetInt(FreezeKey, value ? 1 : 0); PlayerPrefs.Save(); }
    }
}
