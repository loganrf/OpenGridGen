import cqgridfinity
import cadquery as cq

class GridfinityBoxLid(cqgridfinity.GridfinityBox):
    def __init__(self, length_u, width_u, height_u=1.0, handle_style="none", handle_height=5.0, **kwargs):
        # Force solid and no_lip for lid
        kwargs['solid'] = True
        kwargs['no_lip'] = True

        # Workaround for height=1.0 bug in cqgridfinity/cadquery-ocp
        if abs(height_u - 1.0) < 1e-6:
            height_u = 1.001

        super().__init__(length_u, width_u, height_u, **kwargs)
        self.handle_style = handle_style
        self.handle_height = handle_height

    def render(self):
        # Render the base box (lid body)
        box = super().render()

        if self.handle_style == "simple":
            # Calculate handle dimensions
            # Use bounding box to find top Z and dimensions
            bb = box.val().BoundingBox()
            top_z = bb.zmax

            # Handle size: 1/3 of the smallest dimension
            min_dim = min(bb.xlen, bb.ylen)
            h_width = min_dim / 3.0
            h_length = min_dim / 3.0 # Square handle base

            # Create handle geometry
            # Center on XY at top_z
            handle = (
                cq.Workplane("XY")
                .workplane(offset=top_z)
                .rect(h_width, h_length)
                .extrude(self.handle_height)
            )

            # Union the handle with the box
            box = box.union(handle)

        self._cq_obj = box
        return box
