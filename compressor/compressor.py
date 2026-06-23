import os
import subprocess
import shutil
import uuid
import threading
from pathlib import Path
from django.conf import settings

# Thread-safe job status store
_jobs = {}
_jobs_lock = threading.Lock()


def get_job(job_id):
    with _jobs_lock:
        return _jobs.get(job_id, {}).copy()


def _set_job(job_id, data):
    with _jobs_lock:
        _jobs[job_id] = data


def compress_pdf_async(input_path, output_path, quality, job_id):
    thread = threading.Thread(
        target=_run_compression,
        args=(input_path, output_path, quality, job_id),
        daemon=True,
    )
    thread.start()


def _run_compression(input_path, output_path, quality, job_id):
    _set_job(job_id, {'status': 'running', 'progress': 5, 'message': 'Starting compression...'})

    gs_setting = settings.GS_QUALITY_LEVELS.get(quality, '/ebook')
    input_size = os.path.getsize(input_path)

    try:
        _set_job(job_id, {'status': 'running', 'progress': 20, 'message': 'Compressing with Ghostscript...'})

        cmd = [
            'gs',
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            f'-dPDFSETTINGS={gs_setting}',
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            # Keep all content — no page removal
            '-dDetectDuplicateImages=true',
            '-dCompressFonts=true',
            '-dSubsetFonts=true',
            '-dEmbedAllFonts=true',
            f'-sOutputFile={output_path}',
            str(input_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(f'Ghostscript error: {result.stderr}')

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError('Ghostscript produced an empty output file.')

        output_size = os.path.getsize(output_path)
        target_bytes = settings.TARGET_SIZE_MB * 1024 * 1024

        # If still over 350 MB, try progressively more aggressive settings
        if output_size > target_bytes:
            _set_job(job_id, {
                'status': 'running',
                'progress': 60,
                'message': f'Still {_fmt(output_size)} — trying more aggressive compression...',
            })
            output_size = _try_aggressive(input_path, output_path, output_size, target_bytes, job_id)

        ratio = round((1 - output_size / input_size) * 100, 1) if input_size > 0 else 0

        _set_job(job_id, {
            'status': 'done',
            'progress': 100,
            'message': 'Compression complete.',
            'input_size': input_size,
            'output_size': output_size,
            'ratio': ratio,
            'filename': Path(output_path).name,
            'under_350mb': output_size <= target_bytes,
        })

    except Exception as exc:
        _set_job(job_id, {
            'status': 'error',
            'progress': 0,
            'message': str(exc),
        })
        if os.path.exists(output_path):
            os.remove(output_path)


def _try_aggressive(input_path, current_output, current_size, target_bytes, job_id):
    """Retry with /screen setting and explicit low-resolution image downsampling."""
    tmp = str(current_output) + '.tmp.pdf'
    cmd = [
        'gs',
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS=/screen',
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        '-dDetectDuplicateImages=true',
        '-dCompressFonts=true',
        '-dSubsetFonts=true',
        '-dEmbedAllFonts=true',
        # Downsample images aggressively (still preserves text/vector content)
        '-dColorImageResolution=100',
        '-dGrayImageResolution=100',
        '-dMonoImageResolution=150',
        '-dDownsampleColorImages=true',
        '-dDownsampleGrayImages=true',
        '-dDownsampleMonoImages=true',
        '-dColorImageDownsampleType=/Bicubic',
        '-dGrayImageDownsampleType=/Bicubic',
        f'-sOutputFile={tmp}',
        str(input_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode == 0 and os.path.exists(tmp):
        tmp_size = os.path.getsize(tmp)
        if tmp_size < current_size:
            os.replace(tmp, current_output)
            return tmp_size
        else:
            os.remove(tmp)
    return current_size


def _fmt(size_bytes):
    mb = size_bytes / (1024 * 1024)
    return f'{mb:.1f} MB'


def make_job_id():
    return uuid.uuid4().hex


def save_upload(uploaded_file):
    upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)
    job_id = make_job_id()
    safe_name = Path(uploaded_file.name).name
    dest = upload_dir / f'{job_id}_{safe_name}'
    with open(dest, 'wb') as f:
        for chunk in uploaded_file.chunks(chunk_size=8 * 1024 * 1024):
            f.write(chunk)
    return str(dest), job_id, safe_name


def output_path_for(job_id, original_name):
    out_dir = Path(settings.MEDIA_ROOT) / 'compressed'
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(original_name).stem
    return str(out_dir / f'{job_id}_compressed_{stem}.pdf')
