import cadquery as cq
from math import cos, sin, tan, pi, sqrt, radians, acos, atan2

class Gear:
    def __init__(self, teeth=20, module=1.0, width=5.0, bore_d=5.0, pressure_angle=20.0, shaft_type='circle'):
        self.teeth = int(teeth)
        self.module = float(module)
        self.width = float(width)
        self.bore_d = float(bore_d)
        self.pressure_angle = float(pressure_angle)
        self.shaft_type = shaft_type
        self.cq_obj = None

    def render(self):
        m = self.module
        z = self.teeth
        phi = radians(self.pressure_angle)
        width = self.width

        d_pitch = m * z
        d_base = d_pitch * cos(phi)
        d_addendum = d_pitch + 2 * m
        d_dedendum = d_pitch - 2.5 * m

        r_pitch = d_pitch / 2.0
        r_base = d_base / 2.0
        r_addendum = d_addendum / 2.0
        r_dedendum = d_dedendum / 2.0

        if r_base >= r_addendum:
            r_base = r_dedendum # Fallback

        def get_involute_points(num_points=15):
            points = []
            if r_base < r_addendum:
                t_max = sqrt((r_addendum/r_base)**2 - 1)
            else:
                t_max = 0

            for i in range(num_points + 1):
                t = (i / num_points) * t_max
                x = r_base * (cos(t) + t * sin(t))
                y = r_base * (sin(t) - t * cos(t))
                points.append((x, y))
            return points

        points_inv = get_involute_points(15)

        theta_thick = pi / (2 * z)
        inv_alpha = tan(phi) - phi
        angle_offset = theta_thick - inv_alpha

        def rotate_point(pt, ang):
            x, y = pt
            c = cos(ang)
            s = sin(ang)
            return (x * c - y * s, x * s + y * c)

        # Upper flank (y > 0, angle > 0) - Root to Tip
        upper_flank = [rotate_point(p, angle_offset) for p in points_inv]

        # Lower flank (y < 0, angle < 0) - Root to Tip
        lower_flank = [(x, -y) for x, y in upper_flank]

        # Tooth profile CCW:
        # Up Lower Flank (RootL -> TipL)
        # Across Top Land (TipL -> TipR)
        # Down Upper Flank (TipR -> RootR)

        tooth_poly = lower_flank + list(reversed(upper_flank))

        full_points = []
        for i in range(z):
            angle = 2 * pi * i / z
            rotated_tooth = [rotate_point(p, angle) for p in tooth_poly]
            full_points.extend(rotated_tooth)

        # Create wire
        # We need to ensure it's closed. polyline(...).close() does that.
        # This will connect the last point (RootR of last tooth) to first point (RootL of first tooth).
        # This creates the Bottom Land.

        gear_wire = cq.Workplane("XY").polyline(full_points).close().wire()
        gear_face = gear_wire.extrude(width)

        # Add the bore
        if self.shaft_type == 'circle':
            gear_final = gear_face.faces(">Z").workplane().circle(self.bore_d / 2).cutThruAll()
        elif self.shaft_type == 'hex':
            # polygon(n, d) creates polygon with diameter d (circumscribed or inscribed?)
            # CadQuery polygon usually takes diameter of circumscribed circle.
            gear_final = gear_face.faces(">Z").workplane().polygon(6, self.bore_d).cutThruAll()
        elif self.shaft_type == 'd_cut':
            r = self.bore_d / 2
            flat_level = r * 0.9 # Default flat depth
            # Create a D shape
            d_plug = (
                cq.Workplane("XY")
                .circle(r)
                .cut(
                    cq.Workplane("XY")
                    .center(r, 0)
                    .moveTo(flat_level + r, 0)
                    .rect(2*r, 2*r)
                )
            )
            gear_final = gear_face.cut(d_plug.extrude(width))
        else:
            gear_final = gear_face.faces(">Z").workplane().circle(self.bore_d / 2).cutThruAll()

        self.cq_obj = gear_final
        return self.cq_obj

    def save_step_file(self, filename):
        if not self.cq_obj: self.render()
        self.cq_obj.val().exportStep(filename)

    def save_stl_file(self, filename):
        if not self.cq_obj: self.render()
        self.cq_obj.val().exportStl(filename)
