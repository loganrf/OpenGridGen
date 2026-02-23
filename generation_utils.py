import cqgridfinity
import cqgridfinity.constants
import cqgridfinity.gf_baseplate
import cqgridfinity.gf_box
import cqgridfinity.gf_obj
import cadquery as cq
from math import sqrt
from gears import Gear
from hinges import Hinge
from gridfinity_lid import GridfinityBoxLid
from tube_adapter import TubeAdapter

class GeometryValidationError(Exception):
    pass

class GenerationError(Exception):
    pass

def update_constants(settings):
    """
    Update global cqgridfinity constants based on settings dictionary.
    """
    gru = settings.get("GRU", 25.0)
    grhu = settings.get("GRHU", 5.0)

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

def validate_geometry(cq_obj):
    """
    Validate the generated geometry.
    Checks for:
    - Validity (isValid())
    - Watertightness (isClosed()) for solids
    - Non-empty shapes
    """
    if not cq_obj:
        raise GeometryValidationError("Generated object is None")

    try:
        val = cq_obj.val()
    except Exception as e:
        raise GeometryValidationError(f"Failed to retrieve value from object: {e}")

    if not val:
        raise GeometryValidationError("Generated object value is empty")

    if not val.isValid():
        raise GeometryValidationError("Generated geometry is invalid (Topological validity check failed)")

    shape_type = val.ShapeType()

    # Check for watertightness if it's a solid
    if shape_type == "Solid":
        # Check if all shells are closed
        shells = val.Shells()
        if not shells:
             raise GeometryValidationError("Solid has no shells")
        for shell in shells:
            if not shell.Closed():
                raise GeometryValidationError("Solid contains an open shell (not watertight)")

    elif shape_type == "Compound":
        # Check all children solids
        for solid in val.Solids():
             shells = solid.Shells()
             if not shells:
                 raise GeometryValidationError("Compound contains a solid with no shells")
             for shell in shells:
                 if not shell.Closed():
                     raise GeometryValidationError("Compound contains a solid with an open shell (not watertight)")

    # Check for volume (if solid)
    if shape_type == "Solid":
        props = val.Volume()
        if props <= 0:
            raise GeometryValidationError("Generated solid has zero or negative volume")

    return True

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

def generate_box_task(params, settings, output_path=None, format=None):
    update_constants(settings)
    try:
        width = int(params.get('width', 1))
        length = int(params.get('length', 1))
        height = int(params.get('height', 1))
        solid = params.get('solid', False)

        box = cqgridfinity.GridfinityBox(length, width, height, solid=solid)

        # cq_obj is populated in __init__ for cqgridfinity objects usually,
        # or we might need to call render()?
        # cqgridfinity objects usually create geometry in __init__ and store in .cq_obj
        if not box.cq_obj:
            box.render() # Just in case

        validate_geometry(box.cq_obj)

        bb = box.cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        if output_path and format:
            if format == 'step':
                box.save_step_file(output_path)
            elif format == 'stl':
                box.save_stl_file(output_path)

        return dims
    except Exception as e:
        if isinstance(e, GeometryValidationError):
            raise e
        raise GenerationError(str(e))


def generate_tube_adapter_task(params, settings, output_path=None, format=None):
    try:
        side_a_id = float(params.get('side_a_id', 4.0))
        side_a_od = float(params.get('side_a_od', 6.0))
        side_a_barb = params.get('side_a_barb', False)
        side_b_id = float(params.get('side_b_id', 4.0))
        side_b_od = float(params.get('side_b_od', 6.0))
        side_b_barb = params.get('side_b_barb', False)
        length = float(params.get('length', 30.0))

        adapter_obj = TubeAdapter(side_a_id=side_a_id, side_a_od=side_a_od, side_a_barb=side_a_barb,
                                  side_b_id=side_b_id, side_b_od=side_b_od, side_b_barb=side_b_barb,
                                  length=length)

        cq_obj = adapter_obj.render()
        validate_geometry(cq_obj)

        bb = cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        if output_path and format:
            if format == 'step':
                adapter_obj.save_step_file(output_path)
            elif format == 'stl':
                adapter_obj.save_stl_file(output_path)

        return dims
    except Exception as e:
        if isinstance(e, GeometryValidationError):
            raise e
        raise GenerationError(str(e))

def generate_lid_task(params, settings, output_path=None, format=None):
    update_constants(settings)
    try:
        width = int(params.get('width', 1))
        length = int(params.get('length', 1))
        height = float(params.get('height', 0.5))
        handle_style = params.get('handle_style', 'none')
        handle_height = float(params.get('handle_height', 5.0))

        lid_obj = GridfinityBoxLid(length, width, height,
                                 handle_style=handle_style,
                                 handle_height=handle_height)

        cq_obj = lid_obj.render()
        validate_geometry(cq_obj)

        bb = cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        if output_path and format:
            if format == 'step':
                lid_obj.save_step_file(output_path)
            elif format == 'stl':
                lid_obj.save_stl_file(output_path)

        return dims
    except Exception as e:
        if isinstance(e, GeometryValidationError):
            raise e
        raise GenerationError(str(e))

def generate_baseplate_task(params, settings, output_path=None, format=None):
    update_constants(settings)
    try:
        width = int(params.get('width', 1))
        length = int(params.get('length', 1))
        padding_width = float(params.get('padding_width', 0))
        padding_length = float(params.get('padding_length', 0))
        corner_screws = params.get('corner_screws', False)

        kwargs = {}
        if corner_screws:
            kwargs['corner_screws'] = True
            kwargs['csk_hole'] = 3.6
            kwargs['csk_diam'] = 7.0

        bp = CustomGridfinityBaseplate(length, width,
                                     length_padding=padding_length,
                                     width_padding=padding_width,
                                     **kwargs)

        if not bp.cq_obj:
            bp.render() # Ensure geometry exists

        validate_geometry(bp.cq_obj)

        bb = bp.cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        if output_path and format:
            if format == 'step':
                bp.save_step_file(output_path)
            elif format == 'stl':
                bp.save_stl_file(output_path)

        return dims
    except Exception as e:
        if isinstance(e, GeometryValidationError):
            raise e
        raise GenerationError(str(e))

def generate_gear_task(params, settings, output_path=None, format=None):
    # Gears don't use gridfinity settings usually, but we pass them anyway
    try:
        teeth = int(params.get('teeth', 20))
        module = float(params.get('module', 1.0))
        width = float(params.get('width', 5.0))
        bore_d = float(params.get('bore_d', 5.0))
        pressure_angle = float(params.get('pressure_angle', 20.0))
        shaft_type = params.get('shaft_type', 'circle')
        helix_angle = float(params.get('helix_angle', 0.0))
        gear_type = params.get('gear_type', 'spur')
        backlash = float(params.get('backlash', 0.0))

        gear_obj = Gear(teeth=teeth, module=module, width=width,
                        bore_d=bore_d, pressure_angle=pressure_angle,
                        shaft_type=shaft_type, helix_angle=helix_angle,
                        gear_type=gear_type, backlash=backlash)

        cq_obj = gear_obj.render()
        validate_geometry(cq_obj)

        bb = cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        if output_path and format:
            if format == 'step':
                gear_obj.save_step_file(output_path)
            elif format == 'stl':
                gear_obj.save_stl_file(output_path)

        return dims
    except Exception as e:
        if isinstance(e, GeometryValidationError):
            raise e
        raise GenerationError(str(e))

def generate_hinge_task(params, settings, output_path=None, format=None):
    try:
        length = float(params.get('length', 40.0))
        width = float(params.get('width', 40.0))
        height = float(params.get('height', 5.0))
        pin_diam = float(params.get('pin_diam', 3.0))
        clearance = float(params.get('clearance', 0.4))

        hinge_obj = Hinge(length=length, width=width, height=height,
                          pin_diam=pin_diam, clearance=clearance)

        cq_obj = hinge_obj.render()
        validate_geometry(cq_obj)

        bb = cq_obj.val().BoundingBox()
        dims = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}

        if output_path and format:
            if format == 'step':
                hinge_obj.save_step_file(output_path)
            elif format == 'stl':
                hinge_obj.save_stl_file(output_path)

        return dims
    except Exception as e:
        if isinstance(e, GeometryValidationError):
            raise e
        raise GenerationError(str(e))
