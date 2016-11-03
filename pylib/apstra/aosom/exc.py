# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula


# ##### ---------------------------------------------------
# ##### Parent Exception class for everything
# ##### ---------------------------------------------------

class AosCpError(Exception):
    def __init__(self, message=None):
        super(AosCpError, self).__init__(message)


# ##### ---------------------------------------------------
# ##### Login related exceptions
# ##### ---------------------------------------------------

class LoginError(AosCpError):
    def __init__(self, message=None):
        super(LoginError, self).__init__(
            message or 'AOS-server login error')


class LoginNoServerError(LoginError):
    def __init__(self, message=None):
        super(LoginNoServerError, self).__init__(
            message or 'AOS-server value not provided')


class LoginServerUnreachableError(LoginError):
    def __init__(self, message=None):
        super(LoginServerUnreachableError, self).__init__(
            message or 'AOS-server unreachable')


class LoginAuthError(LoginError):
    def __init__(self):
        super(LoginAuthError).__init__()

# ##### ---------------------------------------------------
# ##### Session processing exceptions
# ##### ---------------------------------------------------


class SessionError(AosCpError):
    def __init__(self, message=None):
        super(SessionError, self).__init__(message)


class SessionRqstError(SessionError):
    def __init__(self, resp, message=None):
        self.resp = resp
        super(SessionRqstError, self).__init__(message)


class AccessValueError(SessionError):
    def __init__(self, message=None):
        super(AccessValueError, self).__init__(message)
