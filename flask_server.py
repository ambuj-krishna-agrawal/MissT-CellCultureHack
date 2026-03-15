"""
Flask API server for robot and lab automation.
Exposes motion, gripper, and pour actions as REST endpoints.

Usage:
  python flask_server.py                    # run on http://127.0.0.1:5050
  python flask_server.py --ngrok            # run and expose via ngrok (public URL)
  python flask_server.py --port 8080        # custom port

Requires: pip install -r requirements.txt
Ngrok: set NGROK_AUTH_TOKEN in env if using ngrok (see https://ngrok.com).
"""

import json
import os
import sys
import threading
from flask import Flask, Response, jsonify, request, stream_with_context

import automate

# Unbuffer stdout so request logs appear immediately (e.g. when run from IDE/ngrok)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

app = Flask(__name__)


@app.after_request
def _log_request(response):
    """Log every request so logs are visible (flush so they show when stdout is buffered)."""
    print(
        "%s - %s %s - %s"
        % (request.remote_addr, request.method, request.path, response.status_code),
        flush=True,
    )
    return response

# Single robot connection (lazy init)
_robot_lock = threading.Lock()
_rtde_c = None
_rtde_r = None
_gripper = None


def _get_robot():
    """Return (rtde_c, rtde_r, gripper) or (None, None, None) if not connected."""
    with _robot_lock:
        return _rtde_c, _rtde_r, _gripper


def _set_robot(rtde_c, rtde_r, gripper):
    with _robot_lock:
        global _rtde_c, _rtde_r, _gripper
        _rtde_c, _rtde_r, _gripper = rtde_c, rtde_r, gripper


def _require_robot():
    rtde_c, rtde_r, gripper = _get_robot()
    if rtde_c is None:
        resp = jsonify({"ok": False, "error": "Robot not initialized. Call POST /robot/init first."})
        resp.status_code = 503
        return None, resp
    return (rtde_c, rtde_r, gripper), None


# ---------- Root & health ----------

@app.route("/", methods=["GET", "HEAD"])
def root():
    """Root path: API info and links. Stops 404 when opening ngrok URL in browser."""
    return jsonify({
        "service": "MissT Cell Culture Flask API",
        "docs": "No Swagger; use the endpoints below.",
        "endpoints": {
            "health": "GET /health",
            "robot_status": "GET /robot/status",
            "robot_init": "POST /robot/init",
            "protocol_2_stream": "POST /protocol/2",
        },
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check (no robot required)."""
    return jsonify({"ok": True, "service": "flask_server"})


@app.route("/robot/status", methods=["GET"])
def robot_status():
    """Whether the robot is connected."""
    rtde_c, _, _ = _get_robot()
    return jsonify({"ok": True, "connected": rtde_c is not None})


# ---------- Robot init / disconnect ----------

@app.route("/robot/init", methods=["POST"])
def robot_init():
    """Initialize robot connection (UR + Robotiq gripper)."""
    global _rtde_c, _rtde_r, _gripper
    try:
        with _robot_lock:
            if _rtde_c is not None:
                try:
                    _rtde_c.stopScript()
                    _rtde_c.disconnect()
                except Exception:
                    pass
                _rtde_c, _rtde_r, _gripper = None, None, None
            _rtde_c, _rtde_r, _gripper = automate.init_robot()
        return jsonify({"ok": True, "message": "Robot initialized."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/robot/disconnect", methods=["POST"])
def robot_disconnect():
    """Disconnect from the robot."""
    global _rtde_c, _rtde_r, _gripper
    with _robot_lock:
        if _rtde_c is not None:
            try:
                _rtde_c.stopScript()
                _rtde_c.disconnect()
            except Exception:
                pass
            _rtde_c, _rtde_r, _gripper = None, None, None
    return jsonify({"ok": True, "message": "Disconnected."})


# ---------- Motion endpoints (delegate to automate) ----------

def _motion(name, fn):
    robot, err = _require_robot()
    if err is not None:
        return err
    rtde_c, rtde_r, gripper = robot
    try:
        fn(rtde_c, rtde_r, gripper)
        return jsonify({"ok": True, "action": name})
    except Exception as e:
        return jsonify({"ok": False, "action": name, "error": str(e)}), 500


@app.route("/robot/move/inside_incubator", methods=["POST"])
def move_inside_incubator():
    return _motion("move_inside_incubator", automate.move_inside_incubator)


@app.route("/robot/move/outside_incubator", methods=["POST"])
def move_outside_incubator():
    return _motion("move_outside_incubator", automate.move_outside_incubator)


@app.route("/robot/move/to_microscope", methods=["POST"])
def move_to_microscope():
    return _motion("move_to_microscope", automate.move_to_microscope)


@app.route("/robot/move/away_from_microscope", methods=["POST"])
def move_away_from_microscope():
    return _motion("move_away_from_microscope", automate.move_away_from_microscope)


@app.route("/robot/move/to_fridge", methods=["POST"])
def move_to_fridge():
    return _motion("move_to_fridge", automate.move_to_fridge)


@app.route("/robot/move/to_fridge_door", methods=["POST"])
def move_to_fridge_door():
    return _motion("move_to_fridge_door", automate.move_to_fridge_door)


@app.route("/robot/move/open_fridge_door", methods=["POST"])
def open_fridge_door():
    return _motion("open_fridge_door", automate.open_fridge_door)


@app.route("/robot/move/back_from_fridge_door", methods=["POST"])
def back_from_fridge_door():
    return _motion("back_from_fridge_door", automate.back_from_fridge_door)


@app.route("/robot/move/to_reagent", methods=["POST"])
def move_to_reagent():
    return _motion("move_to_reagent", automate.move_to_reagent)


@app.route("/robot/move/away_from_reagent", methods=["POST"])
def move_to_away_from_reagent():
    return _motion("move_to_away_from_reagent", automate.move_to_away_from_reagent)


@app.route("/robot/move/to_opener", methods=["POST"])
def move_to_opener():
    return _motion("move_towards_opener", automate.move_towards_opener)


# ---------- Gripper ----------

@app.route("/robot/gripper/open", methods=["POST"])
def gripper_open():
    robot, err = _require_robot()
    if err is not None:
        return err
    _, _, gripper = robot
    try:
        gripper.open()
        return jsonify({"ok": True, "action": "gripper_open"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/robot/gripper/close", methods=["POST"])
def gripper_close():
    robot, err = _require_robot()
    if err is not None:
        return err
    _, _, gripper = robot
    try:
        gripper.close()
        return jsonify({"ok": True, "action": "gripper_close"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------- Shake & pour ----------

@app.route("/robot/shake", methods=["POST"])
def shake():
    robot, err = _require_robot()
    if err is not None:
        return err
    rtde_c, rtde_r, _ = robot
    n_shakes = request.args.get("n_shakes", type=int, default=4)
    tilt_angle = request.args.get("tilt_angle", type=float, default=0.15)
    try:
        automate.shake(rtde_c, rtde_r, n_shakes=n_shakes, tilt_angle=tilt_angle)
        return jsonify({"ok": True, "action": "shake"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/robot/pour", methods=["POST"])
def pour():
    robot, err = _require_robot()
    if err is not None:
        return err
    rtde_c, rtde_r, _ = robot
    tilt = request.args.get("tilt", type=float, default=0.8)
    hold = request.args.get("hold", type=float, default=3.0)
    try:
        import tflask_motions
        tflask_motions.pour(rtde_c, rtde_r, tilt_angle=tilt, hold_sec=hold)
        return jsonify({"ok": True, "action": "pour"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------- Protocol 2 (streaming) ----------
@app.route("/protocol/2", methods=["POST"])
def protocol_2_stream_endpoint():
    """
    Run protocol 2 with streaming response (Server-Sent Events).
    Each event is a JSON object: {"step": int, "name": str, "message": str} or {"error": str}.
    """
    robot, err = _require_robot()
    if err is not None:
        return err
    rtde_c, rtde_r, gripper = robot

    def generate():
        try:
            rtde_c, rtde_r, gripper = None, None, None
            for step, name, message in automate.protocol_2_stream(rtde_c, rtde_r, gripper):
                data = json.dumps({"step": step, "name": name, "message": message})
                yield f"data: {data}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------- Run with optional ngrok ----------

def _find_available_port(start_port, host="0.0.0.0"):
    """Return first port in [start_port, start_port+50) that is free to bind."""
    import socket
    for port in range(start_port, start_port + 50):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return port
        except OSError:
            continue
    return start_port  # fallback; will fail with clear error if in use


def main():
    import argparse
    p = argparse.ArgumentParser(description="Flask API server for robot automation.")
    p.add_argument("--port", type=int, default=5050, help="Port for Flask (default 5050, avoids macOS AirPlay on 5000)")
    p.add_argument("--host", default="0.0.0.0", help="Bind host (default 0.0.0.0)")
    p.add_argument("--ngrok", action="store_true", help="Expose server via ngrok (public URL)")
    args = p.parse_args()

    port = _find_available_port(args.port, args.host)
    if port != args.port:
        print("Port %d in use, using %d instead." % (args.port, port))

    if args.ngrok:
        try:
            from pyngrok import ngrok
            if not os.environ.get("NGROK_AUTH_TOKEN"):
                print("Tip: set NGROK_AUTH_TOKEN (get one at https://dashboard.ngrok.com/get-started/your-authtoken)")
            # bind_tls=False → HTTP (no TLS); use True for HTTPS
            public_url = ngrok.connect(port, bind_tls=False)
            print("\n" + "=" * 60)
            print("NGROK: Public URL (HTTP, no TLS):")
            print("  %s" % public_url.public_url)
            print("=" * 60 + "\n")
        except Exception as e:
            print("Ngrok failed: %s" % e)
            print("Set NGROK_AUTH_TOKEN or run without --ngrok for local only.")
            raise SystemExit(1)

    app.run(host=args.host, port=port, threaded=True)


if __name__ == "__main__":
    main()
