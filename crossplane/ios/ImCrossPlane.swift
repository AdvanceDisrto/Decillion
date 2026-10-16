import ICoreC
import Foundation
// i™ shared C ABI wrapper. This is a Swift source bridge, not an iOS .ipa.
public struct IMeshTestResult {
    public let nodeCount: UInt32
    public let droppedNodes: UInt32
    public let simulatedPacketAssignments: UInt32
    public let stateDigest: UInt64
}
public enum IMeshBridgeError: Error { case invalidSimulation }
public enum IMeshBridge {
    public static func test(nodeCount: UInt32 = 20_000, packetCount: UInt32 = 20_000,
                            dropoutEvery: UInt32 = 2) throws -> IMeshTestResult {
        var result = im_mesh_stats()
        let status = im_simulate_mesh(nodeCount, packetCount, dropoutEvery, &result)
        guard status == 0 else { throw IMeshBridgeError.invalidSimulation }
        return IMeshTestResult(nodeCount: result.node_count,
                               droppedNodes: result.disconnected_nodes,
                               simulatedPacketAssignments: result.delivered_simulated,
                               stateDigest: result.aggregate_state)
    }
}
