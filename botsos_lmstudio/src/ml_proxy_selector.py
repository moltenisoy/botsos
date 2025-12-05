"""
Módulo de Selección de Proxy con ML.

Usa Machine Learning para predecir el mejor proxy basado
en historial de rendimiento.

Implementa características de fase5.txt:
- Modelo de predicción (Random Forest, Gradient Boosting).
- Entrenamiento en datos históricos.
- Selección inteligente basada en contexto.
- Fallback a estrategias tradicionales.

Diseñado exclusivamente para Windows.
"""

import logging
import pickle
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
import json

logger = logging.getLogger(__name__)


@dataclass
class ProxyHistoryEntry:
    """Entrada de historial de uso de proxy."""
    proxy_id: str
    timestamp: datetime
    
    # Resultado
    success: bool
    latency_ms: float = 0.0
    
    # Contexto
    session_type: str = "youtube"
    action_type: str = "browse"
    
    # Metadatos del proxy
    proxy_type: str = "http"
    country: str = ""
    
    def to_features(self) -> Dict[str, float]:
        """Convierte a características para ML."""
        hour = self.timestamp.hour
        day_of_week = self.timestamp.weekday()
        
        return {
            'hour': hour,
            'day_of_week': day_of_week,
            'latency_ms': self.latency_ms,
            'is_http': 1.0 if self.proxy_type == 'http' else 0.0,
            'is_https': 1.0 if self.proxy_type == 'https' else 0.0,
            'is_socks5': 1.0 if self.proxy_type == 'socks5' else 0.0,
        }


@dataclass
class ProxyStats:
    """Estadísticas acumuladas de un proxy."""
    proxy_id: str
    server: str
    port: int
    proxy_type: str = "http"
    country: str = ""
    
    # Contadores
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Rendimiento
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    
    # Bloqueos
    bans_detected: int = 0
    
    # Tiempo
    last_used: Optional[datetime] = None
    first_used: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        if self.total_requests == 0:
            return 0.5  # Neutral para proxies nuevos
        return self.successful_requests / self.total_requests
    
    @property
    def avg_latency_ms(self) -> float:
        """Latencia promedio."""
        if self.successful_requests == 0:
            return 1000.0  # Default alto
        return self.total_latency_ms / self.successful_requests
    
    @property
    def hours_since_last_use(self) -> float:
        """Horas desde el último uso."""
        if not self.last_used:
            return 24.0  # Si nunca se usó, asumir 24 horas
        delta = datetime.now() - self.last_used
        return delta.total_seconds() / 3600
    
    def to_features(self) -> Dict[str, float]:
        """Convierte a características para ML."""
        return {
            'success_rate': self.success_rate,
            'avg_latency_ms': self.avg_latency_ms,
            'total_requests': float(self.total_requests),
            'bans_detected': float(self.bans_detected),
            'hours_since_last_use': self.hours_since_last_use,
            'is_http': 1.0 if self.proxy_type == 'http' else 0.0,
            'is_https': 1.0 if self.proxy_type == 'https' else 0.0,
            'is_socks5': 1.0 if self.proxy_type == 'socks5' else 0.0,
        }
    
    def update(self, success: bool, latency_ms: float):
        """Actualiza estadísticas con un nuevo resultado."""
        self.total_requests += 1
        self.last_used = datetime.now()
        
        if not self.first_used:
            self.first_used = datetime.now()
        
        if success:
            self.successful_requests += 1
            self.total_latency_ms += latency_ms
            self.min_latency_ms = min(self.min_latency_ms, latency_ms)
            self.max_latency_ms = max(self.max_latency_ms, latency_ms)
        else:
            self.failed_requests += 1


class MLProxySelector:
    """Selector de proxy basado en Machine Learning.
    
    Usa modelos de ML para predecir qué proxy tendrá
    mejor rendimiento en el contexto actual.
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        model_type: str = "random_forest",
        min_samples: int = 100
    ):
        """Inicializa el selector de proxy ML.
        
        Args:
            data_dir: Directorio para datos y modelo.
            model_type: Tipo de modelo (random_forest, gradient_boosting).
            min_samples: Mínimo de muestras para entrenar.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/ml_proxy")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_type = model_type
        self.min_samples = min_samples
        
        self._model = None
        self._scaler = None
        self._sklearn_available = False
        self._numpy_available = False
        
        self._proxy_stats: Dict[str, ProxyStats] = {}
        self._history: List[ProxyHistoryEntry] = []
        self._lock = Lock()
        
        self._feature_names = [
            'success_rate', 'avg_latency_ms', 'total_requests',
            'bans_detected', 'hours_since_last_use',
            'is_http', 'is_https', 'is_socks5',
            'hour', 'day_of_week'
        ]
        
        self._init_ml()
        self._load_data()
    
    def _init_ml(self):
        """Inicializa las bibliotecas de ML."""
        try:
            import numpy as np
            self._numpy_available = True
        except ImportError:
            logger.warning(
                "numpy no está instalado. "
                "Instale con: pip install numpy"
            )
        
        try:
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.preprocessing import StandardScaler
            self._sklearn_available = True
            logger.info("scikit-learn disponible para selección ML de proxy")
        except ImportError:
            logger.warning(
                "scikit-learn no está instalado. "
                "Instale con: pip install scikit-learn"
            )
    
    @property
    def is_available(self) -> bool:
        """Verifica si ML está disponible."""
        return self._sklearn_available and self._numpy_available
    
    @property
    def is_trained(self) -> bool:
        """Verifica si el modelo está entrenado."""
        return self._model is not None
    
    def _load_data(self):
        """Carga datos y modelo guardados."""
        # Cargar estadísticas de proxies
        stats_file = self.data_dir / "proxy_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for proxy_data in data.get('proxies', []):
                        stats = ProxyStats(
                            proxy_id=proxy_data['proxy_id'],
                            server=proxy_data['server'],
                            port=proxy_data['port'],
                            proxy_type=proxy_data.get('proxy_type', 'http')
                        )
                        stats.total_requests = proxy_data.get('total_requests', 0)
                        stats.successful_requests = proxy_data.get('successful_requests', 0)
                        stats.failed_requests = proxy_data.get('failed_requests', 0)
                        stats.total_latency_ms = proxy_data.get('total_latency_ms', 0.0)
                        stats.bans_detected = proxy_data.get('bans_detected', 0)
                        self._proxy_stats[stats.proxy_id] = stats
                logger.info(f"Cargadas estadísticas de {len(self._proxy_stats)} proxies")
            except Exception as e:
                logger.error(f"Error cargando estadísticas: {e}")
        
        # Cargar modelo entrenado
        model_file = self.data_dir / "proxy_model.pkl"
        if model_file.exists() and self.is_available:
            try:
                with open(model_file, 'rb') as f:
                    model_data = pickle.load(f)
                    self._model = model_data.get('model')
                    self._scaler = model_data.get('scaler')
                logger.info("Modelo ML cargado")
            except Exception as e:
                logger.error(f"Error cargando modelo: {e}")
    
    def _save_data(self):
        """Guarda datos y modelo."""
        # Guardar estadísticas
        try:
            stats_file = self.data_dir / "proxy_stats.json"
            data = {
                'proxies': [
                    {
                        'proxy_id': s.proxy_id,
                        'server': s.server,
                        'port': s.port,
                        'proxy_type': s.proxy_type,
                        'total_requests': s.total_requests,
                        'successful_requests': s.successful_requests,
                        'failed_requests': s.failed_requests,
                        'total_latency_ms': s.total_latency_ms,
                        'bans_detected': s.bans_detected
                    }
                    for s in self._proxy_stats.values()
                ],
                'last_saved': datetime.now().isoformat()
            }
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando estadísticas: {e}")
        
        # Guardar modelo
        if self._model is not None:
            try:
                model_file = self.data_dir / "proxy_model.pkl"
                with open(model_file, 'wb') as f:
                    pickle.dump({
                        'model': self._model,
                        'scaler': self._scaler
                    }, f)
            except Exception as e:
                logger.error(f"Error guardando modelo: {e}")
    
    def register_proxy(
        self,
        proxy_id: str,
        server: str,
        port: int,
        proxy_type: str = "http",
        country: str = ""
    ):
        """Registra un proxy en el sistema.
        
        Args:
            proxy_id: ID único del proxy.
            server: Servidor del proxy.
            port: Puerto del proxy.
            proxy_type: Tipo (http, https, socks5).
            country: País del proxy.
        """
        with self._lock:
            if proxy_id not in self._proxy_stats:
                self._proxy_stats[proxy_id] = ProxyStats(
                    proxy_id=proxy_id,
                    server=server,
                    port=port,
                    proxy_type=proxy_type,
                    country=country
                )
    
    def record_result(
        self,
        proxy_id: str,
        success: bool,
        latency_ms: float,
        session_type: str = "youtube",
        action_type: str = "browse"
    ):
        """Registra el resultado de usar un proxy.
        
        Args:
            proxy_id: ID del proxy.
            success: Si la solicitud fue exitosa.
            latency_ms: Latencia en milisegundos.
            session_type: Tipo de sesión.
            action_type: Tipo de acción realizada.
        """
        with self._lock:
            # Actualizar estadísticas
            if proxy_id in self._proxy_stats:
                self._proxy_stats[proxy_id].update(success, latency_ms)
            
            # Agregar al historial
            entry = ProxyHistoryEntry(
                proxy_id=proxy_id,
                timestamp=datetime.now(),
                success=success,
                latency_ms=latency_ms,
                session_type=session_type,
                action_type=action_type,
                proxy_type=self._proxy_stats.get(proxy_id, ProxyStats("", "", 0)).proxy_type
            )
            self._history.append(entry)
            
            # Limitar historial
            if len(self._history) > 10000:
                self._history = self._history[-5000:]
        
        # Guardar periódicamente
        if len(self._history) % 100 == 0:
            self._save_data()
    
    def record_ban(self, proxy_id: str):
        """Registra un bloqueo detectado para un proxy."""
        with self._lock:
            if proxy_id in self._proxy_stats:
                self._proxy_stats[proxy_id].bans_detected += 1
    
    def train_model(self) -> bool:
        """Entrena el modelo con los datos históricos.
        
        Returns:
            True si se entrenó exitosamente.
        """
        if not self.is_available:
            logger.warning("ML no disponible para entrenamiento")
            return False
        
        with self._lock:
            if len(self._history) < self.min_samples:
                logger.warning(
                    f"Insuficientes muestras para entrenar: "
                    f"{len(self._history)}/{self.min_samples}"
                )
                return False
            
            try:
                import numpy as np
                from sklearn.preprocessing import StandardScaler
                
                if self.model_type == "gradient_boosting":
                    from sklearn.ensemble import GradientBoostingClassifier
                    self._model = GradientBoostingClassifier(
                        n_estimators=100,
                        max_depth=5,
                        random_state=42
                    )
                else:
                    from sklearn.ensemble import RandomForestClassifier
                    self._model = RandomForestClassifier(
                        n_estimators=100,
                        max_depth=10,
                        random_state=42
                    )
                
                # Preparar datos
                X = []
                y = []
                
                for entry in self._history:
                    if entry.proxy_id in self._proxy_stats:
                        # Combinar características del proxy y del contexto
                        proxy_features = self._proxy_stats[entry.proxy_id].to_features()
                        entry_features = entry.to_features()
                        
                        features = []
                        for name in self._feature_names:
                            if name in proxy_features:
                                features.append(proxy_features[name])
                            elif name in entry_features:
                                features.append(entry_features[name])
                            else:
                                features.append(0.0)
                        
                        X.append(features)
                        y.append(1 if entry.success else 0)
                
                if len(X) < self.min_samples:
                    return False
                
                X = np.array(X)
                y = np.array(y)
                
                # Escalar características
                self._scaler = StandardScaler()
                X_scaled = self._scaler.fit_transform(X)
                
                # Entrenar modelo
                self._model.fit(X_scaled, y)
                
                # Guardar modelo
                self._save_data()
                
                logger.info(f"Modelo entrenado con {len(X)} muestras")
                return True
                
            except Exception as e:
                logger.error(f"Error entrenando modelo: {e}")
                return False
    
    def select_best_proxy(
        self,
        available_proxies: List[Dict[str, Any]],
        session_type: str = "youtube",
        action_type: str = "browse"
    ) -> Optional[str]:
        """Selecciona el mejor proxy usando ML.
        
        Args:
            available_proxies: Lista de proxies disponibles.
            session_type: Tipo de sesión.
            action_type: Tipo de acción a realizar.
            
        Returns:
            ID del mejor proxy o None.
        """
        if not available_proxies:
            return None
        
        # Si el modelo no está entrenado, usar fallback
        if not self.is_trained or not self.is_available:
            return self._select_best_fallback(available_proxies)
        
        try:
            import numpy as np
            
            best_proxy_id = None
            best_score = -1.0
            
            now = datetime.now()
            hour = now.hour
            day_of_week = now.weekday()
            
            for proxy in available_proxies:
                proxy_id = proxy.get('proxy_id', f"{proxy['server']}:{proxy['port']}")
                
                # Obtener o crear estadísticas
                if proxy_id not in self._proxy_stats:
                    self.register_proxy(
                        proxy_id=proxy_id,
                        server=proxy['server'],
                        port=proxy['port'],
                        proxy_type=proxy.get('type', 'http'),
                        country=proxy.get('country', '')
                    )
                
                stats = self._proxy_stats[proxy_id]
                
                # Preparar características
                proxy_features = stats.to_features()
                context_features = {
                    'hour': float(hour),
                    'day_of_week': float(day_of_week)
                }
                
                features = []
                for name in self._feature_names:
                    if name in proxy_features:
                        features.append(proxy_features[name])
                    elif name in context_features:
                        features.append(context_features[name])
                    else:
                        features.append(0.0)
                
                # Predecir probabilidad de éxito
                X = np.array([features])
                X_scaled = self._scaler.transform(X)
                
                proba = self._model.predict_proba(X_scaled)[0]
                success_proba = proba[1] if len(proba) > 1 else proba[0]
                
                if success_proba > best_score:
                    best_score = success_proba
                    best_proxy_id = proxy_id
            
            logger.debug(f"Proxy seleccionado por ML: {best_proxy_id} (score: {best_score:.3f})")
            return best_proxy_id
            
        except Exception as e:
            logger.error(f"Error en selección ML: {e}")
            return self._select_best_fallback(available_proxies)
    
    def _select_best_fallback(
        self,
        available_proxies: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Selección de fallback basada en estadísticas simples.
        
        Args:
            available_proxies: Lista de proxies disponibles.
            
        Returns:
            ID del mejor proxy o None.
        """
        if not available_proxies:
            return None
        
        best_proxy_id = None
        best_score = -1.0
        
        for proxy in available_proxies:
            proxy_id = proxy.get('proxy_id', f"{proxy['server']}:{proxy['port']}")
            
            if proxy_id in self._proxy_stats:
                stats = self._proxy_stats[proxy_id]
                # Score basado en tasa de éxito e inversamente proporcional a latencia
                score = stats.success_rate - (stats.avg_latency_ms / 10000)
                # Penalizar proxies con muchos bloqueos
                score -= stats.bans_detected * 0.1
            else:
                # Proxy nuevo, darle una oportunidad
                score = 0.5
            
            if score > best_score:
                best_score = score
                best_proxy_id = proxy_id
        
        logger.debug(f"Proxy seleccionado por fallback: {best_proxy_id}")
        return best_proxy_id
    
    def get_proxy_ranking(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Obtiene un ranking de los mejores proxies.
        
        Args:
            top_n: Número de proxies a retornar.
            
        Returns:
            Lista de proxies ordenados por rendimiento.
        """
        with self._lock:
            proxies = list(self._proxy_stats.values())
            
            # Ordenar por tasa de éxito y latencia
            proxies.sort(
                key=lambda p: (p.success_rate, -p.avg_latency_ms),
                reverse=True
            )
            
            return [
                {
                    'proxy_id': p.proxy_id,
                    'server': p.server,
                    'port': p.port,
                    'success_rate': p.success_rate,
                    'avg_latency_ms': p.avg_latency_ms,
                    'total_requests': p.total_requests,
                    'bans_detected': p.bans_detected
                }
                for p in proxies[:top_n]
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema.
        
        Returns:
            Diccionario con estadísticas.
        """
        with self._lock:
            return {
                'ml_available': self.is_available,
                'model_trained': self.is_trained,
                'total_proxies': len(self._proxy_stats),
                'history_samples': len(self._history),
                'min_samples_for_training': self.min_samples,
                'model_type': self.model_type
            }
    
    def cleanup(self):
        """Guarda datos y limpia recursos."""
        self._save_data()
        logger.info("Datos de ML proxy guardados")
