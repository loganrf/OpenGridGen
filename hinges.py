import cadquery as cq

class Hinge:
    def __init__(self, length=40.0, width=40.0, height=5.0, pin_diam=3.0, clearance=0.4):
        self.length = float(length)
        self.width = float(width)
        self.height = float(height)
        self.pin_diam = float(pin_diam)
        self.clearance = float(clearance)
        self.cq_obj = None

    def render(self):
        L = self.length
        W = self.width
        H = self.height
        D_pin = self.pin_diam
        cl = self.clearance

        # Knuckle diameter
        R_outer = H / 2.0
        R_pin = D_pin / 2.0

        # Leaf dimensions
        T_leaf = H / 2.0
        leaf_width = W / 2.0

        # Calculate knuckles
        num_knuckles = max(3, int(L / 10))
        if num_knuckles % 2 == 0:
            num_knuckles += 1

        k_len = (L - (num_knuckles - 1) * cl) / num_knuckles

        part_A_objs = []
        part_B_objs = []

        y_cursor = -L / 2.0

        for i in range(num_knuckles):
            y_pos = y_cursor + k_len / 2.0

            # Knuckle
            # Center at (0, y_pos, R_outer)
            knuckle = (
                 cq.Workplane("XY")
                 .workplane(offset=R_outer)
                 .center(0, y_pos)
                 .transformed(rotate=(90, 0, 0))
                 .cylinder(k_len, R_outer)
            )

            # Leaf
            # Box centered at (0, y_pos, T_leaf/2)
            # Before translation
            leaf_part = (
                cq.Workplane("XY")
                .center(0, y_pos)
                .box(leaf_width, k_len, T_leaf)
                .translate((0, 0, T_leaf/2.0)) # Move Z up
            )

            if i % 2 == 0:
                # Part A (Left)
                # leaf_part center currently at (0, y_pos, T/2)
                # Move to left: center X = -leaf_width/2
                leaf_part = leaf_part.translate((-leaf_width/2.0, 0, 0))
                part_A_objs.append(knuckle)
                part_A_objs.append(leaf_part)
            else:
                # Part B (Right)
                # Move to right: center X = leaf_width/2
                leaf_part = leaf_part.translate((leaf_width/2.0, 0, 0))
                part_B_objs.append(knuckle)
                part_B_objs.append(leaf_part)

            y_cursor += k_len + cl

        # The Pin
        # Centered at (0, 0, R_outer)
        pin_obj = (
            cq.Workplane("XY")
            .workplane(offset=R_outer)
            .transformed(rotate=(90, 0, 0))
            .cylinder(L, R_pin)
        )

        part_A_objs.append(pin_obj)

        # Fuse objects
        # Helper to union list
        def union_all(objs):
            if not objs: return cq.Workplane("XY")
            res = objs[0]
            for o in objs[1:]:
                res = res.union(o)
            return res

        part_A = union_all(part_A_objs)
        part_B = union_all(part_B_objs)

        # Cut hole in B
        hole_radius = R_pin + cl

        # Hole cutter
        hole_obj = (
            cq.Workplane("XY")
            .workplane(offset=R_outer)
            .transformed(rotate=(90, 0, 0))
            .cylinder(L * 1.1, hole_radius)
        )

        if part_B_objs:
            part_B = part_B.cut(hole_obj)

        self.cq_obj = part_A.union(part_B)
        return self.cq_obj

    def save_step_file(self, filename):
        if not self.cq_obj: self.render()
        self.cq_obj.val().exportStep(filename)

    def save_stl_file(self, filename):
        if not self.cq_obj: self.render()
        self.cq_obj.val().exportStl(filename)
