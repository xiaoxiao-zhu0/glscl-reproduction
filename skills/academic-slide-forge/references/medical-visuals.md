# Medical visual evidence (conditional reference)

Read this section only for relevant projects. It is an example of applying the analysis, not the default visual style or pipeline. When screenshots are unwanted, extract clean scientific views directly from project data if available and in scope. Match the visual to the member's actual task, for example:

- **Image loading and spatial consistency:** slice orientation, voxel spacing and affine mapping, shown with appropriate native axes/labels. Use one consistent case and coordinate convention; check image/mask alignment rather than independently resizing them.
- **Segmentation:** a real slice and aligned mask overlay, or a source-grounded comparison of supported processing routes. Attribute pretrained models accurately. Generated anatomy can explain the target, not supply measured performance.
- **Local editing:** the same case, slice, orientation, crop, window and overlay settings before/after, with the changed region visible. For tiny changes, use a magnified inset and actual voxel difference/count. Verify restoration or unchanged regions from recorded evidence; do not illustrate unverified invariance as a result.
- **Handoff:** connect documented outputs to downstream consumers, distinguishing image-to-mask work from mask-to-mesh work and platform UI. Native objects should carry exact file/interface labels.
- **Evaluation:** source-derived metrics, sample selection and limitations; show supported failure cases when useful. Keep organ segmentation and lesion segmentation claims separate.

These are choices, not a mandatory page sequence. Do not hard-code one project's case IDs, voxel counts or metrics into future prompts.

If real scans/masks are unavailable, use a clearly labeled conceptual explanation and available factual records; disclose the missing visual evidence. Do not generate plausible CT scans, synthetic before/after results or physiological simulations and present them as project output. A three-dimensional-looking illustration is not a numerical simulation. Confirm anatomy against a reliable reference and state only the degree of validation performed.

