"""
Módulo de Gestión de Cuentas.

Maneja la importación, exportación y gestión de cuentas
con encriptación segura.

Implementa características de fase5.txt:
- Importación/exportación de cuentas desde CSV.
- Encriptación con Fernet (clave almacenada en keyring).
- Rotación de cuentas por sesión.
- Almacenamiento seguro de credenciales.

Diseñado exclusivamente para Windows.
"""

import csv
import io
import logging
import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class AccountEntry:
    """Representa una cuenta de usuario."""
    account_id: str
    email: str
    password: str = ""  # Encriptado
    username: str = ""
    platform: str = "youtube"
    
    # Estado
    is_active: bool = True
    last_used: Optional[datetime] = None
    use_count: int = 0
    
    # Metadatos
    country: str = ""
    proxy_preference: str = ""
    notes: str = ""
    
    # Seguridad
    requires_2fa: bool = False
    recovery_email: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario (sin contraseña)."""
        return {
            "account_id": self.account_id,
            "email": self.email,
            "username": self.username,
            "platform": self.platform,
            "is_active": self.is_active,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "use_count": self.use_count,
            "country": self.country,
            "proxy_preference": self.proxy_preference,
            "requires_2fa": self.requires_2fa
        }


class EncryptionManager:
    """Administrador de encriptación con Fernet.
    
    Usa Fernet para encriptación simétrica y keyring
    para almacenamiento seguro de la clave.
    """
    
    SERVICE_NAME = "botsos_accounts"
    KEY_NAME = "encryption_key"
    
    def __init__(self) -> None:
        """Inicializa el administrador de encriptación."""
        self._fernet = None
        self._key: Optional[bytes] = None
        self._init_encryption()
    
    def _init_encryption(self) -> None:
        """Inicializa la encriptación."""
        try:
            from cryptography.fernet import Fernet
            
            # Intentar obtener clave existente
            self._key = self._get_stored_key()
            
            if not self._key:
                # Generar nueva clave
                self._key = Fernet.generate_key()
                self._store_key(self._key)
            
            self._fernet = Fernet(self._key)
            logger.info("Encriptación inicializada correctamente")
            
        except ImportError:
            logger.error(
                "cryptography no está instalado. "
                "Instale con: pip install cryptography"
            )
        except Exception as e:
            logger.error(f"Error inicializando encriptación: {e}")
    
    def _get_stored_key(self) -> Optional[bytes]:
        """Obtiene la clave almacenada."""
        # Intentar keyring primero
        try:
            import keyring
            key_str = keyring.get_password(self.SERVICE_NAME, self.KEY_NAME)
            if key_str:
                return key_str.encode()
        except (ImportError, Exception):
            pass
        
        # Fallback: variable de entorno
        key_env = os.environ.get("BOTSOS_ENCRYPTION_KEY")
        if key_env:
            return key_env.encode()
        
        return None
    
    def _store_key(self, key: bytes):
        """Almacena la clave de forma segura."""
        try:
            import keyring
            keyring.set_password(self.SERVICE_NAME, self.KEY_NAME, key.decode())
            logger.info("Clave de encriptación almacenada en keyring")
        except (ImportError, Exception) as e:
            logger.warning(f"No se pudo usar keyring, usando variable de entorno: {e}")
            os.environ["BOTSOS_ENCRYPTION_KEY"] = key.decode()
    
    @property
    def is_available(self) -> bool:
        """Verifica si la encriptación está disponible."""
        return self._fernet is not None
    
    def encrypt(self, data: str) -> str:
        """Encripta una cadena.
        
        Args:
            data: Datos a encriptar.
            
        Returns:
            Datos encriptados en base64.
        """
        if not self._fernet:
            raise RuntimeError("Encriptación no disponible")
        
        encrypted = self._fernet.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Desencripta una cadena.
        
        Args:
            encrypted_data: Datos encriptados en base64.
            
        Returns:
            Datos desencriptados.
        """
        if not self._fernet:
            raise RuntimeError("Encriptación no disponible")
        
        decrypted = self._fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    def encrypt_file(self, input_path: Path, output_path: Path) -> bool:
        """Encripta un archivo.
        
        Args:
            input_path: Ruta del archivo a encriptar.
            output_path: Ruta del archivo encriptado.
            
        Returns:
            True si se encriptó exitosamente.
        """
        if not self._fernet:
            return False
        
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            encrypted = self._fernet.encrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            logger.error(f"Error encriptando archivo: {e}")
            return False
    
    def decrypt_file(self, input_path: Path, output_path: Path) -> bool:
        """Desencripta un archivo.
        
        Args:
            input_path: Ruta del archivo encriptado.
            output_path: Ruta del archivo desencriptado.
            
        Returns:
            True si se desencriptó exitosamente.
        """
        if not self._fernet:
            return False
        
        try:
            with open(input_path, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self._fernet.decrypt(encrypted)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            return True
        except Exception as e:
            logger.error(f"Error desencriptando archivo: {e}")
            return False


class AccountManager:
    """Administrador de cuentas de usuario.
    
    Gestiona cuentas con encriptación segura,
    importación/exportación CSV y rotación automática.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Inicializa el administrador de cuentas.
        
        Args:
            data_dir: Directorio para almacenamiento de datos.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/accounts")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._accounts: Dict[str, AccountEntry] = {}
        self._lock = Lock()
        self._current_index = 0
        
        # Encriptación
        self.encryption = EncryptionManager()
        
        # Cargar cuentas existentes
        self._load_accounts()
    
    def _load_accounts(self) -> None:
        """Carga las cuentas almacenadas."""
        accounts_file = self.data_dir / "accounts.enc"
        
        if not accounts_file.exists():
            return
        
        if not self.encryption.is_available:
            logger.warning("Encriptación no disponible, no se pueden cargar cuentas")
            return
        
        try:
            # Desencriptar y cargar
            with open(accounts_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Nota: Fernet se importa pero no se usa directamente aquí
            decrypted_data = self.encryption._fernet.decrypt(encrypted_data)
            
            import json
            data = json.loads(decrypted_data.decode())
            
            for account_data in data.get('accounts', []):
                account = AccountEntry(
                    account_id=account_data['account_id'],
                    email=account_data['email'],
                    password=account_data.get('password', ''),
                    username=account_data.get('username', ''),
                    platform=account_data.get('platform', 'youtube'),
                    is_active=account_data.get('is_active', True),
                    use_count=account_data.get('use_count', 0),
                    country=account_data.get('country', ''),
                    requires_2fa=account_data.get('requires_2fa', False)
                )
                self._accounts[account.account_id] = account
            
            logger.info(f"Cargadas {len(self._accounts)} cuentas")
            
        except Exception as e:
            logger.error(f"Error cargando cuentas: {e}")
    
    def _save_accounts(self):
        """Guarda las cuentas encriptadas."""
        if not self.encryption.is_available:
            logger.warning("Encriptación no disponible, no se pueden guardar cuentas")
            return
        
        try:
            import json
            
            # Preparar datos
            data = {
                'accounts': [
                    {
                        'account_id': a.account_id,
                        'email': a.email,
                        'password': a.password,
                        'username': a.username,
                        'platform': a.platform,
                        'is_active': a.is_active,
                        'use_count': a.use_count,
                        'country': a.country,
                        'requires_2fa': a.requires_2fa
                    }
                    for a in self._accounts.values()
                ],
                'last_saved': datetime.now().isoformat()
            }
            
            # Encriptar y guardar
            json_data = json.dumps(data).encode()
            encrypted_data = self.encryption._fernet.encrypt(json_data)
            
            accounts_file = self.data_dir / "accounts.enc"
            with open(accounts_file, 'wb') as f:
                f.write(encrypted_data)
            
            logger.debug("Cuentas guardadas exitosamente")
            
        except Exception as e:
            logger.error(f"Error guardando cuentas: {e}")
    
    def add_account(
        self,
        email: str,
        password: str,
        username: str = "",
        platform: str = "youtube",
        **kwargs
    ) -> Optional[str]:
        """Agrega una nueva cuenta.
        
        Args:
            email: Correo electrónico.
            password: Contraseña.
            username: Nombre de usuario.
            platform: Plataforma (youtube, etc.).
            **kwargs: Metadatos adicionales.
            
        Returns:
            ID de la cuenta o None si falló.
        """
        import uuid
        
        with self._lock:
            # Verificar duplicados
            for account in self._accounts.values():
                if account.email == email and account.platform == platform:
                    logger.warning(f"Cuenta {email} ya existe para {platform}")
                    return None
            
            account_id = str(uuid.uuid4())[:8]
            
            # Encriptar contraseña
            encrypted_password = password
            if self.encryption.is_available:
                encrypted_password = self.encryption.encrypt(password)
            
            account = AccountEntry(
                account_id=account_id,
                email=email,
                password=encrypted_password,
                username=username,
                platform=platform,
                country=kwargs.get('country', ''),
                requires_2fa=kwargs.get('requires_2fa', False),
                recovery_email=kwargs.get('recovery_email', ''),
                notes=kwargs.get('notes', '')
            )
            
            self._accounts[account_id] = account
            self._save_accounts()
            
            logger.info(f"Cuenta agregada: {account_id} ({email})")
            return account_id
    
    def remove_account(self, account_id: str) -> bool:
        """Elimina una cuenta.
        
        Args:
            account_id: ID de la cuenta.
            
        Returns:
            True si se eliminó exitosamente.
        """
        with self._lock:
            if account_id not in self._accounts:
                return False
            
            del self._accounts[account_id]
            self._save_accounts()
            
            logger.info(f"Cuenta eliminada: {account_id}")
            return True
    
    def get_account(self, account_id: str) -> Optional[AccountEntry]:
        """Obtiene una cuenta por ID."""
        return self._accounts.get(account_id)
    
    def get_account_credentials(self, account_id: str) -> Optional[Dict[str, str]]:
        """Obtiene las credenciales desencriptadas de una cuenta.
        
        Args:
            account_id: ID de la cuenta.
            
        Returns:
            Diccionario con email y contraseña, o None.
        """
        account = self._accounts.get(account_id)
        if not account:
            return None
        
        try:
            password = account.password
            if self.encryption.is_available and account.password:
                password = self.encryption.decrypt(account.password)
            
            return {
                'email': account.email,
                'password': password,
                'username': account.username
            }
        except Exception as e:
            logger.error(f"Error desencriptando credenciales: {e}")
            return None
    
    def get_next_account(self, platform: str = "youtube") -> Optional[AccountEntry]:
        """Obtiene la siguiente cuenta disponible (rotación).
        
        Args:
            platform: Plataforma para filtrar.
            
        Returns:
            La siguiente cuenta disponible o None.
        """
        with self._lock:
            active_accounts = [
                a for a in self._accounts.values()
                if a.is_active and a.platform == platform
            ]
            
            if not active_accounts:
                return None
            
            # Ordenar por uso (menos usadas primero)
            active_accounts.sort(key=lambda a: a.use_count)
            
            # Obtener la menos usada
            account = active_accounts[0]
            account.last_used = datetime.now()
            account.use_count += 1
            
            self._save_accounts()
            return account
    
    def get_all_accounts(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Obtiene todas las cuentas.
        
        Args:
            include_inactive: Si se incluyen cuentas inactivas.
            
        Returns:
            Lista de cuentas (sin contraseñas).
        """
        with self._lock:
            accounts = [
                a.to_dict() for a in self._accounts.values()
                if include_inactive or a.is_active
            ]
            return accounts
    
    def import_from_csv(self, file_path: Path, encrypted: bool = True) -> int:
        """Importa cuentas desde un archivo CSV.
        
        Args:
            file_path: Ruta del archivo CSV.
            encrypted: Si el archivo está encriptado.
            
        Returns:
            Número de cuentas importadas.
        """
        try:
            content = ""
            
            if encrypted and self.encryption.is_available:
                # Desencriptar archivo
                with open(file_path, 'rb') as f:
                    encrypted_data = f.read()
                decrypted = self.encryption._fernet.decrypt(encrypted_data)
                content = decrypted.decode()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Parsear CSV
            reader = csv.DictReader(io.StringIO(content))
            count = 0
            
            for row in reader:
                email = row.get('email', row.get('Email', '')).strip()
                password = row.get('password', row.get('Password', '')).strip()
                
                if email and password:
                    account_id = self.add_account(
                        email=email,
                        password=password,
                        username=row.get('username', row.get('Username', '')),
                        platform=row.get('platform', row.get('Platform', 'youtube')),
                        country=row.get('country', row.get('Country', '')),
                        requires_2fa=row.get('requires_2fa', '').lower() == 'true'
                    )
                    if account_id:
                        count += 1
            
            logger.info(f"Importadas {count} cuentas desde {file_path}")
            return count
            
        except Exception as e:
            logger.error(f"Error importando CSV: {e}")
            return 0
    
    def export_to_csv(self, file_path: Path, encrypt: bool = True) -> bool:
        """Exporta cuentas a un archivo CSV.
        
        Args:
            file_path: Ruta del archivo de salida.
            encrypt: Si se debe encriptar el archivo.
            
        Returns:
            True si se exportó exitosamente.
        """
        try:
            # Generar CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'email', 'password', 'username', 'platform',
                'country', 'requires_2fa', 'use_count'
            ])
            writer.writeheader()
            
            for account in self._accounts.values():
                # Desencriptar contraseña para exportación
                password = account.password
                if self.encryption.is_available and account.password:
                    try:
                        password = self.encryption.decrypt(account.password)
                    except Exception:
                        pass
                
                writer.writerow({
                    'email': account.email,
                    'password': password,
                    'username': account.username,
                    'platform': account.platform,
                    'country': account.country,
                    'requires_2fa': str(account.requires_2fa),
                    'use_count': account.use_count
                })
            
            csv_content = output.getvalue()
            
            if encrypt and self.encryption.is_available:
                # Encriptar y guardar
                encrypted = self.encryption._fernet.encrypt(csv_content.encode())
                with open(file_path, 'wb') as f:
                    f.write(encrypted)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
            
            logger.info(f"Exportadas {len(self._accounts)} cuentas a {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando CSV: {e}")
            return False
    
    def set_account_active(self, account_id: str, active: bool) -> bool:
        """Activa o desactiva una cuenta.
        
        Args:
            account_id: ID de la cuenta.
            active: Si debe estar activa.
            
        Returns:
            True si se actualizó exitosamente.
        """
        with self._lock:
            if account_id not in self._accounts:
                return False
            
            self._accounts[account_id].is_active = active
            self._save_accounts()
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de las cuentas.
        
        Returns:
            Diccionario con estadísticas.
        """
        with self._lock:
            accounts = list(self._accounts.values())
            
            return {
                "total": len(accounts),
                "active": sum(1 for a in accounts if a.is_active),
                "inactive": sum(1 for a in accounts if not a.is_active),
                "requires_2fa": sum(1 for a in accounts if a.requires_2fa),
                "total_uses": sum(a.use_count for a in accounts),
                "platforms": list(set(a.platform for a in accounts))
            }
    
    def cleanup(self):
        """Guarda datos y limpia recursos."""
        self._save_accounts()
        logger.info("Cuentas guardadas")
