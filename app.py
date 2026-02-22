from flask import Flask, render_template, request, send_file, jsonify, after_this_request
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
from math import sqrt
from gridfinity_lid import GridfinityBoxLid
from gears import Gear
from hinges import Hinge

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

def update_constants():
    gru = SETTINGS["GRU"]
    grhu = SETTINGS["GRHU"]

    scale_xy = gru / 42.0
    scale_z = grhu / 7.0
    SQRT2 = sqrt(2)

    # Update main constants module
    cqgridfinity.constants.GRU = gru
    cqgridfinity.constants.GRHU = grhu
    cqgridfinity.constants.GRU2 = gru / 2
    cqgridfinity.constants.GRU_CUT = gru + 0.2

    # Scale Hole Distance
    cqgridfinity.constants.GR_HOLE_DIST = 13.0 * scale_xy

    # Scale Base Registry radii
    cqgridfinity.constants.GR_BREG_R0 = 11.0 * scale_xy
    cqgridfinity.constants.GR_BREG_R1 = 8.0 * scale_xy

    # Update Heights
    cqgridfinity.constants.GR_BOT_H = grhu
    cqgridfinity.constants.GR_BASE_HEIGHT = 4.75 * scale_z

    GR_BASE_HEIGHT = cqgridfinity.constants.GR_BASE_HEIGHT

    # Base Profile
    GR_BASE_CHAMF_H = (0.98994949 / SQRT2) * scale_z
    GR_STR_H = 1.8 * scale_z
    GR_BASE_TOP_CHAMF = GR_BASE_HEIGHT - GR_BASE_CHAMF_H - GR_STR_H

    cqgridfinity.constants.GR_BASE_PROFILE = (
        (GR_BASE_TOP_CHAMF * SQRT2, 45),
        GR_STR_H,
        (GR_BASE_CHAMF_H * SQRT2, 45),
    )

    # Box Profile
    GR_BOX_CHAMF_H = (1.1313708 / SQRT2) * scale_z
    GR_BASE_CLR = 0.25 * scale_z
    GR_BOX_TOP_CHAMF = GR_BASE_HEIGHT - GR_BOX_CHAMF_H - GR_STR_H + GR_BASE_CLR

    cqgridfinity.constants.GR_BOX_PROFILE = (
        (GR_BOX_TOP_CHAMF * SQRT2, 45),
        GR_STR_H,
        (GR_BOX_CHAMF_H * SQRT2, 45),
    )

    # List of modules to update
    modules = [
        cqgridfinity.gf_obj,
        cqgridfinity.gf_baseplate,
        cqgridfinity.gf_box,
    ]

    keys_to_update = [
        'GRU', 'GRHU', 'GRU2', 'GRU_CUT',
        'GR_HOLE_DIST', 'GR_BREG_R0', 'GR_BREG_R1',
        'GR_BOT_H', 'GR_BASE_HEIGHT',
        'GR_BASE_PROFILE', 'GR_BOX_PROFILE'
    ]

    for mod in modules:
        for key in keys_to_update:
            if hasattr(mod, key):
                setattr(mod, key, getattr(cqgridfinity.constants, key))

class CustomGridfinityBaseplate(cqgridfinity.GridfinityBaseplate):
    def __init__(self, length_u, width_u, length_padding=0, width_padding=0, **kwargs):
        self.length_padding = length_padding
        self.width_padding = width_padding
        super().__init__(length_u, width_u, **kwargs)

    @property
    def length(self):
        return self.length_u * cqgridfinity.constants.GRU + self.length_padding

    @property
    def width(self):
        return self.width_u * cqgridfinity.constants.GRU + self.width_padding

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
        solid = data.get('solid', False)

        box = cqgridfinity.GridfinityBox(length, width, height, solid=solid)

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
        solid = data.get('solid', False)

        box = cqgridfinity.GridfinityBox(length, width, height, solid=solid)

        # Get dimensions
        bb = box.cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        filename = f"preview_box_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        box.save_stl_file(filepath)

        response = send_and_remove(filepath, mimetype='model/stl')
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
        solid = request.form.get('solid') == 'true'

        box = cqgridfinity.GridfinityBox(length, width, height, solid=solid)

        user_filename = f"box_{width}x{length}x{height}.{format_type}"
        disk_filename = f"download_box_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        if format_type == 'step':
            box.save_step_file(filepath)
        elif format_type == 'stl':
            box.save_stl_file(filepath)
        else:
            return "Invalid format", 400

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except Exception as e:
        return str(e), 500

@app.route('/lid')
def lid():
    return render_template('lid.html')

@app.route('/api/preview_lid', methods=['POST'])
def preview_lid():
    update_constants()
    try:
        data = request.json
        width = int(data.get('width', 1))
        length = int(data.get('length', 1))
        height = float(data.get('height', 0.5))
        handle_style = data.get('handle_style', 'none')
        handle_height = float(data.get('handle_height', 5.0))

        lid_obj = GridfinityBoxLid(length, width, height,
                                 handle_style=handle_style,
                                 handle_height=handle_height)

        # Get dimensions and update cq_obj
        cq_obj = lid_obj.render()
        bb = cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        filename = f"preview_lid_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        lid_obj.save_stl_file(filepath)

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/download_lid', methods=['POST'])
def download_lid():
    update_constants()
    try:
        width = int(request.form.get('width', 1))
        length = int(request.form.get('length', 1))
        height = float(request.form.get('height', 0.5))
        format_type = request.form.get('format', 'step').lower()
        handle_style = request.form.get('handle_style', 'none')
        handle_height = float(request.form.get('handle_height', 5.0))

        lid_obj = GridfinityBoxLid(length, width, height,
                                 handle_style=handle_style,
                                 handle_height=handle_height)
        lid_obj.render() # Update cq_obj

        user_filename = f"lid_{width}x{length}.{format_type}"
        disk_filename = f"download_lid_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        if format_type == 'step':
            lid_obj.save_step_file(filepath)
        elif format_type == 'stl':
            lid_obj.save_stl_file(filepath)
        else:
            return "Invalid format", 400

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except Exception as e:
        return str(e), 500

@app.route('/api/generate_baseplate_info', methods=['POST'])
def generate_baseplate_info():
    update_constants()
    try:
        data = request.json
        width = int(data.get('width', 1))
        length = int(data.get('length', 1))
        padding_width = float(data.get('padding_width', 0))
        padding_length = float(data.get('padding_length', 0))
        corner_screws = data.get('corner_screws', False)

        kwargs = {}
        if corner_screws:
            kwargs['corner_screws'] = True
            kwargs['csk_hole'] = 3.6
            kwargs['csk_diam'] = 7.0

        bp = CustomGridfinityBaseplate(length, width,
                                     length_padding=padding_length,
                                     width_padding=padding_width,
                                     **kwargs)

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
        padding_width = float(data.get('padding_width', 0))
        padding_length = float(data.get('padding_length', 0))
        corner_screws = data.get('corner_screws', False)

        kwargs = {}
        if corner_screws:
            kwargs['corner_screws'] = True
            kwargs['csk_hole'] = 3.6
            kwargs['csk_diam'] = 7.0

        bp = CustomGridfinityBaseplate(length, width,
                                     length_padding=padding_length,
                                     width_padding=padding_width,
                                     **kwargs)

        # Get dimensions
        bb = bp.cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        filename = f"preview_baseplate_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        bp.save_stl_file(filepath)

        response = send_and_remove(filepath, mimetype='model/stl')
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
        padding_width = float(request.form.get('padding_width', 0))
        padding_length = float(request.form.get('padding_length', 0))
        corner_screws = request.form.get('corner_screws') == 'true'

        kwargs = {}
        if corner_screws:
            kwargs['corner_screws'] = True
            kwargs['csk_hole'] = 3.6
            kwargs['csk_diam'] = 7.0

        bp = CustomGridfinityBaseplate(length, width,
                                     length_padding=padding_length,
                                     width_padding=padding_width,
                                     **kwargs)

        user_filename = f"baseplate_{width}x{length}.{format_type}"
        disk_filename = f"download_baseplate_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        if format_type == 'step':
            bp.save_step_file(filepath)
        elif format_type == 'stl':
            bp.save_stl_file(filepath)
        else:
            return "Invalid format", 400

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except Exception as e:
        return str(e), 500

@app.route('/gear')
def gear():
    return render_template('gear.html')

@app.route('/hinge')
def hinge():
    return render_template('hinge.html')

@app.route('/api/preview_gear', methods=['POST'])
def preview_gear():
    try:
        data = request.json
        teeth = int(data.get('teeth', 20))
        module = float(data.get('module', 1.0))
        width = float(data.get('width', 5.0))
        bore_d = float(data.get('bore_d', 5.0))
        pressure_angle = float(data.get('pressure_angle', 20.0))
        shaft_type = data.get('shaft_type', 'circle')
        helix_angle = float(data.get('helix_angle', 0.0))
        gear_type = data.get('gear_type', 'spur')
        backlash = float(data.get('backlash', 0.0))

        gear_obj = Gear(teeth=teeth, module=module, width=width,
                        bore_d=bore_d, pressure_angle=pressure_angle,
                        shaft_type=shaft_type, helix_angle=helix_angle,
                        gear_type=gear_type, backlash=backlash)

        cq_obj = gear_obj.render()
        bb = cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        filename = f"preview_gear_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        gear_obj.save_stl_file(filepath)

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/download_gear', methods=['POST'])
def download_gear():
    try:
        teeth = int(request.form.get('teeth', 20))
        module = float(request.form.get('module', 1.0))
        width = float(request.form.get('width', 5.0))
        bore_d = float(request.form.get('bore_d', 5.0))
        pressure_angle = float(request.form.get('pressure_angle', 20.0))
        shaft_type = request.form.get('shaft_type', 'circle')
        helix_angle = float(request.form.get('helix_angle', 0.0))
        gear_type = request.form.get('gear_type', 'spur')
        backlash = float(request.form.get('backlash', 0.0))
        format_type = request.form.get('format', 'step').lower()

        gear_obj = Gear(teeth=teeth, module=module, width=width,
                        bore_d=bore_d, pressure_angle=pressure_angle,
                        shaft_type=shaft_type, helix_angle=helix_angle,
                        gear_type=gear_type, backlash=backlash)
        gear_obj.render()

        user_filename = f"gear_m{module}_z{teeth}.{format_type}"
        disk_filename = f"download_gear_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        if format_type == 'step':
            gear_obj.save_step_file(filepath)
        elif format_type == 'stl':
            gear_obj.save_stl_file(filepath)
        else:
            return "Invalid format", 400

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except Exception as e:
        return str(e), 500

@app.route('/api/preview_hinge', methods=['POST'])
def preview_hinge():
    try:
        data = request.json
        length = float(data.get('length', 40.0))
        width = float(data.get('width', 40.0))
        height = float(data.get('height', 5.0))
        pin_diam = float(data.get('pin_diam', 3.0))
        clearance = float(data.get('clearance', 0.4))

        hinge_obj = Hinge(length=length, width=width, height=height,
                          pin_diam=pin_diam, clearance=clearance)

        cq_obj = hinge_obj.render()
        bb = cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        filename = f"preview_hinge_{uuid.uuid4()}.stl"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        hinge_obj.save_stl_file(filepath)

        response = send_and_remove(filepath, mimetype='model/stl')
        response.headers['X-Dimensions'] = json.dumps(dims)
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/download_hinge', methods=['POST'])
def download_hinge():
    try:
        length = float(request.form.get('length', 40.0))
        width = float(request.form.get('width', 40.0))
        height = float(request.form.get('height', 5.0))
        pin_diam = float(request.form.get('pin_diam', 3.0))
        clearance = float(request.form.get('clearance', 0.4))
        format_type = request.form.get('format', 'step').lower()

        hinge_obj = Hinge(length=length, width=width, height=height,
                          pin_diam=pin_diam, clearance=clearance)
        hinge_obj.render()

        user_filename = f"hinge_{length}x{width}.{format_type}"
        disk_filename = f"download_hinge_{uuid.uuid4()}.{format_type}"
        filepath = os.path.join(tempfile.gettempdir(), disk_filename)

        if format_type == 'step':
            hinge_obj.save_step_file(filepath)
        elif format_type == 'stl':
            hinge_obj.save_stl_file(filepath)
        else:
            return "Invalid format", 400

        return send_and_remove(filepath, as_attachment=True, download_name=user_filename)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=4242)
