package io.im.core;

import android.app.Application;
import android.util.Log;

public final class ImApplication extends Application {
    private static final String TAG = "iMobile";
    private static boolean nativeReady;

    static { System.loadLibrary("im_under_the_hood"); }
    public native boolean bootUnderTheHoodSystem(String internalStoragePath);
    public native String nativeCapabilities();
    public static boolean isNativeReady() { return nativeReady; }

    @Override public void onCreate() {
        super.onCreate();
        nativeReady = bootUnderTheHoodSystem(getFilesDir().getAbsolutePath());
        Log.i(TAG, "Native sandbox ledger initialized: " + nativeReady);
        // Never claim a device radio, WireGuard tunnel or VPU engine is activated.
    }
}
