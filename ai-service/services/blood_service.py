"""Bounded, optional research segmentation with separately installed TensorFlow."""
import base64
import hashlib
import io
import json
import os
import subprocess
import warnings
from functools import lru_cache
from pathlib import Path
from threading import Lock

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from config import ROOT, root_path

SOURCE_URL = 'https://github.com/abhanjac/blood_cell_image_segmentation'
REVISION = '8d32c82c8d2847ed38e8408e5ee7fdd7c6ca9bcb'
MAX_BLOOD_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MIN_IMAGE_SIDE = 32
MODEL_SIDE = 224
WORKER = Path(__file__).with_name('blood_worker.py')
CHECKPOINT_HASHES = {
    '.meta': '9e99cbf424c4601cb61bb692bf5753d53073056430de242b11cfd7064094be1f',
    '.index': '054dde82df3c8c1151dc66543e0b83dc4b56a5f74089b3f1d13c6303e8dc7298',
    '.data-00000-of-00001': '3b0bfb985587cf38966c4f8440503f5cb3c183731c8732ede808e13881cd24a4',
}
CLASSES = (
    ('eosinophil', 'Eosinophil', '#00ffff'),
    ('basophil', 'Basophil', '#008080'),
    ('neutrophil', 'Neutrophil', '#fabebe'),
    ('lymphocyte', 'Lymphocyte', '#808000'),
    ('monocyte', 'Monocyte', '#000080'),
    ('partial_wbc', 'Partial white blood cell', '#0000ff'),
    ('platelet', 'Platelet', '#ffe100'),
    ('platelet_clump', 'Platelet clump', '#ff00ff'),
    ('rbc_class_a', 'RBC training class A (upstream: Infected)', '#ff0000'),
    ('rbc_class_b', 'RBC training class B (upstream: Healthy RBC)', '#00ff00'),
    ('background', 'Background', '#000000'),
)
WARNING = (
    'General awareness only, not a substitute for a doctor\'s advice. '
    'Experimental research segmentation: colors and percentages describe pixels in this image, '
    'not blood cell counts, CBC values, or a diagnosis. The upstream Infected and Healthy RBC '
    'training labels cannot establish infection, malaria, or health. A qualified laboratory '
    'professional must review the original blood-smear image.'
)
WARNING_HI = (
    'केवल सामान्य जागरूकता के लिए, डॉक्टर की सलाह का विकल्प नहीं। '
    'यह प्रायोगिक शोध विभाजन है: रंग और प्रतिशत इस चित्र के पिक्सेल बताते हैं, रक्त कोशिकाओं की संख्या, '
    'CBC मान या निदान नहीं। मूल मॉडल के Infected और Healthy RBC प्रशिक्षण नाम संक्रमण, मलेरिया '
    'या स्वस्थ होने की पुष्टि नहीं करते। योग्य प्रयोगशाला विशेषज्ञ को मूल रक्त-स्मियर चित्र की समीक्षा करनी चाहिए।'
)
_runtime_lock = Lock()


class BloodModelUnavailable(RuntimeError):
    def __init__(self, message='Blood-smear analysis is unavailable. Check the optional local model setup and try again.', code='blood_model_unavailable', status=503):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(message)


class BloodImageError(ValueError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def checkpoint_path():
    return root_path('BLOOD_CHECKPOINT', '.local-data/blood-cell-segmentation/codes/saved_models/tiny_yolo_ckpt-35')


def runtime_python():
    default = '.local-data/blood-runtime/Scripts/python.exe' if os.name == 'nt' else '.local-data/blood-runtime/bin/python'
    return root_path('BLOOD_PYTHON', default)


def _fingerprint(path):
    stat = path.stat()
    return str(path.resolve()), stat.st_size, stat.st_mtime_ns


@lru_cache(maxsize=16)
def _verified_checkpoint(fingerprints):
    for (path, _, _), expected in zip(fingerprints, CHECKPOINT_HASHES.values()):
        digest = hashlib.sha256()
        with open(path, 'rb') as stream:
            while block := stream.read(1024 * 1024):
                digest.update(block)
        if digest.hexdigest() != expected:
            return False
    return True


def _configuration():
    checkpoint = checkpoint_path()
    try:
        fingerprints = tuple(_fingerprint(Path(str(checkpoint) + suffix)) for suffix in CHECKPOINT_HASHES)
    except OSError:
        return None, 'checkpoint_missing', 'The optional blood-smear model is not installed. Complete the Blood Guide model setup.'
    try:
        if not _verified_checkpoint(fingerprints):
            return None, 'checkpoint_integrity_failed', 'The blood-smear checkpoint does not match the verified upstream version. Reinstall the pinned model.'
    except OSError:
        return None, 'checkpoint_missing', 'The blood-smear checkpoint could not be read. Complete the model setup.'
    python = runtime_python()
    if not python.is_file() or not os.access(python, os.X_OK):
        return None, 'runtime_missing', 'The optional blood-smear analysis runtime is not installed. Complete the Blood Guide model setup.'
    return (python, checkpoint, fingerprints), None, None


def _run_worker(mode, python, checkpoint, payload=None, image_size=None):
    if not _runtime_lock.acquire(timeout=1):
        raise BloodModelUnavailable('Blood-smear analysis is busy. Please try again in a moment.')
    try:
        env = os.environ.copy()
        env['TF_CPP_MIN_LOG_LEVEL'] = '3'
        arguments = [str(python), str(WORKER), mode, str(checkpoint)]
        if image_size:
            arguments.extend(str(value) for value in image_size)
        result = subprocess.run(
            arguments, input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
            cwd=str(ROOT), env=env, check=False,
        )
        if result.returncode:
            raise BloodModelUnavailable()
        return result.stdout
    except subprocess.TimeoutExpired as error:
        raise BloodModelUnavailable('Blood-smear analysis took too long. Please try again with a clear microscope image.', 'blood_model_timeout', 504) from error
    except OSError as error:
        raise BloodModelUnavailable() from error
    finally:
        _runtime_lock.release()


@lru_cache(maxsize=4)
def _probe_runtime(python, python_fingerprint, fingerprints, checkpoint):
    output = _run_worker('status', Path(python), Path(checkpoint))
    try:
        info = json.loads(output)
    except (ValueError, TypeError) as error:
        raise BloodModelUnavailable() from error
    if info.get('ready') is not True:
        raise BloodModelUnavailable()
    return info


def model_status():
    status = {'ready': False, 'source_url': SOURCE_URL, 'revision': REVISION, 'input_size': [MODEL_SIDE, MODEL_SIDE]}
    configuration, code, message = _configuration()
    if not configuration:
        return {**status, 'code': code, 'message': message}
    python, checkpoint, fingerprints = configuration
    try:
        info = _probe_runtime(str(python), _fingerprint(python), fingerprints, str(checkpoint))
        return {**status, **info, 'ready': True, 'code': 'ready', 'message': 'The experimental blood-smear segmentation model is ready.'}
    except (BloodModelUnavailable, OSError):
        return {**status, 'code': 'blood_model_unavailable', 'message': 'The optional blood-smear model could not be loaded. Check the local model setup.'}


def decode_image(payload):
    if not payload:
        raise BloodImageError(400, 'The uploaded image is empty.')
    if len(payload) > MAX_BLOOD_UPLOAD_BYTES:
        raise BloodImageError(413, 'Blood-smear images must be 5 MB or smaller.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(payload)) as source:
                if source.format not in {'PNG', 'JPEG'}:
                    raise BloodImageError(415, 'Only PNG and JPEG blood-smear images are supported.')
                width, height = source.size
                if width * height > MAX_IMAGE_PIXELS or max(width, height) > 8192:
                    raise BloodImageError(413, 'Image dimensions are too large. Use a microscope image up to 16 megapixels and 8192 pixels per side.')
                if min(width, height) < MIN_IMAGE_SIDE:
                    raise BloodImageError(422, 'The blood-smear image must be at least 32 pixels on each side.')
                if getattr(source, 'n_frames', 1) != 1:
                    raise BloodImageError(415, 'Use a single-frame PNG or JPEG blood-smear image.')
                source.load()
                return ImageOps.exif_transpose(source).convert('RGB')
    except BloodImageError:
        raise
    except (Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise BloodImageError(413, 'Image dimensions are too large.') from error
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise BloodImageError(415, 'The uploaded file is not a valid PNG or JPEG image.') from error


def _infer_probabilities(image, configuration):
    python, checkpoint, _ = configuration
    # The isolated OpenCV worker resizes a clean RGB decode with INTER_LINEAR,
    # reverses to upstream BGR order and applies the checkpoint normalization.
    output = _run_worker('infer', python, checkpoint, image.tobytes(), image.size)
    try:
        probabilities = np.load(io.BytesIO(output), allow_pickle=False)
    except (ValueError, OSError, EOFError) as error:
        raise BloodModelUnavailable() from error
    if (not isinstance(probabilities, np.ndarray) or probabilities.dtype.kind != 'f'
            or probabilities.shape != (MODEL_SIDE, MODEL_SIDE, len(CLASSES))
            or not np.isfinite(probabilities).all()
            or np.any(probabilities < 0) or np.any(probabilities > 1)
            or not np.allclose(probabilities.sum(axis=-1), 1, atol=0.001)):
        raise BloodModelUnavailable('Blood-smear analysis returned an invalid model result. Please try again.', 'blood_model_failed', 502)
    return probabilities


def _png_data(image):
    output = io.BytesIO()
    image.save(output, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii')


def render_result(image, probabilities):
    confidence = probabilities.max(axis=-1)
    predicted = probabilities.argmax(axis=-1)
    confident = confidence > 0.5
    palette = np.array([tuple(bytes.fromhex(color[1:])) for _, _, color in CLASSES], dtype=np.uint8)
    segmentation = palette[predicted]
    segmentation[~confident] = 0
    segmentation_image = Image.fromarray(segmentation)
    # Keep responses bounded even when a large microscope image is uploaded.
    display = image.copy()
    display.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    labels = segmentation_image.resize(display.size, Image.Resampling.NEAREST)
    foreground = Image.fromarray(np.asarray(confident & (predicted != 10), dtype=np.uint8) * 112).resize(display.size, Image.Resampling.NEAREST)
    overlay = Image.composite(labels, display, foreground)
    area = MODEL_SIDE * MODEL_SIDE
    classes = []
    for index, (key, name, color) in enumerate(CLASSES):
        count = int(np.count_nonzero(confident & (predicted == index)))
        classes.append({'key': key, 'name': name, 'color': color, 'pixel_count': count, 'pixel_percent': round(100 * count / area, 2)})
    return {
        'mode': 'model', 'width': image.width, 'height': image.height,
        'analyzed_width': MODEL_SIDE, 'analyzed_height': MODEL_SIDE,
        'overlay_image': _png_data(overlay), 'segmentation_image': _png_data(segmentation_image),
        'classes': classes, 'uncertain_pixel_percent': round(100 * np.count_nonzero(~confident) / area, 2),
        'warning': WARNING, 'warning_hi': WARNING_HI,
        'source': {'url': SOURCE_URL, 'revision': REVISION, 'checkpoint': 'tiny_yolo_ckpt-35', 'framework': 'TensorFlow compatibility graph'},
    }


def analyze_image(payload):
    image = decode_image(payload)
    configuration, _, message = _configuration()
    if not configuration:
        raise BloodModelUnavailable(message)
    return render_result(image, _infer_probabilities(image, configuration))
