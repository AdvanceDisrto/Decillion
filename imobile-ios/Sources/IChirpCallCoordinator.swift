import Foundation
import CallKit
import PushKit
import AVFAudio

/// Native call UI and VoIP token registration foundation.
/// Not activated until an authenticated iMobile backend can bind a token to a user.
/// A VoIP token must never be sent to a public unauthenticated endpoint.
@MainActor
final class IChirpCallCoordinator: NSObject, ObservableObject {
    static let shared = IChirpCallCoordinator()
    @Published private(set) var status = "Native incoming calls not enrolled"
    private var registry: PKPushRegistry?
    private var provider: CXProvider?
    private var callRoomById: [UUID: String] = [:]
    var onAnswer: ((String) -> Void)?
    var onEnd: ((String) -> Void)?
    var onToken: ((String) -> Void)?

    func startNativeCallsAfterAccountEnrollment() {
        guard registry == nil else { return }
        let config = CXProviderConfiguration(localizedName: "iChirp")
        config.supportsVideo = true
        config.maximumCallsPerCallGroup = 1
        config.supportedHandleTypes = [.generic]
        let callProvider = CXProvider(configuration: config)
        callProvider.setDelegate(self, queue: .main)
        provider = callProvider
        let pushRegistry = PKPushRegistry(queue: .main)
        pushRegistry.delegate = self
        pushRegistry.desiredPushTypes = [.voIP]
        registry = pushRegistry
        status = "Requesting VoIP push token; server registration required"
    }

    func showIncoming(roomId: String, callerName: String, video: Bool, uuid: UUID) {
        guard let provider else {
            status = "CallKit not initialized"
            return
        }
        let update = CXCallUpdate()
        update.remoteHandle = CXHandle(type: .generic, value: callerName)
        update.localizedCallerName = callerName
        update.hasVideo = video
        callRoomById[uuid] = roomId
        provider.reportNewIncomingCall(with: uuid, update: update) { [weak self] error in
            if let error {
                self?.callRoomById.removeValue(forKey: uuid)
                self?.status = "CallKit rejected incoming call: \(error.localizedDescription)"
            } else {
                self?.status = "Incoming iChirp call reported to iOS"
            }
        }
    }

    func reportEnded(uuid: UUID) {
        provider?.reportCall(with: uuid, endedAt: Date(), reason: .remoteEnded)
        callRoomById.removeValue(forKey: uuid)
    }
}

extension IChirpCallCoordinator: CXProviderDelegate {
    nonisolated func providerDidReset(_ provider: CXProvider) {
        Task { @MainActor in
            callRoomById.removeAll()
            status = "Calls reset by iOS"
        }
    }

    nonisolated func provider(_ provider: CXProvider, perform action: CXAnswerCallAction) {
        Task { @MainActor in
            guard let room = callRoomById[action.callUUID], let onAnswer else {
                action.fail()
                return
            }
            onAnswer(room)
            // Connection must be established by the app; never claim media is connected here.
            action.fulfill()
        }
    }

    nonisolated func provider(_ provider: CXProvider, perform action: CXEndCallAction) {
        Task { @MainActor in
            if let room = callRoomById.removeValue(forKey: action.callUUID) {
                onEnd?(room)
            }
            action.fulfill()
        }
    }
}

extension IChirpCallCoordinator: PKPushRegistryDelegate {
    nonisolated func pushRegistry(_ registry: PKPushRegistry,
                                 didUpdate pushCredentials: PKPushCredentials,
                                 for type: PKPushType) {
        guard type == .voIP else { return }
        let token = pushCredentials.token.map { String(format: "%02x", $0) }.joined()
        Task { @MainActor in
            status = "VoIP token obtained; authenticated registration required"
            onToken?(token)
        }
    }

    nonisolated func pushRegistry(_ registry: PKPushRegistry,
                                 didInvalidatePushTokenFor type: PKPushType) {
        Task { @MainActor in
            status = "VoIP token invalidated; remove old registration from server"
        }
    }

    nonisolated func pushRegistry(_ registry: PKPushRegistry,
                                 didReceiveIncomingPushWith payload: PKPushPayload,
                                 for type: PKPushType,
                                 completion: @escaping () -> Void) {
        guard type == .voIP else {
            completion()
            return
        }
        let data = payload.dictionaryPayload
        guard let roomId = data["room_id"] as? String,
              let callString = data["call_uuid"] as? String,
              let callUUID = UUID(uuidString: callString),
              roomId.count <= 128 else {
            // Do not intentionally send malformed VoIP pushes: iOS expects a call report.
            completion()
            return
        }
        let name = (data["caller_name"] as? String).flatMap { String($0.prefix(80)) } ?? "iMobile caller"
        let hasVideo = data["video"] as? Bool ?? false
        Task { @MainActor in
            showIncoming(roomId: roomId, callerName: name, video: hasVideo, uuid: callUUID)
            completion()
        }
    }
}
