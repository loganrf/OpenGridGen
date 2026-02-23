from flask import Flask, render_template, request, send_file, jsonify, after_this_request
import os
import tempfile
import json
import uuid
from generation_utils import (
    GeometryValidationError, GenerationError,
    generate_box_task, generate_baseplate_task, generate_lid_task,
    generate_gear_task, generate_hinge_task, generate_tube_adapter_task
)
from task_runner import run_task_with_timeout

app = Flask(__name__)

def send_and_remove(filepath, **kwargs):
    @after_this_request
    def remove_file(response):
        try:
            os.remove(filepath)
        except Exception as error:
            app.logger.error(f"Error removing or closing downloaded file handle: {error}")
        return response
    return send_file(filepath, **kwargs)

# Global settings (simplified for single-user local tool)
SETTINGS = {
    "GRU": 25.0,
    "GRHU": 5.0
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/box')
def box():
    return render_template('box.html')

@app.route('/baseplate')
def baseplate():
    return render_template('baseplate.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        SETTINGS["GRU"] = float(request.form.get('GRU', 25.0))
        SETTINGS["GRHU"] = float(request.form.get('GRHU', 5.0))
        return render_template('settings.html', settings=SETTINGS, message="Settings updated!")
    return render_template('settings.html', settings=SETTINGS)

@app.route('/api/generate_box_info', methods=['POST'])
def generate_box_info():
    try:
        data = request.json
        dims = run_task_with_timeout(
            generate_box_task,
            kwargs={'params': data, 'settings': SETTINGS},
            timeout=30
        )
        return jsonify({"success": True, "dimensions": dims})
    except TimeoutError:
        return jsonify({"success": False, "error": "Generation timed out"}), 408
    except GeometryValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/preview_box', methods=['POST'])
def preview_box():
    try:
        data = request.json
        filename = f"preview_box_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        dims = run_task_with_timeout(
            generate_box_task,
            kwargs={'params': data, 'settings': SETTINGS, 'output_path': filepath, 'format': 'stl'},
            timeout=60
        )

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except TimeoutError:
        return jsonify({"success": False, "error": "Generation timed out"}), 408
    except GeometryValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download_box', methods=['POST'])
def download_box():
    try:
        # Form data handling
        params = {
            'width': int(request.form.get('width', 1)),
            'length': int(request.form.get('length', 1)),
            'height': int(request.form.get('height', 1)),
            'solid': request.form.get('solid') == 'true'
        }
        format_type = request.form.get('format', 'step').lower()

        user_filename = f"box_{params['width']}x{params['length']}x{params['height']}.{format_type}"
        disk_filename = f"download_box_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        run_task_with_timeout(
            generate_box_task,
            kwargs={'params': params, 'settings': SETTINGS, 'output_path': filepath, 'format': format_type},
            timeout=60
        )

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except TimeoutError:
        return "Generation timed out", 408
    except GeometryValidationError as e:
        return str(e), 422
    except Exception as e:
        return str(e), 500

@app.route('/lid')
def lid():
    return render_template('lid.html')

@app.route('/api/preview_lid', methods=['POST'])
def preview_lid():
    try:
        data = request.json
        filename = f"preview_lid_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        dims = run_task_with_timeout(
            generate_lid_task,
            kwargs={'params': data, 'settings': SETTINGS, 'output_path': filepath, 'format': 'stl'},
            timeout=60
        )

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except TimeoutError:
        return jsonify({"success": False, "error": "Generation timed out"}), 408
    except GeometryValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download_lid', methods=['POST'])
def download_lid():
    try:
        params = {
            'width': int(request.form.get('width', 1)),
            'length': int(request.form.get('length', 1)),
            'height': float(request.form.get('height', 0.5)),
            'handle_style': request.form.get('handle_style', 'none'),
            'handle_height': float(request.form.get('handle_height', 5.0))
        }
        format_type = request.form.get('format', 'step').lower()

        user_filename = f"lid_{params['width']}x{params['length']}.{format_type}"
        disk_filename = f"download_lid_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        run_task_with_timeout(
            generate_lid_task,
            kwargs={'params': params, 'settings': SETTINGS, 'output_path': filepath, 'format': format_type},
            timeout=60
        )

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except TimeoutError:
        return "Generation timed out", 408
    except GeometryValidationError as e:
        return str(e), 422
    except Exception as e:
        return str(e), 500

@app.route('/api/generate_baseplate_info', methods=['POST'])
def generate_baseplate_info():
    try:
        data = request.json
        dims = run_task_with_timeout(
            generate_baseplate_task,
            kwargs={'params': data, 'settings': SETTINGS},
            timeout=30
        )
        return jsonify({"success": True, "dimensions": dims})
    except TimeoutError:
        return jsonify({"success": False, "error": "Generation timed out"}), 408
    except GeometryValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/preview_baseplate', methods=['POST'])
def preview_baseplate():
    try:
        data = request.json
        filename = f"preview_baseplate_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        dims = run_task_with_timeout(
            generate_baseplate_task,
            kwargs={'params': data, 'settings': SETTINGS, 'output_path': filepath, 'format': 'stl'},
            timeout=60
        )

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except TimeoutError:
        return jsonify({"success": False, "error": "Generation timed out"}), 408
    except GeometryValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download_baseplate', methods=['POST'])
def download_baseplate():
    try:
        params = {
            'width': int(request.form.get('width', 1)),
            'length': int(request.form.get('length', 1)),
            'padding_width': float(request.form.get('padding_width', 0)),
            'padding_length': float(request.form.get('padding_length', 0)),
            'corner_screws': request.form.get('corner_screws') == 'true'
        }
        format_type = request.form.get('format', 'step').lower()

        user_filename = f"baseplate_{params['width']}x{params['length']}.{format_type}"
        disk_filename = f"download_baseplate_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        run_task_with_timeout(
            generate_baseplate_task,
            kwargs={'params': params, 'settings': SETTINGS, 'output_path': filepath, 'format': format_type},
            timeout=60
        )

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except TimeoutError:
        return "Generation timed out", 408
    except GeometryValidationError as e:
        return str(e), 422
    except Exception as e:
        return str(e), 500

@app.route('/gear')
def gear():
    return render_template('gear.html')

@app.route('/hinge')
def hinge():
    return render_template('hinge.html')

@app.route('/tube-adapter')
def tube_adapter():
    return render_template('tube_adapter.html')

@app.route('/api/preview_gear', methods=['POST'])
def preview_gear():
    try:
        data = request.json
        filename = f"preview_gear_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        dims = run_task_with_timeout(
            generate_gear_task,
            kwargs={'params': data, 'settings': SETTINGS, 'output_path': filepath, 'format': 'stl'},
            timeout=60
        )

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except TimeoutError:
        return jsonify({"success": False, "error": "Generation timed out"}), 408
    except GeometryValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download_gear', methods=['POST'])
def download_gear():
    try:
        params = {
            'teeth': int(request.form.get('teeth', 20)),
            'module': float(request.form.get('module', 1.0)),
            'width': float(request.form.get('width', 5.0)),
            'bore_d': float(request.form.get('bore_d', 5.0)),
            'pressure_angle': float(request.form.get('pressure_angle', 20.0)),
            'shaft_type': request.form.get('shaft_type', 'circle'),
            'helix_angle': float(request.form.get('helix_angle', 0.0)),
            'gear_type': request.form.get('gear_type', 'spur'),
            'backlash': float(request.form.get('backlash', 0.0))
        }
        format_type = request.form.get('format', 'step').lower()

        user_filename = f"gear_m{params['module']}_z{params['teeth']}.{format_type}"
        disk_filename = f"download_gear_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        run_task_with_timeout(
            generate_gear_task,
            kwargs={'params': params, 'settings': SETTINGS, 'output_path': filepath, 'format': format_type},
            timeout=120
        )

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except TimeoutError:
        return "Generation timed out", 408
    except GeometryValidationError as e:
        return str(e), 422
    except Exception as e:
        return str(e), 500

@app.route('/api/preview_tube_adapter', methods=['POST'])
def preview_tube_adapter():
    try:
        data = request.json
        filename = f"preview_tube_adapter_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        dims = run_task_with_timeout(
            generate_tube_adapter_task,
            kwargs={'params': data, 'settings': SETTINGS, 'output_path': filepath, 'format': 'stl'},
            timeout=60
        )

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except TimeoutError:
        return jsonify({"success": False, "error": "Generation timed out"}), 408
    except GeometryValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download_tube_adapter', methods=['POST'])
def download_tube_adapter():
    try:
        params = {
            'side_a_id': float(request.form.get('side_a_id', 4.0)),
            'side_a_od': float(request.form.get('side_a_od', 6.0)),
            'side_a_barb': request.form.get('side_a_barb') == 'true',
            'side_b_id': float(request.form.get('side_b_id', 4.0)),
            'side_b_od': float(request.form.get('side_b_od', 6.0)),
            'side_b_barb': request.form.get('side_b_barb') == 'true',
            'length': float(request.form.get('length', 30.0))
        }
        format_type = request.form.get('format', 'step').lower()

        user_filename = f"adapter_a{params['side_a_od']}_b{params['side_b_od']}.{format_type}"
        disk_filename = f"download_tube_adapter_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        run_task_with_timeout(
            generate_tube_adapter_task,
            kwargs={'params': params, 'settings': SETTINGS, 'output_path': filepath, 'format': format_type},
            timeout=60
        )

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except TimeoutError:
        return "Generation timed out", 408
    except GeometryValidationError as e:
        return str(e), 422
    except Exception as e:
        return str(e), 500

@app.route('/api/preview_hinge', methods=['POST'])
def preview_hinge():
    try:
        data = request.json
        filename = f"preview_hinge_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        dims = run_task_with_timeout(
            generate_hinge_task,
            kwargs={'params': data, 'settings': SETTINGS, 'output_path': filepath, 'format': 'stl'},
            timeout=60
        )

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except TimeoutError:
        return jsonify({"success": False, "error": "Generation timed out"}), 408
    except GeometryValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download_hinge', methods=['POST'])
def download_hinge():
    try:
        params = {
            'length': float(request.form.get('length', 40.0)),
            'width': float(request.form.get('width', 40.0)),
            'height': float(request.form.get('height', 5.0)),
            'pin_diam': float(request.form.get('pin_diam', 3.0)),
            'clearance': float(request.form.get('clearance', 0.4))
        }
        format_type = request.form.get('format', 'step').lower()

        user_filename = f"hinge_{params['length']}x{params['width']}.{format_type}"
        disk_filename = f"download_hinge_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        run_task_with_timeout(
            generate_hinge_task,
            kwargs={'params': params, 'settings': SETTINGS, 'output_path': filepath, 'format': format_type},
            timeout=60
        )

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except TimeoutError:
        return "Generation timed out", 408
    except GeometryValidationError as e:
        return str(e), 422
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=4242)
