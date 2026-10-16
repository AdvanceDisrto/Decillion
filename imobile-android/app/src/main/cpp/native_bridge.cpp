// iMobile native bootstrap — sandbox-only runtime; no modem/VPU/mesh privileges.
#include <jni.h>
#include "im_crossplane.h"
#include <android/log.h>
#include <cerrno>
#include <cstdint>
#include <fstream>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace {
constexpr const char* kTag = "iMobileNative";
bool safe_path(const std::string& p) {
    return !p.empty() && p[0] == '/' && p.size() < 1024 &&
           p.find("..") == std::string::npos && p.find('\0') == std::string::npos;
}
bool initialize_local_ledger(const std::string& root) {
    const std::string ledger = root + "/imobile-ledger-v1.log";
    // App-private directory is supplied by Context.getFilesDir(); regular file,
    // never a world-accessible /tmp socket or network interface.
    std::ofstream out(ledger, std::ios::out | std::ios::app);
    if (!out.good()) return false;
    out << "schema=i-mobile-native-ledger/1 event=boot engine=local-only\n";
    out.flush();
    return out.good();
}
}  // namespace

extern "C" JNIEXPORT jboolean JNICALL
Java_io_im_core_ImApplication_bootUnderTheHoodSystem(
    JNIEnv* env, jobject /*self*/, jstring internal_storage_path) {
    if (internal_storage_path == nullptr) return JNI_FALSE;
    const char* raw = env->GetStringUTFChars(internal_storage_path, nullptr);
    if (!raw) return JNI_FALSE;
    std::string base(raw);
    env->ReleaseStringUTFChars(internal_storage_path, raw);
    if (!safe_path(base)) {
        __android_log_print(ANDROID_LOG_ERROR, kTag, "Invalid sandbox path");
        return JNI_FALSE;
    }
    const bool ok = initialize_local_ledger(base);
    im_mesh_stats native_test{};
    const bool shared_core_linked = (im_core_version() == IM_CORE_ABI_VERSION) &&
       (im_simulate_mesh(20, 20, 2, &native_test) == 0) &&
       (native_test.delivered_simulated == 20) &&
       (native_test.disconnected_nodes == 10);
    if (!shared_core_linked) {
        __android_log_print(ANDROID_LOG_ERROR, kTag, "Portable shared C++ core failed local software self-test");
    }
    __android_log_print(ok ? ANDROID_LOG_INFO : ANDROID_LOG_ERROR, kTag,
        "Local offline ledger %s. VPU, iCalcula model, mesh tunnel and gRPC are NOT started.",
        ok ? "initialized" : "unavailable");
    return (ok && shared_core_linked) ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jstring JNICALL
Java_io_im_core_ImApplication_nativeCapabilities(
    JNIEnv* env, jobject /*self*/) {
    const char* status = "{\"offline_ledger\":\"app-private\","
        "\"vpu_mmio\":false,\"wireguard_mesh\":false,\"grpc_daemon\":false,"
        "\"imodel_inference\":false,\"hardware_receipts\":false,\"portable_core_linked\":true}";
    return env->NewStringUTF(status);
}
