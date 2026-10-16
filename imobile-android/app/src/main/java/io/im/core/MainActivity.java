package io.im.core;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;

public final class MainActivity extends Activity {
    private WebView webView;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setBackgroundColor(0xff072622);
        TextView status = new TextView(this);
        status.setTextColor(0xffc2ffe8);
        status.setPadding(16,16,16,16);
        status.setText("i™ iMobile · Native ledger: " +
            (ImApplication.isNativeReady() ? "initialized" : "unavailable") +
            " · Mesh and VPU hardware: not connected");
        layout.addView(status);
        webView = new WebView(this);
        webView.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest req) {
                final String url = req.getUrl().toString();
                return !(req.isForMainFrame() && (
                    url.equals("https://i-the-one-buddy-preview.onrender.com/") ||
                    url.startsWith("https://i-the-one-buddy-preview.onrender.com/?") ||
                    url.startsWith("https://i-the-one-buddy-preview.onrender.com/#")));
            }
            @Override public void onReceivedError(WebView v, WebResourceRequest req,
                    android.webkit.WebResourceError error) {
                if (req.isForMainFrame()) v.loadUrl("file:///android_asset/offline.html");
            }
        });
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true); // Needed by our PWA; no JavascriptInterface is exposed.
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        layout.addView(webView, new LinearLayout.LayoutParams(-1,0,1f));
        setContentView(layout);
        webView.loadUrl("https://i-the-one-buddy-preview.onrender.com/");
    }
    @Override public void onBackPressed() {
        if(webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
    @Override protected void onDestroy() {
        if(webView != null){webView.destroy();webView=null;}
        super.onDestroy();
    }
}
