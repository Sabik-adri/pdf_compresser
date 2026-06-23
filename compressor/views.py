import os
import mimetypes
from pathlib import Path

from django.shortcuts import render
from django.http import JsonResponse, FileResponse, Http404, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings

from .compressor import (
    compress_pdf_async,
    get_job,
    save_upload,
    output_path_for,
)


def index(request):
    return render(request, 'compressor/index.html', {
        'quality_levels': list(settings.GS_QUALITY_LEVELS.keys()),
        'target_mb': settings.TARGET_SIZE_MB,
    })


@require_POST
def compress_pdf(request):
    uploaded = request.FILES.get('pdf_file')
    if not uploaded:
        return HttpResponseBadRequest('No file uploaded.')
    if not uploaded.name.lower().endswith('.pdf'):
        return HttpResponseBadRequest('Only PDF files are accepted.')

    quality = request.POST.get('quality', 'ebook')
    if quality not in settings.GS_QUALITY_LEVELS:
        quality = 'ebook'

    input_path, job_id, original_name = save_upload(uploaded)
    output_path = output_path_for(job_id, original_name)

    compress_pdf_async(input_path, output_path, quality, job_id)

    return JsonResponse({'job_id': job_id, 'original_name': original_name})


@require_GET
def compression_progress(request, job_id):
    job = get_job(job_id)
    if not job:
        return JsonResponse({'status': 'pending', 'progress': 0, 'message': 'Queued...'})
    return JsonResponse(job)


def download_file(request, filename):
    compressed_dir = Path(settings.MEDIA_ROOT) / 'compressed'
    file_path = compressed_dir / filename

    # Security: only serve files within the compressed directory
    try:
        file_path.resolve().relative_to(compressed_dir.resolve())
    except ValueError:
        raise Http404

    if not file_path.exists():
        raise Http404

    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=filename,
    )
    return response
