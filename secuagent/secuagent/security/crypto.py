"""
Encryption Service - 암호화 서비스

AES-256-GCM, RSA-4096 암호화 및 키 관리
"""

from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime
import os
import base64
import json

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag
import secrets


@dataclass
class KeyInfo:
    """키 정보"""
    key_id: str
    algorithm: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class KeyManager:
    """
    키 관리자
    
    암호화 키의 생성, 저장, 회전, 폐기를 관리
    """
    
    def __init__(self):
        self._keys: Dict[str, bytes] = {}
        self._key_info: Dict[str, KeyInfo] = {}
        self._default_key_id: Optional[str] = None
    
    def generate_symmetric_key(self, key_size: int = 32) -> str:
        """대칭키 생성 (AES-256 기본)"""
        key_id = secrets.token_hex(16)
        key = secrets.token_bytes(key_size)
        
        self._keys[key_id] = key
        self._key_info[key_id] = KeyInfo(
            key_id=key_id,
            algorithm=f"AES-{key_size * 8}",
            created_at=datetime.utcnow()
        )
        
        if self._default_key_id is None:
            self._default_key_id = key_id
        
        return key_id
    
    def generate_asymmetric_key_pair(
        self,
        key_size: int = 4096
    ) -> tuple[str, str]:
        """비대칭 키 쌍 생성 (RSA)"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        key_id = secrets.token_hex(16)
        
        # 개인키 저장
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        self._keys[f"{key_id}_private"] = private_pem
        
        # 공개키 저장
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self._keys[f"{key_id}_public"] = public_pem
        
        self._key_info[key_id] = KeyInfo(
            key_id=key_id,
            algorithm=f"RSA-{key_size}",
            created_at=datetime.utcnow()
        )
        
        return f"{key_id}_private", f"{key_id}_public"
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """키 조회"""
        return self._keys.get(key_id)
    
    def get_default_key_id(self) -> Optional[str]:
        """기본 키 ID 반환"""
        return self._default_key_id
    
    def rotate_key(self, key_id: str) -> str:
        """키 회전 (새 키 생성, 기존 키 비활성화)"""
        if key_id not in self._key_info:
            raise ValueError(f"Key not found: {key_id}")
        
        # 기존 키 비활성화
        self._key_info[key_id].is_active = False
        
        # 새 키 생성
        key_info = self._key_info[key_id]
        if "AES" in key_info.algorithm:
            new_key_id = self.generate_symmetric_key()
        else:
            new_key_id, _ = self.generate_asymmetric_key_pair()
            new_key_id = new_key_id.replace("_private", "")
        
        return new_key_id
    
    def delete_key(self, key_id: str) -> bool:
        """키 삭제"""
        if key_id in self._keys:
            del self._keys[key_id]
        if key_id in self._key_info:
            del self._key_info[key_id]
        return True
    
    def list_keys(self) -> list[KeyInfo]:
        """키 목록 반환"""
        return list(self._key_info.values())


class EncryptionService:
    """
    암호화 서비스
    
    AES-256-GCM 대칭 암호화 및 RSA 비대칭 암호화 제공
    """
    
    def __init__(self, key_manager: Optional[KeyManager] = None):
        self.key_manager = key_manager or KeyManager()
    
    def encrypt_aes(
        self,
        plaintext: Union[str, bytes],
        key_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        AES-256-GCM 암호화
        
        Returns:
            dict: {nonce, ciphertext, tag} (모두 base64 인코딩)
        """
        if key_id is None:
            key_id = self.key_manager.get_default_key_id()
            if key_id is None:
                key_id = self.key_manager.generate_symmetric_key()
        
        key = self.key_manager.get_key(key_id)
        if key is None:
            raise ValueError(f"Key not found: {key_id}")
        
        # plaintext 을 바이트로 변환
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # nonce 생성
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        
        # 암호화
        aesgcm = AESGCM(key)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)
        
        # ciphertext 와 tag 분리 (tag 는 마지막 16 바이트)
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        return {
            "key_id": key_id,
            "nonce": base64.b64encode(nonce).decode('ascii'),
            "ciphertext": base64.b64encode(ciphertext).decode('ascii'),
            "tag": base64.b64encode(tag).decode('ascii'),
            "algorithm": "AES-256-GCM"
        }
    
    def decrypt_aes(
        self,
        encrypted_data: Dict[str, str],
        key_id: Optional[str] = None
    ) -> bytes:
        """
        AES-256-GCM 복호화
        
        Args:
            encrypted_data: {nonce, ciphertext, tag} (base64 인코딩)
            key_id: 키 ID (생략시 encrypted_data 에서 사용)
        """
        if key_id is None:
            key_id = encrypted_data.get("key_id")
            if key_id is None:
                raise ValueError("key_id required")
        
        key = self.key_manager.get_key(key_id)
        if key is None:
            raise ValueError(f"Key not found: {key_id}")
        
        nonce = base64.b64decode(encrypted_data["nonce"])
        ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        tag = base64.b64decode(encrypted_data["tag"])
        
        # 복호화
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext + tag, None)
            return plaintext
        except InvalidTag:
            raise ValueError("Decryption failed: invalid tag or corrupted data")
    
    def encrypt_rsa(
        self,
        plaintext: Union[str, bytes],
        public_key_id: str
    ) -> str:
        """
        RSA 암호화
        
        Returns:
            base64 인코딩된 암호문
        """
        public_key_pem = self.key_manager.get_key(public_key_id)
        if public_key_pem is None:
            raise ValueError(f"Public key not found: {public_key_id}")
        
        # 공개키 로드
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        
        # plaintext 을 바이트로 변환
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # 암호화
        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(ciphertext).decode('ascii')
    
    def decrypt_rsa(
        self,
        ciphertext_b64: str,
        private_key_id: str
    ) -> bytes:
        """
        RSA 복호화
        """
        private_key_pem = self.key_manager.get_key(private_key_id)
        if private_key_pem is None:
            raise ValueError(f"Private key not found: {private_key_id}")
        
        # 개인키 로드
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )
        
        # 복호화
        ciphertext = base64.b64decode(ciphertext_b64)
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return plaintext
    
    def hash_data(
        self,
        data: Union[str, bytes],
        algorithm: str = "sha256"
    ) -> str:
        """데이터 해시"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if algorithm == "sha256":
            h = hashes.Hash(hashes.SHA256(), backend=default_backend())
        elif algorithm == "sha512":
            h = hashes.Hash(hashes.SHA512(), backend=default_backend())
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        h.update(data)
        return h.finalize().hex()
