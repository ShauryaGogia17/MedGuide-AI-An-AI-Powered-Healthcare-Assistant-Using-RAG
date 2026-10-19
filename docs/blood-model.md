# Blood Guide microscope-image model

Blood Guide uses the trained modified U-Net checkpoint from [abhanjac/blood_cell_image_segmentation](https://github.com/abhanjac/blood_cell_image_segmentation), pinned to commit `8d32c82c8d2847ed38e8408e5ee7fdd7c6ca9bcb` (2022-02-24). It is an optional research feature. Saved-report guidance and the rest of MedGuide continue to work when the model runtime is unavailable.

Run from the project root after the normal MedGuide setup:

```sh
python3 scripts/setup_blood_model.py
```

The script downloads the pinned upstream checkout to ignored `.local-data/blood-cell-segmentation`, verifies the supplied checkpoint, creates ignored `.local-data/blood-runtime`, installs official TensorFlow 2.21.0 and headless OpenCV 4.13.0.92 there, and tests actual graph inference. It does not run/import upstream Python scripts or modify `ai-service/.venv` and its dependencies. Git, network access and a compatible Python interpreter are required; no hosted paid service or API key is used.

This implementation was verified with Python 3.13 on macOS arm64. [TensorFlow's installation documentation](https://www.tensorflow.org/install/pip#package_location) lists current Python/platform wheels. To choose an installed compatible interpreter when creating the optional runtime, use `python3 scripts/setup_blood_model.py --python /absolute/path/to/python`. The existing optional runtime is preserved if present.

For a separately provisioned deployment, configure:

```dotenv
BLOOD_PYTHON=/absolute/path/to/isolated/venv/bin/python
BLOOD_CHECKPOINT=/absolute/path/to/codes/saved_models/tiny_yolo_ckpt-35
```

On Windows the runtime interpreter is `Scripts/python.exe`. The checkpoint configuration is a prefix without a file extension. Required `.meta`, `.index`, and `.data-00000-of-00001` hashes must match this pinned version; a different model is intentionally rejected. These paths are server configuration, never accepted from a user upload.

The backend forwards authenticated requests to FastAPI `GET /blood/status` and multipart `POST /blood/analyze`. Both use the existing gateway-secret and user-context checks. Images/results are not persisted in report storage or sent to an external provider. Multipart parsing may use a temporary file which is closed/deleted after the request; validation and inference then operate in memory. Uploads are restricted to single-frame PNG/JPEG up to 5 MB, and must have 32 pixels per side or more, at most 16 megapixels, and at most 8192 pixels per side. The main service validates and decodes with Pillow, corrects EXIF orientation, and sends clean RGB bytes and validated dimensions to the isolated worker. The worker converts to OpenCV BGR, resizes with `INTER_LINEAR` to 224 by 224, and normalizes with `float32(image) / 127.5 - 1.0`. The original upstream inference expects already-resized 224 by 224 inputs; the adapter adds bounded resizing for other uploaded dimensions. The checkpoint is restored through `tf.compat.v1`, rather than legacy `tf.layers` source code. The feature makes no external AI-provider calls: Hindi text is authored, and image analysis uses the local checkpoint.

## Reading the output

The supplied graph has **11 channels**, including partial WBC and background; the README's 10-class list is older than this checkpoint. Pixels count towards a class only when its predicted probability is strictly greater than 0.5. Other pixels are reported as uncertain and shown in black on the segmentation map. Overlay previews are at most 1024 by 1024; the segmentation and all coverage statistics refer to the 224 by 224 analyzed image.

Class pixel counts and percentages describe colored regions **in this uploaded image**. They are not cell counts, CBC measurements, blood concentrations, or a diagnosis. The RBC classes retain the upstream names `Infected` and `Healthy RBC` only for provenance, displayed as research training classes A and B. A model class cannot establish infection, malaria, or health. The UI includes English/Hindi warnings and requires laboratory review of the original smear.

The upstream dataset was synthesized to resemble 40x microscope views. Uploaded reports, ordinary photographs, other magnifications/stains, and clinical use are outside the demonstrated training conditions. The upstream README reports a research pixel accuracy of 93.48%; MedGuide does not present that as clinical accuracy. The repository's `trial/segments` files are ground-truth labels, never used as new inference results.

## Upstream provenance and distribution

The upstream repository supplies the trained weights directly in Git. It does not include a LICENSE file or explicit license text at the pinned revision. MedGuide's tracked code contains an independently written adapter and attribution; upstream source, sample images and weights remain in the separate ignored checkout. Establish permission before redistributing or publishing upstream files. The setup retains the original upstream checkout and never runs its training/test scripts.

Checkpoint 35 SHA-256 values verified before loading:

- `.meta`: `9e99cbf424c4601cb61bb692bf5753d53073056430de242b11cfd7064094be1f`
- `.index`: `054dde82df3c8c1151dc66543e0b83dc4b56a5f74089b3f1d13c6303e8dc7298`
- `.data-00000-of-00001`: `3b0bfb985587cf38966c4f8440503f5cb3c183731c8732ede808e13881cd24a4`

Fast deterministic tests use generated images and synthetic probability arrays to verify upload/authentication boundaries, channel order, threshold/color/class mapping, and model error behavior. A real inference smoke test is available after optional setup:

```sh
MEDGUIDE_BLOOD_INTEGRATION=1 ai-service/.venv/bin/python -m pytest tests/blood -q
```

The optional smoke test reads the original ignored upstream sample and compares a fresh prediction against its supplied ground truth. It does not copy sample assets into MedGuide's tracked source or equate the test with clinical validation.
