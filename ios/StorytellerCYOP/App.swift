import SwiftUI
import WebKit
import UIKit

// Storyteller CYOP — iOS wrapper around the bundled web app (www/index.html).
// The web app detects the shell via window.__CYOP_IOS__ (injected below) and
// disables Stripe checkout inside the app (Apple Guideline 3.1.1: digital
// subscriptions must use In-App Purchase).

struct CYOPWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.websiteDataStore = .default() // persistent localStorage for stories
        let marker = WKUserScript(
            source: "window.__CYOP_IOS__=true;",
            injectionTime: .atDocumentStart,
            forMainFrameOnly: false
        )
        cfg.userContentController.addUserScript(marker)

        let wv = WKWebView(frame: .zero, configuration: cfg)
        wv.navigationDelegate = context.coordinator
        wv.isOpaque = false
        wv.backgroundColor = UIColor(red: 244/255, green: 236/255, blue: 216/255, alpha: 1) // #f4ecd8 parchment
        wv.scrollView.contentInsetAdjustmentBehavior = .never

        if let url = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "www") {
            wv.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        }
        return wv
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKNavigationDelegate {
        func webView(_ webView: WKWebView,
                     decidePolicyFor navigationAction: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = navigationAction.request.url else {
                decisionHandler(.allow); return
            }
            if url.isFileURL { decisionHandler(.allow); return }
            // Anything external (a shared story link, etc.) opens in Safari.
            DispatchQueue.main.async { UIApplication.shared.open(url) }
            decisionHandler(.cancel)
        }
    }
}

@main
struct StorytellerCYOPApp: App {
    var body: some Scene {
        WindowGroup {
            CYOPWebView()
                .ignoresSafeArea()
        }
    }
}
