"""
Utility functions for the ERP system
"""


def get_company_info():
    """
    Get company information for use in invoices, reports, and other documents.
    Returns a dictionary with company details.
    
    Returns:
        dict: Dictionary containing company_name, company_address, and company_phone
    """
    return {
        'company_name': 'Haji Edris And Sons',
        'company_address': 'Bandareia, Borisal, Country',
        'company_phone':   '01824909309',
    }

