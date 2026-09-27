# Bills bison family — V3, printability revision

The bull's raised foreleg now ends in a shorter ankle and a distinct faceted hoof, replacing V2's long pointed sweep. The cow and calf retain their poses. Stripe frames, adult horn tips and the calf's tail stem are reinforced; the calf's stripe rails are wider in their own plane as well as thicker.

## Recommended files

For a freestanding display, choose the **integral-base versions** in `STL/optional_with_bases/`. The bull requires a base or attachment to a display surface because its three-hoof stance is not statically stable by itself.

| File | Overall dimensions, mm |
|---|---|
| `01_Bull_integral_display_base.stl` | 212 × 111.6 × 168.6 |
| `02_Cow_integral_display_base.stl` | 168.1 × 87.5 × 134.7 |
| `03_Calf_integral_display_base.stl` | 95.0 × 45.8 × 71.2 |
| `04_Family_on_230mm_oval_display.stl` | 175 × 230 × 107.4 |

The three primary files in `STL/` are unbased, striped animals: 200 mm bull, 158.6 mm cow and 89.7 mm calf, measured along their length. `STL/optional_plain/` contains complete alternatives without the stripe assemblies. The ten files are alternative models, not ten assembly parts.

Import STLs in **millimeters at 100%**, with Z up and the hoof/base bottoms on the bed. The family display uses animals at 62% of the individual sizes; its smaller details need more careful support removal.

## Printing setup used for verification

All ten STLs were sliced individually with **OrcaSlicer 2.4.0**, a 0.4 mm nozzle, Generic PLA, 0.20 mm layers, three walls, 15% infill, automatic tree supports, a 45-degree support threshold, and a 5 mm outer brim. Supports were allowed on both the bed and the model. Automatic geometry changes to make overhangs printable were disabled.

**Supports are required.** In particular, retain support under the raised hoof, belly, beard, horns, ears, tail and the stripe-frame undersides. Remove supports gradually with flush cutters where access is tight; do not pull a support tree against a stripe or horn. Do not downscale these versions without checking and adapting their thin features.

The verification used an Elegoo Centauri Carbon 0.4 mm profile with a 256 × 256 mm bed as a test configuration. **Select your actual printer and filament profiles when slicing.** The pack contains STLs and editable source, not ready-to-run machine G-code. No print was sent to a printer.

The family display's supports/brim use essentially the full width of the 256 mm test bed. Check your printer's usable area and exclusion zones. The individual animals offer more bed margin and larger, easier-to-handle details.

## What has been checked

- All ten exported STLs: closed surfaces, consistent winding, one connected material solid, no enclosed void shells, no degenerate triangles, positive volume, flat bed contact, dimensions and hashes.
- All ten STLs: successful slicing with supports, nonempty layer toolpaths, and valid sliced 3MF archives containing the generated G-code.
- Generated toolpaths: extrusion bounds including a 0.25 mm bead margin within the test bed, plus support beneath the bull's raised hoof. `previews/Bull_sliced_layers.png` shows actual generated model and support paths.
- The bull's unbased center of mass is approximately 4 mm outside its support polygon. The integral bases resolve that geometric balance problem.

These checks establish that the files can be sliced with the stated setup. **They have not been physically test printed.** Surface quality, support release and small-feature durability still depend on the printer, filament and cooling.

## Included

- `source/Bills_Bison_Family.blend`: editable Blender 5.2 scene. No extra library is needed to open it.
- `previews/`: actual mesh renders, leg comparison and sliced-layer review.
- `FINAL_VALIDATION.json`, `SLICE_VALIDATION.json`, `TOOLPATH_REVIEW.json`: measurements and verification results tied to the exported files.
- `slicing_settings/`: the exact local test profiles for reproducibility; select your own printer for production printing.
- `scripts/`: generation and validation source. Rebuilding geometry requires Blender's Python, NumPy and Manifold3D; the vendor search path can be adjusted for another computer. `build_v3.py` builds the models; `finish_and_validate.py` creates bases and validates them. Slicing checks additionally require OrcaSlicer; copy the three test profile JSONs from `slicing_settings/` into a `slicing/` folder before running `slice_check.py`. Toolpath previews require Pillow.

Headless OrcaSlicer reported an OpenGL thumbnail-rendering warning during export. G-code generation and sliced-archive validation completed; the supplied visual previews were rendered separately.

These remain photo-based interpretations of the stadium sculpture; references and artist credit are in REFERENCE_NOTES.md. Previous versions are retained separately. Downloaded reference photographs, large diagnostic G-code/3MF files, logs and backup files are excluded from this ZIP.
