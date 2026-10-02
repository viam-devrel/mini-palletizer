"""Generate the printable cube-and-pallet template for the mini-palletizer workshop.

Produces `cube-and-pallet-template.pdf`:
- two pages of fold-up cube nets (eight 20 mm cubes total)
- one pallet mat marking the 2x2 grid at 30 mm pitch, plus a cut-out staging square

Dimensions match the workshop code exactly: CUBE = 16 mm, PITCH = 30 mm.
Print at 100% scale (no "fit to page") so the millimeters come out right.

Run:  uv run --with reportlab python template/generate_template.py
"""

import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

CUBE = 16  # mm, cube side length
PITCH = 30  # mm, center-to-center pallet spacing
OUT = os.path.join(os.path.dirname(__file__), "cube-and-pallet-template.pdf")

CUT = (0.15, 0.15, 0.15)  # near-black solid cut lines
FOLD = (0.55, 0.55, 0.55)  # gray dashed fold lines


def draw_cube_net(c, ox, oy):
    """Draw one cube net (a cross) with its bounding-box bottom-left at (ox, oy)."""
    s = CUBE * mm

    def pt(cx, ry):
        return (ox + cx * s, oy + ry * s)

    # Outline of the cross (the cut line), walked as a closed polygon.
    outline = [
        (1, 0), (2, 0), (2, 2), (3, 2), (3, 3), (2, 3),
        (2, 4), (1, 4), (1, 3), (0, 3), (0, 2), (1, 2),
    ]
    c.setStrokeColorRGB(*CUT)
    c.setLineWidth(1.1)
    c.setDash()  # solid
    path = c.beginPath()
    path.moveTo(*pt(*outline[0]))
    for cx, ry in outline[1:]:
        path.lineTo(*pt(cx, ry))
    path.close()
    c.drawPath(path, stroke=1, fill=0)

    # Internal fold lines (dashed).
    folds = [
        ((1, 1), (2, 1)),
        ((1, 2), (2, 2)),
        ((1, 3), (2, 3)),
        ((1, 2), (1, 3)),
        ((2, 2), (2, 3)),
    ]
    c.setStrokeColorRGB(*FOLD)
    c.setLineWidth(0.7)
    c.setDash(3, 2)
    for a, b in folds:
        c.line(*pt(*a), *pt(*b))
    c.setDash()

    # Label the center square.
    c.setFillColorRGB(*FOLD)
    c.setFont("Helvetica", 7)
    c.drawCentredString(ox + 1.5 * s, oy + 2.5 * s - 3, "%d mm" % CUBE)
    c.setFillColorRGB(0, 0, 0)


def cube_pages(c):
    """Two pages, four cube nets each: eight cubes in all."""
    page_w, page_h = letter
    # Net bounding box is 3 x 4 cells; leave room around each.
    cols, rows = 2, 2
    cell_w = 3 * CUBE * mm
    cell_h = 4 * CUBE * mm
    gap_x = (page_w - cols * cell_w) / (cols + 1)
    gap_y = (page_h - 90 - rows * cell_h) / (rows + 1)

    for page in range(2):
        c.setFont("Helvetica-Bold", 13)
        c.drawString(20 * mm, page_h - 22 * mm, "Mini-palletizer cubes")
        c.setFont("Helvetica", 9)
        c.drawString(
            20 * mm, page_h - 30 * mm,
            "Print at 100%%. Cut the solid outline, fold the dashed lines, "
            "tape the edges into a %d mm cube. (Page %d of 2, four cubes.)" % (CUBE, page + 1),
        )
        for r in range(rows):
            for col in range(cols):
                ox = gap_x + col * (cell_w + gap_x)
                oy = gap_y + r * (cell_h + gap_y)
                draw_cube_net(c, ox, oy)
        c.showPage()


def pallet_page(c):
    """One pallet mat: 2x2 grid at 30 mm pitch plus a staging square."""
    page_w, page_h = letter
    s = CUBE * mm
    half = s / 2

    # Map mat-local mm coordinates to page points. Origin placed so the whole
    # layout (staging to the left of the grid) sits centered on the page.
    base_x = 118 * mm
    base_y = 150 * mm

    def mat(mx, my):
        return (base_x + mx * mm, base_y + my * mm)

    def square(mx, my, label=None):
        cx, cy = mat(mx, my)
        c.setStrokeColorRGB(*CUT)
        c.setLineWidth(1.1)
        c.rect(cx - half, cy - half, s, s, stroke=1, fill=0)
        if label:
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0, 0, 0)
            c.drawCentredString(cx, cy - half - 11, label)

    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, page_h - 22 * mm, "Mini-palletizer pallet mat")
    c.setFont("Helvetica", 9)
    c.drawString(
        20 * mm, page_h - 30 * mm,
        "Print at 100%. Place under the arm and align the x and y arrows with the arm's axes.",
    )
    c.drawString(
        20 * mm, page_h - 36 * mm,
        "In Phase 3, teach the arm the staging square and the origin square.",
    )

    # Four pallet cells at (0,0), (0,PITCH), (PITCH,0), (PITCH,PITCH). Only the
    # origin is labelled; the arm computes the other three from it.
    for mx, my in [(0, 0), (PITCH, 0), (0, PITCH), (PITCH, PITCH)]:
        square(mx, my)
    square(0, 0, "origin")

    # Mark the origin corner with a filled dot.
    ox, oy = mat(0, 0)
    c.setFillColorRGB(*CUT)
    c.circle(ox, oy, 1.6 * mm, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)

    # Axis arrows from the origin: +x toward the far cells, +y across.
    c.setStrokeColorRGB(*CUT)
    c.setFillColorRGB(*CUT)
    c.setLineWidth(0.9)
    c.setFont("Helvetica-Oblique", 9)

    def arrow(mx0, my0, mx1, my1, label):
        x0, y0 = mat(mx0, my0)
        x1, y1 = mat(mx1, my1)
        c.line(x0, y0, x1, y1)
        # small arrowhead
        if x1 == x0:  # vertical
            c.line(x1, y1, x1 - 2, y1 - 3 if y1 > y0 else y1 + 3)
            c.line(x1, y1, x1 + 2, y1 - 3 if y1 > y0 else y1 + 3)
        else:  # horizontal
            c.line(x1, y1, x1 - 3 if x1 > x0 else x1 + 3, y1 - 2)
            c.line(x1, y1, x1 - 3 if x1 > x0 else x1 + 3, y1 + 2)
        c.drawString(x1 + 3, y1 - 3, label)

    arrow(PITCH + 16, 0, PITCH + 26, 0, "x")
    arrow(0, PITCH + 16, 0, PITCH + 26, "y")

    # Pitch dimension line between two adjacent cell centers.
    ax, ay = mat(0, -16)
    bx, by = mat(PITCH, -16)
    c.setStrokeColorRGB(*FOLD)
    c.setLineWidth(0.7)
    c.line(ax, ay, bx, by)
    c.line(ax, ay - 4, ax, ay + 4)
    c.line(bx, by - 4, bx, by + 4)
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*FOLD)
    c.drawCentredString((ax + bx) / 2, ay - 10, "PITCH 30 mm")
    c.setFillColorRGB(0, 0, 0)

    # Staging square, as a separate cut-out well clear of the mat. It is taught
    # as its own anchor, so it goes wherever the arm reaches comfortably --
    # printing it at a fixed offset from the grid would imply a layout the code
    # never assumes.
    sx, sy = page_w / 2, 70 * mm
    c.setStrokeColorRGB(*CUT)
    c.setLineWidth(1.1)
    c.setDash(4, 3)
    c.rect(sx - 22 * mm, sy - 20 * mm, 44 * mm, 40 * mm, stroke=1, fill=0)
    c.setDash()
    c.rect(sx - half, sy - half + 3 * mm, s, s, stroke=1, fill=0)
    c.setFont("Helvetica", 8)
    c.drawCentredString(sx, sy - half - 8, "staging")
    c.setFillColorRGB(*FOLD)
    c.drawCentredString(sx, sy - 17 * mm, "cut out and place anywhere the arm reaches")
    c.setFillColorRGB(0, 0, 0)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*FOLD)
    c.drawString(
        20 * mm, 40 * mm,
        "Cells and the staging spot are %d mm squares; one cube footprint each." % CUBE,
    )
    c.setFillColorRGB(0, 0, 0)
    c.showPage()


def main():
    c = canvas.Canvas(OUT, pagesize=letter)
    c.setTitle("Mini-palletizer cube and pallet template")
    cube_pages(c)
    pallet_page(c)
    c.save()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
