"""
Utility functions for the ERP system
"""
import logging
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def html_to_pdf_response(html, filename, content_type='application/pdf'):
    """
    Try WeasyPrint first, then xhtml2pdf (works on Ubuntu without cairo/pango).
    Returns HttpResponse with PDF or HTML fallback.
    """
    from io import BytesIO

    # 1. Try WeasyPrint (best quality, needs system libs on Linux)
    try:
        from weasyprint import HTML as WeasyHTML
        pdf_file = BytesIO()
        WeasyHTML(string=html).write_pdf(pdf_file)
        pdf_file.seek(0)
        response = HttpResponse(pdf_file.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except ImportError:
        pass
    except Exception as e:
        logger.warning("WeasyPrint PDF failed: %s", e)

    # 2. Fallback: xhtml2pdf (pure Python, works on Ubuntu server)
    try:
        from xhtml2pdf import pisa
        result = BytesIO()
        status = pisa.CreatePDF(html, dest=result)
        if not status.err:
            result.seek(0)
            response = HttpResponse(result.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    except ImportError:
        pass
    except Exception as e:
        logger.warning("xhtml2pdf PDF failed: %s", e)

    # 3. Return HTML so user can Print -> Save as PDF
    response = HttpResponse(html, content_type='text/html')
    safe_name = filename.replace('.pdf', '.html')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}"'
    return response


def get_company_info():
    """
    Get company information for use in invoices, reports, and other documents.
    Returns a dictionary with company details.
    
    Returns:
        dict: Dictionary containing company_name, company_address, and company_phone
    """
    return {
        'company_name': 'HAJI IDRIS AND SONS',
        'company_address': 'RISERV PUKUR UTTOR PAR, CHAIRMAN BARI SHAROK, BHANDARIA, PIROJPUR.',
        'company_phone': '01704-822220 | 01401-077666 | 01712-450013',
    }

