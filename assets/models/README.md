# Spaghetti Bowl — 3D Object

A procedurally generated, realistic rainbow-spaghetti-on-a-plate 3D object.

- `spaghetti_bowl.glb` — the object itself: a ceramic plate plus ~78
  individually colored, tangled noodle strands (swept tube geometry) piled
  into a rounded nest, matching the reference photo. Real-world scale
  (30 cm plate). glTF 2.0 binary, PBR materials, ready to drop into
  Three.js, Unity, Blender, Godot, or any glTF-compatible pipeline.
- `index.html` + `model-viewer.min.js` — a standalone, offline interactive
  viewer (`@google/model-viewer`, vendored locally). Serve this directory
  over HTTP and open `index.html` to drag-orbit, zoom, and view the object
  in AR on supported devices.

## Regenerating

The model is built procedurally by `scripts/generate_spaghetti_bowl.py`
(repo root). Install `scripts/requirements.txt`, then run:

```
python3 scripts/generate_spaghetti_bowl.py
```

Strand paths use tapered multi-octave sine-sum turbulence confined to a
domed envelope, so tweaking the random seed or the per-strand `radius`
/`height` formulas produces a different but similarly shaped tangle.

Note for anyone editing the generator: trimesh's glTF exporter does **not**
convert Z-up authoring space to glTF's required Y-up convention, so a
`-90°` rotation about X must be applied to the scene right before export
— otherwise Y-up viewers render the plate on its side.
