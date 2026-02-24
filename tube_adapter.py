import cadquery as cq

class TubeAdapter:
    def __init__(self,
                 side_a_id=4.0, side_a_od=6.0, side_a_barb=False,
                 side_b_id=4.0, side_b_od=6.0, side_b_barb=False,
                 length=30.0,
                 num_barbs=3, barb_height_percentage=10.0, barb_width=2.0):
        self.side_a_id = float(side_a_id)
        self.side_a_od = float(side_a_od)
        self.side_a_barb = bool(side_a_barb)
        self.side_b_id = float(side_b_id)
        self.side_b_od = float(side_b_od)
        self.side_b_barb = bool(side_b_barb)
        self.length = float(length)
        self.num_barbs = int(num_barbs)
        self.barb_height_percentage = float(barb_height_percentage)
        self.barb_width = float(barb_width)
        self.cq_obj = None

    def render(self):
        # Validation
        if self.side_a_id >= self.side_a_od:
            raise ValueError(f"Side A ID ({self.side_a_id}) must be less than OD ({self.side_a_od})")
        if self.side_b_id >= self.side_b_od:
            raise ValueError(f"Side B ID ({self.side_b_id}) must be less than OD ({self.side_b_od})")
        if self.length <= 0:
            raise ValueError("Length must be positive")

        # Geometry Construction

        # Dimensions
        L = self.length

        section_len = L * 0.4
        trans_len = L * 0.2

        # Section A Cylinder (Z=0 to Z=section_len)
        cyl_a = cq.Workplane("XY").circle(self.side_a_od/2).extrude(section_len)

        # Section B Cylinder (Z=section_len+trans_len to Z=L)
        cyl_b = cq.Workplane("XY").workplane(offset=section_len + trans_len).circle(self.side_b_od/2).extrude(section_len)

        # Transition Cylinder (Z=section_len to Z=section_len+trans_len)
        trans = cq.Workplane("XY").workplane(offset=section_len).circle(self.side_a_od/2).workplane(offset=trans_len).circle(self.side_b_od/2).loft()

        # Combine
        body = cyl_a.union(trans).union(cyl_b)

        # Barb Logic
        def add_barbs(obj, od, section_start_z, section_len, direction):
            barb_h = od * (self.barb_height_percentage / 100.0)
            num_barbs = self.num_barbs
            barb_width = self.barb_width

            available_len = section_len

            # Check if barbs fit
            required_len = num_barbs * barb_width
            if required_len > available_len:
                raise ValueError(f"Barbs do not fit. Required {required_len:.2f}mm, available {available_len:.2f}mm")

            if num_barbs > 0:
                step = available_len / num_barbs

                for i in range(num_barbs):
                    slot_start = section_start_z + i * step

                    if direction == 'A':
                        z_pos = slot_start
                    else:
                        z_pos = slot_start + step - barb_width

                    if direction == 'A':
                        # Side A (Left): Insert Left->Right. Removal Right->Left.
                        # Vertical Face at Right (High Z). Ramp at Left (Low Z).
                        # Cone: Bottom(Low Z)=R_small, Top(High Z)=R_large
                        r1 = od / 2
                        r2 = od / 2 + barb_h
                    else:
                        # Side B (Right): Insert Right->Left. Removal Left->Right.
                        # Vertical Face at Left (Low Z). Ramp at Right (High Z).
                        # Cone: Bottom(Low Z)=R_large, Top(High Z)=R_small
                        r1 = od / 2 + barb_h
                        r2 = od / 2

                    # Create cone using loft
                    b = cq.Workplane("XY").workplane(offset=z_pos).circle(r1).workplane(offset=barb_width).circle(r2).loft()

                    obj = obj.union(b)
            return obj

        if self.side_a_barb:
            body = add_barbs(body, self.side_a_od, 0, section_len, 'A')

        if self.side_b_barb:
            body = add_barbs(body, self.side_b_od, section_len + trans_len, section_len, 'B')

        # Hole
        # Lofted hole through entire length
        hole_a = cq.Workplane("XY").circle(self.side_a_id/2).extrude(section_len)
        hole_b = cq.Workplane("XY").workplane(offset=section_len + trans_len).circle(self.side_b_id/2).extrude(section_len)
        hole_trans = cq.Workplane("XY").workplane(offset=section_len).circle(self.side_a_id/2).workplane(offset=trans_len).circle(self.side_b_id/2).loft()

        full_hole = hole_a.union(hole_trans).union(hole_b)

        adapter = body.cut(full_hole)

        self.cq_obj = adapter
        return self.cq_obj

    def save_step_file(self, filename):
        if not self.cq_obj: self.render()
        self.cq_obj.val().exportStep(filename)

    def save_stl_file(self, filename):
        if not self.cq_obj: self.render()
        self.cq_obj.val().exportStl(filename)
