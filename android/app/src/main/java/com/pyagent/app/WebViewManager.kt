package com.pyagent.app

import android.annotation.SuppressLint
import android.content.Context
import android.util.Log
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView

class WebViewManager(private val context: Context) {
    companion object {
        private const val TAG = "WebViewManager"
    }

    @SuppressLint("SetJavaScriptEnabled")
    fun createWebView(): WebView {
        val webView = WebView(context)
        
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = true
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView?,
                request: WebResourceRequest?
            ): Boolean {
                return false
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                Log.i(TAG, "Page finished loading: $url")
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                super.onProgressChanged(view, newProgress)
            }
        }

        return webView
    }

    fun loadUrl(webView: WebView, url: String) {
        Log.i(TAG, "Loading URL: $url")
        webView.loadUrl(url)
    }
}

@Composable
fun PyAgentWebView(url: String) {
    val context = LocalContext.current
    val webViewManager = remember { WebViewManager(context) }
    val webView = remember { webViewManager.createWebView() }

    DisposableEffect(url) {
        webViewManager.loadUrl(webView, url)
        onDispose {
            webView.destroy()
        }
    }

    AndroidView(
        factory = { webView },
        update = { view ->
            if (view.url != url) {
                webViewManager.loadUrl(view, url)
            }
        }
    )
}
