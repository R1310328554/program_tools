"""Extra encoding / crypto tools from community catalogs."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import zlib
from typing import Any

import jwt
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets


MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', ' ': '/',
}
MORSE_REV = {v: k for k, v in MORSE.items()}


def hmac_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'sign':
        raise ValueError(f'未知操作: {action}')
    key = (options.get('key') or 'secret').encode('utf-8')
    algo = (options.get('algo') or 'sha256').lower()
    if algo not in hashlib.algorithms_available and algo not in {'md5', 'sha1', 'sha256', 'sha384', 'sha512'}:
        raise ValueError(f'不支持的算法: {algo}')
    digest = hmac.new(key, text.encode('utf-8'), getattr(hashlib, algo)).hexdigest()
    return {'result': digest}


def aes_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    """AES-GCM with key derived/padded from passphrase, or Fernet token mode."""
    mode = (options.get('mode') or 'fernet').lower()
    secret = options.get('key') or 'stackbox-demo-key'

    if mode == 'fernet':
        # Derive a url-safe 32-byte key from passphrase
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode('utf-8')).digest())
        f = Fernet(key)
        if action == 'encrypt':
            token = f.encrypt(text.encode('utf-8')).decode('ascii')
            return {'result': token}
        if action == 'decrypt':
            try:
                return {'result': f.decrypt(text.strip().encode('ascii')).decode('utf-8')}
            except InvalidToken as exc:
                raise ValueError('解密失败：密钥或密文不正确') from exc
        raise ValueError(f'未知操作: {action}')

    # AES-GCM: key = sha256(secret), nonce prepended to ciphertext (b64)
    key = hashlib.sha256(secret.encode('utf-8')).digest()
    aes = AESGCM(key)
    if action == 'encrypt':
        nonce = secrets.token_bytes(12)
        ct = aes.encrypt(nonce, text.encode('utf-8'), None)
        blob = base64.b64encode(nonce + ct).decode('ascii')
        return {'result': blob}
    if action == 'decrypt':
        raw = base64.b64decode(text.strip())
        if len(raw) < 13:
            raise ValueError('密文过短')
        nonce, ct = raw[:12], raw[12:]
        try:
            return {'result': aes.decrypt(nonce, ct, None).decode('utf-8')}
        except Exception as exc:  # noqa: BLE001
            raise ValueError('AES-GCM 解密失败') from exc
    raise ValueError(f'未知操作: {action}')


def jwt_sign(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'sign':
        raise ValueError(f'未知操作: {action}')
    secret = options.get('key') or 'secret'
    alg = (options.get('alg') or 'HS256').upper()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError('Payload 需要是 JSON 对象') from exc
    if not isinstance(payload, dict):
        raise ValueError('Payload 需要是 JSON 对象')
    token = jwt.encode(payload, secret, algorithm=alg)
    return {'result': token}


def base32_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        return {'result': base64.b32encode(text.encode('utf-8')).decode('ascii')}
    if action == 'decode':
        raw = text.strip().replace(' ', '').upper()
        pad = '=' * (-len(raw) % 8)
        return {'result': base64.b32decode(raw + pad).decode('utf-8')}
    raise ValueError(f'未知操作: {action}')


def morse_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        parts = []
        for ch in text.upper():
            if ch in MORSE:
                parts.append(MORSE[ch])
            else:
                parts.append('?')
        return {'result': ' '.join(parts)}
    if action == 'decode':
        out = []
        for token in text.strip().split():
            out.append(MORSE_REV.get(token, '?'))
        return {'result': ''.join(out)}
    raise ValueError(f'未知操作: {action}')


def rot13_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    shift = 13 if action in ('rot13', 'encode', 'decode') else int(options.get('shift') or 13)

    def tr(s: str, n: int) -> str:
        res = []
        for ch in s:
            if 'a' <= ch <= 'z':
                res.append(chr((ord(ch) - 97 + n) % 26 + 97))
            elif 'A' <= ch <= 'Z':
                res.append(chr((ord(ch) - 65 + n) % 26 + 65))
            else:
                res.append(ch)
        return ''.join(res)

    if action in ('rot13', 'encode'):
        return {'result': tr(text, shift)}
    if action == 'decode':
        return {'result': tr(text, -shift)}
    if action == 'caesar':
        return {'result': tr(text, shift)}
    raise ValueError(f'未知操作: {action}')


def crc32_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'hash':
        raise ValueError(f'未知操作: {action}')
    value = zlib.crc32(text.encode('utf-8')) & 0xFFFFFFFF
    return {'result': f'{value:08x}\nunsigned: {value}'}


def binary_text(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action == 'encode':
        return {'result': ' '.join(f'{b:08b}' for b in text.encode('utf-8'))}
    if action == 'decode':
        bits = text.replace(' ', '').strip()
        if len(bits) % 8:
            raise ValueError('二进制长度需为 8 的倍数')
        data = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
        return {'result': data.decode('utf-8')}
    raise ValueError(f'未知操作: {action}')


def gzip_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    import gzip
    if action == 'compress':
        raw = gzip.compress(text.encode('utf-8'))
        return {'result': base64.b64encode(raw).decode('ascii')}
    if action == 'decompress':
        raw = base64.b64decode(text.strip())
        return {'result': gzip.decompress(raw).decode('utf-8')}
    raise ValueError(f'未知操作: {action}')


def base58_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    import base58
    if action == 'encode':
        return {'result': base58.b58encode(text.encode('utf-8')).decode('ascii')}
    if action == 'decode':
        return {'result': base58.b58decode(text.strip()).decode('utf-8')}
    raise ValueError(f'未知操作: {action}')


def rsa_tool(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization

    if action == 'keygen':
        bits = int(options.get('bits') or 2048)
        bits = 2048 if bits not in (2048, 3072, 4096) else bits
        key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
        priv = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode('ascii')
        pub = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode('ascii')
        return {'result': priv + chr(10) + pub}

    pem = (options.get('key') or '').strip()
    if not pem:
        raise ValueError('请在选项中粘贴 PEM 公钥或私钥')
    data = text.encode('utf-8')
    if action == 'encrypt':
        pub = serialization.load_pem_public_key(pem.encode('utf-8'))
        ct = pub.encrypt(
            data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        return {'result': base64.b64encode(ct).decode('ascii')}
    if action == 'decrypt':
        priv = serialization.load_pem_private_key(pem.encode('utf-8'), password=None)
        pt = priv.decrypt(
            base64.b64decode(text.strip()),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        return {'result': pt.decode('utf-8')}
    raise ValueError(f'未知操作: {action}')


def jwt_verify(action: str, text: str, options: dict[str, Any]) -> dict[str, Any]:
    if action != 'verify':
        raise ValueError(f'未知操作: {action}')
    secret = options.get('key') or 'secret'
    alg = (options.get('alg') or 'HS256').upper()
    try:
        payload = jwt.decode(text.strip(), secret, algorithms=[alg])
    except Exception as exc:  # noqa: BLE001
        return {'ok': False, 'error': f'校验失败: {exc}'}
    return {'result': json.dumps({'valid': True, 'payload': payload}, ensure_ascii=False, indent=2)}
