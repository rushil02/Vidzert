class VideoError(Exception):
    """Custom Exception
    Used mainly by celery, to catch expected errors without traceback
    Traceback stored in result backend"""
    pass


class GraphError(Exception):
    """Custom Exception
    Used mainly by celery, to catch expected errors without traceback
    Traceback stored in result backend"""
    pass


class EmailValidationError(Exception):
    """Custom Exception
    Used by forms while validation emails, if email is from domain gmail
    - '.' periods will be removed."""
    pass


class VideoStateError(Exception):
    """Custom Exception
    Used wherever the current video state is fetched"""
    pass


class ForceTerminate(Exception):
    """Custom Exception
    Used wherever the video is force terminated"""
    pass
