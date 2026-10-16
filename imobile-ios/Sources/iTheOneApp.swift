import SwiftUI
import WebKit

@main
struct ITheOneApp: App {
    var body: some Scene {
        WindowGroup {
            ITheOneView()
        }
    }
}

struct ITheOneView: View {
    @State private var showStatus = false
    var body: some View {
        ZStack(alignment: .bottomTrailing) {
            BuddyWebView()
                .ignoresSafeArea(edges: .bottom)
            Button {
                showStatus = true
            } label: {
                Label("Sorcery", systemImage: "bolt.shield.fill")
                    .padding(12)
                    .background(.regularMaterial, in: Capsule())
            }
            .padding()
        }
        .sheet(isPresented: $showStatus) {
            SorceryStatusView()
        }
    }
}

struct BuddyWebView: UIViewRepresentable {
    func makeUIView(context: Context) -> WKWebView {
        let view = WKWebView()
        view.isOpaque = false
        view.backgroundColor = UIColor(red: 0.02, green: 0.12, blue: 0.12, alpha: 1)
        view.allowsBackForwardNavigationGestures = true
        view.load(URLRequest(url: URL(string: "https://i-the-one-buddy-preview.onrender.com/")!))
        return view
    }
    func updateUIView(_ uiView: WKWebView, context: Context) {}
}

struct SorceryStatusView: View {
    @State private var report = "No checks executed"
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Checks use real HTTPS requests. No arbitrary host shell.")
                    Button("Check Buddy backend") {
                        Task { await checkHealth() }
                    }
                    .buttonStyle(.borderedProminent)
                    Text(report)
                        .font(.system(.footnote, design: .monospaced))
                        .textSelection(.enabled)
                }
                .padding()
            }
            .navigationTitle("i™ Sorcery")
        }
    }
    @MainActor private func checkHealth() async {
        guard let url = URL(string: "https://i-the-one-buddy-api.onrender.com/health") else { return }
        do {
            let (data,response) = try await URLSession.shared.data(from: url)
            guard let http = response as? HTTPURLResponse else { throw URLError(.badServerResponse) }
            report = "HTTP \(http.statusCode)\n" + (String(data: data, encoding: .utf8) ?? "Non-UTF8 response")
        } catch {
            report = "Unavailable: \(error.localizedDescription)"
        }
    }
}
