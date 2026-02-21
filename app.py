from flask import Flask, render_template, request, send_file, jsonify
import cqgridfinity
import cqgridfinity.gf_baseplate
import cqgridfinity.gf_box
import cqgridfinity.gf_obj
import cqgridfinity.constants
import cadquery as cq
import os
import tempfile
import json
import uuid

app = Flask(__name__)

# Global settings (simplified for single-user local tool)
SETTINGS = {
    "GRU": 42.0,
    "GRHU": 7.0
}

def update_constants():
    gru = SETTINGS["GRU"]
    grhu = SETTINGS["GRHU"]

    # Update main constants module
    cqgridfinity.constants.GRU = gru
    cqgridfinity.constants.GRHU = grhu
    cqgridfinity.constants.GRU2 = gru / 2
    cqgridfinity.constants.GRU_CUT = gru + 0.2

    # List of modules to update
    modules = [
        cqgridfinity.gf_obj,
        cqgridfinity.gf_baseplate,
        cqgridfinity.gf_box,
    ]

    for mod in modules:
        if hasattr(mod, 'GRU'): mod.GRU = cqgridfinity.constants.GRU
        if hasattr(mod, 'GRHU'): mod.GRHU = cqgridfinity.constants.GRHU
        if hasattr(mod, 'GRU2'): mod.GRU2 = cqgridfinity.constants.GRU2
        if hasattr(mod, 'GRU_CUT'): mod.GRU_CUT = cqgridfinity.constants.GRU_CUT

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
        SETTINGS["GRU"] = float(request.form.get('GRU', 42.0))
        SETTINGS["GRHU"] = float(request.form.get('GRHU', 7.0))
        update_constants()
        return render_template('settings.html', settings=SETTINGS, message="Settings updated!")
    return render_template('settings.html', settings=SETTINGS)

@app.route('/api/generate_box_info', methods=['POST'])
def generate_box_info():
    update_constants()
    try:
        data = request.json
        width = int(data.get('width', 1))
        length = int(data.get('length', 1))
        height = int(data.get('height', 1))

        box = cqgridfinity.GridfinityBox(length, width, height)

        # Calculate bounding box
        # cqgridfinity objects have .cq_obj which is a CadQuery Workplane object
        # but to get bounding box we usually need the underlying shape
        # box.cq_obj.val().BoundingBox() returns a BoundingBox object

        bb = box.cq_obj.val().BoundingBox()
        dims = {
            "x": bb.xlen,
            "y": bb.ylen,
            "z": bb.zlen
        }

        return jsonify({"success": True, "dimensions": dims})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/preview_box', methods=['POST'])
def preview_box():
    update_constants()
    try:
        data = request.json
        width = int(data.get('width', 1))
        length = int(data.get('length', 1))
        height = int(data.get('height', 1))

        box = cqgridfinity.GridfinityBox(length, width, height)

        # Get dimensions
        bb = box.cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        filename = f"preview_box_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        box.save_stl_file(filepath)

        response = send_file(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/download_box', methods=['POST'])
def download_box():
    update_constants()
    try:
        width = int(request.form.get('width', 1))
        length = int(request.form.get('length', 1))
        height = int(request.form.get('height', 1))
        format_type = request.form.get('format', 'step').lower()

        box = cqgridfinity.GridfinityBox(length, width, height)

        filename = f"box_{width}x{length}x{height}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        if format_type == 'step':
            box.save_step_file(filepath)
        elif format_type == 'stl':
            box.save_stl_file(filepath)
        else:
            return "Invalid format", 400

        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return str(e), 500

@app.route('/api/generate_baseplate_info', methods=['POST'])
def generate_baseplate_info():
    update_constants()
    try:
        data = request.json
        width = int(data.get('width', 1))
        length = int(data.get('length', 1))

        bp = cqgridfinity.GridfinityBaseplate(length, width)

        bb = bp.cq_obj.val().BoundingBox()
        dims = {
            "x": bb.xlen,
            "y": bb.ylen,
            "z": bb.zlen
        }

        return jsonify({"success": True, "dimensions": dims})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/preview_baseplate', methods=['POST'])
def preview_baseplate():
    update_constants()
    try:
        data = request.json
        width = int(data.get('width', 1))
        length = int(data.get('length', 1))

        bp = cqgridfinity.GridfinityBaseplate(length, width)

        # Get dimensions
        bb = bp.cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        filename = f"preview_baseplate_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        bp.save_stl_file(filepath)

        response = send_file(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/download_baseplate', methods=['POST'])
def download_baseplate():
    update_constants()
    try:
        width = int(request.form.get('width', 1))
        length = int(request.form.get('length', 1))
        format_type = request.form.get('format', 'step').lower()

        bp = cqgridfinity.GridfinityBaseplate(length, width)

        filename = f"baseplate_{width}x{length}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        if format_type == 'step':
            bp.save_step_file(filepath)
        elif format_type == 'stl':
            bp.save_stl_file(filepath)
        else:
            return "Invalid format", 400

        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=4242)
