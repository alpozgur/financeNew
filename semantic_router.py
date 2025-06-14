"""
Semantic Router Implementation
Uses sentence transformers for semantic matching and advanced routing capabilities
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import time
from collections import defaultdict
import re

@dataclass
class RouteMatch:
    """Route eşleşme sonucu"""
    handler: str
    method: str
    confidence: float
    context: Dict[str, Any]
    reasoning: str = ""
    is_multi_handler: bool = False
    execution_order: int = 50

class SemanticRouter:
    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        similarity_threshold: float = 0.7,
        max_matches: int = 5,
        cache_size: int = 1000
    ):
        """
        Semantic Router initialization
        
        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Minimum similarity score for matches
            max_matches: Maximum number of matches to return
            cache_size: Size of the LRU cache for embeddings
        """
        self.logger = logging.getLogger('semantic_router')
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        self.max_matches = max_matches
        self.cache_size = cache_size
        
        # Handler bilgileri ve embedding'leri
        self.handler_descriptions: Dict[str, Dict] = {}
        self.handler_embeddings: Dict[str, np.ndarray] = {}
        
        # Cache
        self.question_cache: Dict[str, Tuple[float, List[RouteMatch]]] = {}
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        # İstatistikler
        self.metrics = defaultdict(int)
        self.last_reset = time.time()
        
    def add_handler(
        self,
        handler: str,
        description: str,
        methods: Dict[str, str],
        examples: List[str] = None,
        execution_order: int = 50
    ) -> None:
        """
        Yeni handler ekle
        
        Args:
            handler: Handler adı
            description: Handler açıklaması
            methods: Desteklenen metodlar ve açıklamaları
            examples: Örnek sorular
            execution_order: Çalışma sırası
        """
        # Handler bilgilerini kaydet
        self.handler_descriptions[handler] = {
            'description': description,
            'methods': methods,
            'examples': examples or [],
            'execution_order': execution_order
        }
        
        # Handler için embedding oluştur
        texts_to_encode = [description]
        if examples:
            texts_to_encode.extend(examples)
            
        # Tüm metinleri birleştir ve embedding oluştur
        combined_text = " ".join(texts_to_encode)
        embedding = self.model.encode(combined_text)
        self.handler_embeddings[handler] = embedding
        
        self.logger.info(f"Added handler: {handler}")
        
    def route(self, question: str) -> List[RouteMatch]:
        """
        Soruyu route et
        
        Args:
            question: Kullanıcı sorusu
            
        Returns:
            List[RouteMatch]: Eşleşen handler'lar
        """
        start_time = time.time()
        
        # Cache kontrolü
        if cached := self._check_cache(question):
            self.metrics['cache_hits'] += 1
            return cached
            
        self.metrics['cache_misses'] += 1
        
        # Önce pattern matching kontrolü
        question_lower = question.lower()
        exact_matches = []
        
        # Performance analyzer için özel pattern kontrolü
        performance_patterns = [
            r'en\s*(?:çok\s*)?kazandıran\s*(?:fonlar?)?',
            r'en\s*(?:iyi|yüksek)\s*(?:performans|getiri)(?:\s*(?:gösteren|li))?\s*(?:fonlar?)?',
            r'en\s*(?:çok\s*)?kazandıran\s*\d*\s*(?:fonlar?)?',
            r'(?:son|geçen)\s*\d*\s*(?:ay|yıl)\s*(?:en\s*(?:iyi|çok\s*kazandıran))?\s*(?:fonlar?)?'
        ]
        
        if any(re.search(pattern, question_lower) for pattern in performance_patterns):
            exact_matches.append(RouteMatch(
                handler='performance_analyzer',
                method='handle_top_gainers',
                confidence=1.0,
                context={'question': question, 'handler': 'performance_analyzer'},
                reasoning='Exact pattern match for performance question',
                is_multi_handler=False,
                execution_order=5
            ))
            return exact_matches
        
        # Soruyu embedding'e çevir
        question_embedding = self._get_embedding(question)
        
        # Benzerlik hesapla
        matches = []
        for handler, handler_embedding in self.handler_embeddings.items():
            similarity = cosine_similarity(
                [question_embedding],
                [handler_embedding]
            )[0][0]
            
            if similarity >= self.similarity_threshold:
                # Context ve method belirle
                context = self._extract_context(question, handler)
                method = self._determine_method(question, handler)
                
                match = RouteMatch(
                    handler=handler,
                    method=method,
                    confidence=float(similarity),
                    context=context,
                    reasoning=self._generate_reasoning(question, handler, similarity),
                    is_multi_handler=self._check_multi_handler(question, handler),
                    execution_order=self.handler_descriptions[handler]['execution_order']
                )
                matches.append(match)
        
        # Sonuçları sırala
        matches.sort(key=lambda x: (x.execution_order, -x.confidence))
        matches = matches[:self.max_matches]
        
        # Cache'e kaydet
        self._update_cache(question, matches)
        
        # Metrikleri güncelle
        duration = time.time() - start_time
        self._update_metrics(duration)
        
        return matches
        
    def _get_embedding(self, text: str) -> np.ndarray:
        """Metin için embedding oluştur veya cache'den al"""
        if text in self.embedding_cache:
            return self.embedding_cache[text]
            
        embedding = self.model.encode(text)
        self.embedding_cache[text] = embedding
        
        # Cache boyutunu kontrol et
        if len(self.embedding_cache) > self.cache_size:
            # En eski entry'i sil
            self.embedding_cache.pop(next(iter(self.embedding_cache)))
            
        return embedding
        
    def _check_cache(self, question: str) -> Optional[List[RouteMatch]]:
        """Cache'de sonuç var mı kontrol et"""
        if question in self.question_cache:
            timestamp, matches = self.question_cache[question]
            # 1 saat geçmişse cache'i temizle
            if time.time() - timestamp < 3600:
                return matches
            else:
                del self.question_cache[question]
        return None
        
    def _update_cache(self, question: str, matches: List[RouteMatch]) -> None:
        """Cache'i güncelle"""
        self.question_cache[question] = (time.time(), matches)
        
        # Cache boyutunu kontrol et
        if len(self.question_cache) > self.cache_size:
            # En eski entry'i sil
            self.question_cache.pop(next(iter(self.question_cache)))
            
    def _extract_context(self, question: str, handler: str) -> Dict[str, Any]:
        """Soru ve handler'dan context çıkar"""
        context = {
            'question': question,
            'handler': handler,
            'timestamp': time.time()
        }
        
        # Handler'a özel context extraction
        handler_info = self.handler_descriptions[handler]
        if 'context_extractor' in handler_info:
            context.update(handler_info['context_extractor'](question))
            
        return context
        
    def _determine_method(self, question: str, handler: str) -> str:
        """Soru için uygun method'u belirle"""
        handler_info = self.handler_descriptions[handler]
        methods = handler_info['methods']
        
        # Method belirleme mantığı
        question_lower = question.lower()
        
        # Özel method belirleme kuralları
        if any(word in question_lower for word in ['getir', 'göster', 'listele']):
            return 'GET'
        elif any(word in question_lower for word in ['ekle', 'kaydet', 'oluştur']):
            return 'POST'
        elif any(word in question_lower for word in ['güncelle', 'değiştir']):
            return 'PUT'
        elif any(word in question_lower for word in ['sil', 'kaldır']):
            return 'DELETE'
            
        # Varsayılan method
        return next(iter(methods))
        
    def _check_multi_handler(self, question: str, handler: str) -> bool:
        """Multi-handler gerekiyor mu kontrol et"""
        # Multi-handler trigger kelimeleri
        multi_triggers = ['ve', 'ile', 'aynı zamanda', 'hem', 'hem de']
        
        question_lower = question.lower()
        return any(trigger in question_lower for trigger in multi_triggers)
        
    def _generate_reasoning(self, question: str, handler: str, 
                          similarity: float) -> str:
        """Eşleşme için açıklama oluştur"""
        handler_info = self.handler_descriptions[handler]
        
        if similarity > 0.9:
            return "Yüksek benzerlik skoru ile eşleşme"
        elif similarity > 0.8:
            return "Güçlü semantic eşleşme"
        else:
            return f"Semantic benzerlik: {similarity:.2f}"
            
    def _update_metrics(self, duration: float) -> None:
        """Metrikleri güncelle"""
        self.metrics['total_requests'] += 1
        self.metrics['total_duration'] += duration
        
        # Her saat başı metrikleri sıfırla
        if time.time() - self.last_reset > 3600:
            self.metrics.clear()
            self.last_reset = time.time()
            
    def get_metrics(self) -> Dict[str, Any]:
        """Mevcut metrikleri döndür"""
        metrics = dict(self.metrics)
        if metrics['total_requests'] > 0:
            metrics['avg_duration'] = (
                metrics['total_duration'] / metrics['total_requests']
            )
        return metrics
        
    def save_state(self, filepath: str) -> None:
        """Router durumunu kaydet"""
        state = {
            'handler_descriptions': self.handler_descriptions,
            'handler_embeddings': {
                k: v.tolist() for k, v in self.handler_embeddings.items()
            },
            'metrics': dict(self.metrics)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            
    def load_state(self, filepath: str) -> None:
        """Router durumunu yükle"""
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)
            
        self.handler_descriptions = state['handler_descriptions']
        self.handler_embeddings = {
            k: np.array(v) for k, v in state['handler_embeddings'].items()
        }
        self.metrics = defaultdict(int, state['metrics']) 