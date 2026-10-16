import SwiftUI
import WebKit
import Contacts
import UserNotifications

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
    @State private var showContacts = false
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
            VStack {
                Spacer()
                HStack {
                    Button {
                        showContacts = true
                    } label: {
                        Label("Contacts & Alerts", systemImage: "person.crop.circle.badge.checkmark")
                            .padding(10)
                            .background(.regularMaterial, in: Capsule())
                    }
                    Spacer()
                }
                .padding(.horizontal)
                .padding(.bottom, 70)
            }
        }
        .sheet(isPresented: $showContacts) {
            MobileContactsAndAlertsView()
        }
        .sheet(isPresented: $showStatus) {
            SorceryStatusView()
        }
    }
}

struct BuddyWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }
    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        let view = WKWebView(frame: .zero, configuration: configuration)
        view.uiDelegate = context.coordinator
        view.isOpaque = false
        view.backgroundColor = UIColor(red: 0.02, green: 0.12, blue: 0.12, alpha: 1)
        view.allowsBackForwardNavigationGestures = true
        view.load(URLRequest(url: URL(string: "https://i-the-one-buddy-preview.onrender.com/")!))
        return view
    }
    func updateUIView(_ uiView: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKUIDelegate {
        @available(iOS 15.0, *)
        func webView(_ webView: WKWebView,
                     requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                     initiatedByFrame frame: WKFrameInfo,
                     type: WKMediaCaptureType,
                     decisionHandler: @escaping (WKPermissionDecision) -> Void) {
            // Let iOS and WebKit request camera/microphone consent, never auto-grant.
            decisionHandler(.prompt)
        }
    }
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

struct MobileContactsAndAlertsView: View {
    @State private var contacts: [String] = []
    @State private var info = "Contacts are never uploaded. Sync is optional."
    @State private var alertsInfo = "Notifications not requested."

    var body: some View {
        NavigationStack {
            List {
                Section("Device Contacts") {
                    Button("Request access & read contacts") {
                        requestContacts()
                    }
                    Text(info).font(.footnote)
                    ForEach(contacts, id: \.self) { name in
                        Text(name)
                    }
                }
                Section("iChirp alerts") {
                    Button("Allow i™ alerts & sounds") {
                        requestAlerts()
                    }
                    Text(alertsInfo).font(.footnote)
                    Text("Permission alone does not enable incoming call push delivery or background ringing. These require APNs and CallKit.")
                        .font(.footnote)
                }
            }
            .navigationTitle("iMobile Contacts")
        }
    }

    private func requestContacts() {
        let store = CNContactStore()
        store.requestAccess(for: .contacts) { granted, error in
            guard granted else {
                DispatchQueue.main.async { info = "Contact access not granted." }
                return
            }
            DispatchQueue.global(qos: .userInitiated).async {
                var names: [String] = []
                let keys = [CNContactGivenNameKey as CNKeyDescriptor, CNContactFamilyNameKey as CNKeyDescriptor]
                let request = CNContactFetchRequest(keysToFetch: keys)
                do {
                    try store.enumerateContacts(with: request) { contact, stop in
                        if names.count >= 200 {
                            stop.pointee = true
                            return
                        }
                        let name = [contact.givenName, contact.familyName]
                            .filter { !$0.isEmpty }.joined(separator: " ")
                        if !name.isEmpty { names.append(name) }
                    }
                    DispatchQueue.main.async {
                        contacts = names
                        info = "Loaded \(names.count) contact names on this iPhone. Not uploaded."
                    }
                } catch {
                    DispatchQueue.main.async { info = "Contact read failed." }
                }
            }
        }
    }

    private func requestAlerts() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            DispatchQueue.main.async {
                alertsInfo = granted ? "i™ notification permission granted. Push transport not yet configured." : "Notifications unavailable or denied."
            }
        }
    }
}
