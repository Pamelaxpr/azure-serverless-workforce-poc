import pyotp


def verify_totp(secret_key: str, code: str, window: int = 1) -> bool:
    """
    Valida si el código TOTP provisto es válido para la clave secreta dada.
    
    :param secret_key: Clave secreta Base32 asignada al empleado/terminal.
    :param code: Código de 6 dígitos a verificar.
    :param window: Tolerancia temporal (1 = ±30 segundos).
    :return: True si el código es válido, False en caso contrario.
    """
    totp = pyotp.TOTP(secret_key)
    return totp.verify(code, valid_window=window)