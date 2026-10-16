"""Local edge inference gRPC service. Requires generated protobuf stubs and a real
model adapter. Never emits fabricated model tokens or hardware attestations.

Install: python -m pip install grpcio grpcio-tools
Generate: python -m grpc_tools.protoc -I i-api/edge --python_out=i-api/edge --grpc_python_out=i-api/edge i-api/edge/inference.proto
Run: python i-api/edge/server.py --model /absolute/path/model.gguf --socket /tmp/i-edge.sock
"""
import argparse
import hashlib
import os
import pathlib
import stat
from concurrent import futures

from ledger import Ledger

def create_model(model_path, context_size):
    """Load real GGUF weights using llama-cpp-python; no dummy fallback."""
    path = pathlib.Path(model_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".gguf":
        raise FileNotFoundError("A real GGUF model file is required: " + str(path))
    from llama_cpp import Llama
    return Llama(model_path=str(path), n_ctx=context_size,
                 n_gpu_layers=int(os.environ.get("I_EDGE_GPU_LAYERS", "0")),
                 verbose=False)

def serve(model_path, socket_path, db_path, context_size):
    import grpc
    import inference_pb2 as pb
    import inference_pb2_grpc as rpc

    model = create_model(model_path, context_size)
    ledger = Ledger(db_path)

    class Service(rpc.MobileInferenceServiceServicer):
        def StreamInference(self, request, context):
            if not request.session_id or not request.prompt or not (1 <= request.max_tokens <= 2048):
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "session, prompt and max_tokens 1..2048 required")
            if not (0 <= request.temperature <= 2):
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "temperature outside 0..2")
            # llama.cpp streaming returns actual model output chunks, not
            # necessarily individual tokenizer tokens.
            try:
                chunks = model.create_completion(prompt=request.prompt, max_tokens=request.max_tokens,
                    temperature=request.temperature, stream=True)
                previous = None
                index = 0
                for chunk in chunks:
                    if not context.is_active():
                        return
                    token = chunk["choices"][0].get("text", "")
                    if not token:
                        continue
                    receipt = ledger.append(request.session_id, {
                        "event": "model-output-chunk", "index": index, "text_sha256":
                        hashlib.sha256(token.encode()).hexdigest(), "model_id": request.model_id,
                        "backend": "llama.cpp", "device_attested": False})
                    if previous is not None:
                        yield previous
                    previous = pb.InferenceResponse(token=token, token_index=index,
                        is_final=False, receipt_hash=receipt["receipt_hash"],
                        backend="llama.cpp", signing_key_id="",
                        cryptographic_sig=b"")
                    index += 1
                if previous is None:
                    receipt = ledger.append(request.session_id, {
                        "event": "empty-model-response", "model_id": request.model_id,
                        "backend": "llama.cpp", "device_attested": False})
                    yield pb.InferenceResponse(is_final=True, token_index=0,
                        receipt_hash=receipt["receipt_hash"], backend="llama.cpp")
                else:
                    previous.is_final = True
                    yield previous
            except Exception as exc:
                context.abort(grpc.StatusCode.INTERNAL, "Inference failed: " + type(exc).__name__)

        def VerifyStateAnchor(self, request, context):
            try:
                state = ledger.verify()
                valid = state["head"] == request.absolute_state_hash
                return pb.AnchorCheckResponse(is_valid_continuity=valid,
                    im_receipt_id=state["head"] if valid else "",
                    verification_scope=state["scope"])
            except Exception:
                return pb.AnchorCheckResponse(is_valid_continuity=False,
                    verification_scope="local verification failed")

    sock = pathlib.Path(socket_path)
    sock.parent.mkdir(parents=True, exist_ok=True)
    if sock.exists():
        if not stat.S_ISSOCK(sock.stat().st_mode):
            raise RuntimeError("Refusing to unlink non-socket: " + str(sock))
        sock.unlink()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    rpc.add_MobileInferenceServiceServicer_to_server(Service(), server)
    address = "unix:" + str(sock)
    if server.add_insecure_port(address) != 1:
        raise RuntimeError("Could not bind Unix socket " + address)
    server.start()
    os.chmod(sock, 0o600)
    print("i™ edge runtime active on local Unix socket", address, flush=True)
    try:
        server.wait_for_termination()
    finally:
        server.stop(grace=2)
        ledger.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Real local GGUF model file")
    parser.add_argument("--socket", default="/tmp/i-edge.sock")
    parser.add_argument("--ledger", default="./data/i-edge-ledger.sqlite3")
    parser.add_argument("--context", type=int, default=2048)
    args = parser.parse_args()
    serve(args.model, args.socket, args.ledger, args.context)
