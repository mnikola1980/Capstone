"""Procedurally generate a realistic rainbow-spaghetti-on-a-plate 3D object (GLB)."""
import os

import numpy as np
import trimesh
from trimesh.creation import revolve, sweep_polygon
from shapely.geometry import Point

np.random.seed(7)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO_ROOT, "assets", "models", "spaghetti_bowl.glb")

# ---------------------------------------------------------------------------
# Plate: solid of revolution (dinner plate with foot ring, wall, rim, well)
# profile is (radius, height) in meters, traced counterclockwise so the
# revolved solid has outward-facing normals.
# ---------------------------------------------------------------------------
plate_profile = np.array([
    (0.000, 0.000),  # center of underside (foot)
    (0.100, 0.000),  # flat underside out to foot ring
    (0.106, 0.005),  # foot ring outer edge, stepping up
    (0.098, 0.007),  # foot ring inner recess
    (0.128, 0.009),  # underside sloping out to plate body
    (0.148, 0.019),  # rising outer wall up to the rim
    (0.150, 0.022),  # outer lip, top edge
    (0.141, 0.021),  # rim top surface, sloping slightly inward
    (0.116, 0.015),  # inner rim wall sloping down into the well
    (0.060, 0.011),  # well floor sloping toward center
    (0.000, 0.010),  # center of the well (top surface, closes the loop)
])
plate = revolve(plate_profile, sections=96)
plate.fix_normals()
plate.visual = trimesh.visual.TextureVisuals(
    material=trimesh.visual.material.PBRMaterial(
        baseColorFactor=[0.94, 0.90, 0.80, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.45,
        name="plate_ceramic",
    )
)
PLATE_TOP_Z = 0.010  # height of the well floor, where the mound sits

# ---------------------------------------------------------------------------
# Spaghetti strands: each strand is a tube (circular cross-section) swept
# along a coiled 3D path, built to pile up into a rounded, twirled mound
# sitting in the plate's well - similar to a nest of twirled spaghetti.
# ---------------------------------------------------------------------------
PALETTE = [
    (0.70, 0.14, 0.06),  # tomato red
    (0.82, 0.38, 0.04),  # mustard / carrot orange
    (0.33, 0.40, 0.10),  # olive / herb green
    (0.83, 0.55, 0.12),  # golden semolina
]

def turbulence(t, n_terms, amp, freq_range, phase_seed):
    """Sum of random sine waves -- irregular, non-repeating wobble."""
    rng = np.random.RandomState(phase_seed)
    out = np.zeros_like(t)
    for _ in range(n_terms):
        f = rng.uniform(*freq_range)
        p = rng.uniform(0, 2 * np.pi)
        a = rng.uniform(0.4, 1.0)
        out += a * np.sin(2 * np.pi * f * t + p)
    return amp * out / n_terms * 2.2

def make_strand(center_xy, radius, n_loops, height, lift, twist_phase,
                 noodle_r, seed, n_pts=170):
    """Build one tangled noodle path + matching tube mesh.

    Rather than a clean helix, the path is an envelope (a loose loop that
    rises out of the plate and settles back down) perturbed by several
    layers of irregular sine-sum turbulence, so strands read as tangled
    cooked pasta rather than coiled wire.
    """
    t = np.linspace(0.0, 1.0, n_pts)
    rng = np.random.RandomState(seed)

    # taper: zero at both ends (strand rests on the plate there), maximal
    # in the middle -- keeps turbulence from flinging strand ends out of
    # the mound silhouette
    taper = np.sin(np.pi * t) ** 0.5

    # slow envelope: rises from the plate, sweeps around, settles back down
    rad_env = radius * (0.30 + 0.70 * np.sin(np.pi * t) ** 0.55)
    theta = twist_phase + 2 * np.pi * n_loops * t

    # irregular wobble layered on top -- low + mid frequency turbulence,
    # tapered so it fades out near the strand ends
    rad = rad_env + taper * (turbulence(t, 3, radius * 0.30, (1.2, 4.5), seed)
                              + turbulence(t, 3, radius * 0.12, (5.0, 11.0), seed + 1))
    rad = np.clip(rad, radius * 0.08, radius * 1.05)
    theta = theta + taper * turbulence(t, 3, 0.7, (1.0, 3.5), seed + 2)

    x = center_xy[0] + rad * np.cos(theta)
    y = center_xy[1] + rad * np.sin(theta)

    z_env = PLATE_TOP_Z + lift + height * np.sin(np.pi * t) ** 0.7
    z = z_env + taper * (turbulence(t, 3, height * 0.18, (1.5, 5.0), seed + 3)
                          + turbulence(t, 3, height * 0.07, (6.0, 13.0), seed + 4))
    z = np.clip(z, PLATE_TOP_Z + 0.001, PLATE_TOP_Z + lift + height * 1.15)

    path = np.column_stack([x, y, z])
    path = trimesh.path.simplify.resample_spline(path, smooth=0.00035, count=n_pts)

    circle = Point(0, 0).buffer(noodle_r, quad_segs=8)
    tube = sweep_polygon(circle, path)
    return tube

strand_meshes = []
N_STRANDS = 78
for i in range(N_STRANDS):
    layer = i / N_STRANDS  # 0 = inner/top strands, 1 = outer/base strands
    center_xy = np.random.normal(0, 0.008, 2) * (1 - layer)
    radius = 0.020 + 0.075 * layer ** 0.8 + np.random.uniform(-0.005, 0.005)
    n_loops = np.random.uniform(2.6, 4.6)
    height = 0.125 * (1 - 0.55 * layer ** 1.3) + np.random.uniform(-0.007, 0.007)
    lift = 0.006 + 0.004 * (1 - layer)
    twist_phase = np.random.uniform(0, 2 * np.pi)
    noodle_r = np.random.uniform(0.0016, 0.0020)

    tube = make_strand(center_xy, radius, n_loops, height, lift, twist_phase,
                        noodle_r, seed=i * 17 + 3)

    base = PALETTE[i % len(PALETTE)] if i % 5 else PALETTE[np.random.randint(len(PALETTE))]
    base = np.array(base) + np.random.uniform(-0.04, 0.04, 3)
    base = np.clip(base, 0, 1)
    color = np.clip(base + np.random.uniform(-0.02, 0.02, 3), 0, 1)

    tube.visual = trimesh.visual.TextureVisuals(
        material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=[*color, 1.0],
            metallicFactor=0.0,
            roughnessFactor=float(np.random.uniform(0.28, 0.42)),
            name=f"noodle_{i}",
        )
    )
    strand_meshes.append(tube)

# ---------------------------------------------------------------------------
# Assemble scene and export
# ---------------------------------------------------------------------------
scene = trimesh.Scene()
scene.add_geometry(plate, node_name="plate")
for i, m in enumerate(strand_meshes):
    scene.add_geometry(m, node_name=f"noodle_{i:03d}")

# trimesh builds/exports geometry as authored (Z-up here) but does not
# rotate it for glTF's Y-up convention on export -- do that ourselves so
# Y-up viewers (model-viewer, three.js, etc.) show the plate flat and the
# noodles piled upward instead of sideways.
scene.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
scene.export(OUT)

verts = sum(len(m.vertices) for m in strand_meshes) + len(plate.vertices)
faces = sum(len(m.faces) for m in strand_meshes) + len(plate.faces)
print(f"Exported {OUT}")
print(f"strands={len(strand_meshes)} total_verts={verts} total_faces={faces}")
print(f"bounds={scene.bounds.tolist()}")
