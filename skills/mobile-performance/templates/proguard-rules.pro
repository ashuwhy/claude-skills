# Goes into app.json as expo-build-properties > android > extraProguardRules,
# next to enableMinifyInReleaseBuilds and enableShrinkResourcesInReleaseBuilds.
# Every rule below exists because something is looked up by name at runtime,
# which R8 cannot see, so a missing rule fails on the phone and never at build
# time. Drop the blocks for libraries the app does not use, and prefer a
# library's own published consumer rules over these when it ships them.

# Razorpay drives checkout through a WebView JavascriptInterface and reflects
# on payment callbacks by name. These are Razorpay's own published rules.
-keepattributes *Annotation*
-keepattributes JavascriptInterface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
-dontwarn com.razorpay.**
-keep class com.razorpay.** { *; }
-optimizations !method/inlining/*
-keepclasseswithmembers class * {
  public void onPayment*(...);
}

# WebView bridges (react-native-webview, react-native-youtube-iframe): the
# player injects JS and reads state back over the same interface mechanism.
-keepclassmembers class * extends android.webkit.WebChromeClient {
    public void *(android.webkit.WebView, java.lang.String);
}

# Worklets are resolved by name on the UI thread. Reanimated ships consumer
# rules, but the worklets runtime is a separate artifact.
-keep class com.swmansion.reanimated.** { *; }
-keep class com.swmansion.worklets.** { *; }
-dontwarn com.swmansion.**

# expo-modules-core resolves native modules reflectively from their annotated
# definitions.
-keep class expo.modules.** { *; }
-keepclassmembers class * {
    @expo.modules.core.interfaces.ExpoProp <methods>;
    @expo.modules.core.interfaces.ExpoMethod <methods>;
}

# Supabase goes through OkHttp.
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn javax.annotation.**
