"""
A generic utilities module
"""
def set_return_response(res, status, err_code, 
                        err_msg=None, data=None):
    """
        Generic function to set reponse fields
    """
    res['status'] = status
    res['error_code'] = err_code
    res['error_msg'] = err_msg
    res['data'] = data

