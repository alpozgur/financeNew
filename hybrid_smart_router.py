# hybrid_smart_router.py
"""
Hybrid AI Smart Router - Pattern + SBERT + LLM fallback
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# SBERT optional - comment out if not installed
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    print("⚠️ SBERT not available. Using pattern matching only.")

@dataclass
class HybridRouteMatch:
    """Hybrid routing sonucu"""
    handler: str
    method: str
    confidence: float
    reasoning: str
    match_type: str  # 'pattern', 'keyword', 'sbert', 'llm'

class HybridSmartRouter:
    """Pattern, SBERT ve LLM fallback ile akıllı yönlendirme"""
    
    def __init__(self, registry, ai_provider=None, use_sbert=True, sbert_model="paraphrase-multilingual-MiniLM-L12-v2"):
        self.registry = registry
        self.ai_provider = ai_provider
        self.use_sbert = use_sbert and SBERT_AVAILABLE
        
        # SBERT initialization
        if self.use_sbert:
            print("🧠 SBERT yükleniyor...")
            self.sbert = SentenceTransformer(sbert_model)
            self._initialize_embeddings()
        else:
            self.sbert = None
            self.example_embeddings = None
            self.example_mapping = []
    
    def _initialize_embeddings(self):
        """Tüm örnekleri encode et"""
        self.example_mapping = []
        all_examples = []
        
        for handler_name, info in self.registry.registry.items():
            for example in info['examples']:
                all_examples.append(example)
                self.example_mapping.append((handler_name, example))
        
        if all_examples:
            print(f"📊 {len(all_examples)} örnek encode ediliyor...")
            self.example_embeddings = self.sbert.encode(all_examples, convert_to_tensor=True)
        else:
            self.example_embeddings = None
    
    def route(self, question: str, threshold: float = 0.5) -> Optional[HybridRouteMatch]:
        """Tek bir en iyi route döndür"""
        routes = self.route_multi(question, max_routes=1, threshold=threshold)
        return routes[0] if routes else None
    
    def route_multi(self, question: str, max_routes: int = 3, threshold: float = 0.5) -> List[HybridRouteMatch]:
        """Birden fazla olası route döndür"""
        routes = []
        question_lower = question.lower()
        
        # 1. Pattern-based routing (en yüksek öncelik)
        pattern_match = self.registry.get_handler_for_pattern(question_lower)
        if pattern_match and pattern_match[2] >= threshold:
            handler, method, score = pattern_match
            routes.append(HybridRouteMatch(
                handler=handler,
                method=method,
                confidence=score,
                reasoning="Pattern match",
                match_type="pattern"
            ))
            
            # Eğer pattern match çok güçlüyse (>0.9), direk döndür
            if score > 0.9:
                return routes[:max_routes]
        
        # 2. SBERT similarity (varsa)
        if self.use_sbert and self.example_embeddings is not None:
            sbert_matches = self._sbert_route(question, top_k=3)
            for handler, method, score, example in sbert_matches:
                if score >= threshold:
                    routes.append(HybridRouteMatch(
                        handler=handler,
                        method=method,
                        confidence=score,
                        reasoning=f"Similar to: {example}",
                        match_type="sbert"
                    ))
        
        # 3. Remove duplicates and sort
        unique_routes = self._deduplicate_routes(routes)
        unique_routes.sort(key=lambda x: x.confidence, reverse=True)
        
        # 4. LLM fallback (eğer yeterli sonuç yoksa)
        if len(unique_routes) < max_routes and self.ai_provider:
            llm_routes = self._llm_route(question, exclude_handlers=[r.handler for r in unique_routes])
            unique_routes.extend(llm_routes)
        
        return unique_routes[:max_routes]
    
    def _sbert_route(self, question: str, top_k: int = 3) -> List[Tuple[str, str, float, str]]:
        """SBERT ile benzer örnekleri bul"""
        if not self.use_sbert or self.example_embeddings is None:
            return []
        
        # Encode question
        q_embedding = self.sbert.encode(question, convert_to_tensor=True)
        
        # Calculate similarities
        similarities = st_util.cos_sim(q_embedding, self.example_embeddings)[0]
        
        # Get top-k matches
        top_indices = similarities.argsort(descending=True)[:top_k]
        
        results = []
        for idx in top_indices:
            idx = int(idx)
            score = float(similarities[idx])
            handler_name, example = self.example_mapping[idx]
            
            # Method'u belirle
            handler_info = self.registry.registry.get(handler_name, {})
            method = self._find_method_for_question(question, handler_info.get('methods', {}))
            
            results.append((handler_name, method, score, example))
        
        return results
    
    def _llm_route(self, question: str, exclude_handlers: List[str] = None) -> List[HybridRouteMatch]:
        """LLM ile route belirleme"""
        if not self.ai_provider:
            return []
        
        prompt = self._build_llm_routing_prompt(question, exclude_handlers)
        
        try:
            response = self.ai_provider.query(prompt, "Sen bir soru yönlendirme uzmanısın.")
            
            # Parse LLM response
            routes = self._parse_llm_response(response, question)
            return routes
            
        except Exception as e:
            print(f"⚠️ LLM routing hatası: {e}")
            return []
    
    def _build_llm_routing_prompt(self, question: str, exclude_handlers: List[str] = None) -> str:
        """LLM için routing prompt'u oluştur"""
        exclude_handlers = exclude_handlers or []
        
        prompt = f"""Aşağıdaki soruyu en uygun handler'a yönlendir.

Soru: "{question}"

Mevcut handler'lar ve yetenekleri:
"""
        
        for name, info in self.registry.registry.items():
            if name in exclude_handlers:
                continue
                
            examples = info['examples'][:3]  # İlk 3 örnek
            keywords = info['keywords'][:5]  # İlk 5 keyword
            
            prompt += f"\n{name}:"
            if examples:
                prompt += f"\n  Örnekler: {', '.join(examples)}"
            if keywords:
                prompt += f"\n  Anahtar kelimeler: {', '.join(keywords)}"
        
        prompt += """

Lütfen en uygun handler'ı ve method'u belirle. Yanıtını şu formatta ver:
handler: handler_adı
method: method_adı
confidence: 0.0-1.0 arası güven skoru
reasoning: kısa açıklama
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, question: str) -> List[HybridRouteMatch]:
        """LLM yanıtını parse et"""
        routes = []
        
        try:
            # Basit parsing
            lines = response.strip().split('\n')
            handler = None
            method = None
            confidence = 0.7
            reasoning = "LLM suggestion"
            
            for line in lines:
                if line.startswith('handler:'):
                    handler = line.split(':', 1)[1].strip()
                elif line.startswith('method:'):
                    method = line.split(':', 1)[1].strip()
                elif line.startswith('confidence:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except:
                        confidence = 0.7
                elif line.startswith('reasoning:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            if handler and method:
                routes.append(HybridRouteMatch(
                    handler=handler,
                    method=method,
                    confidence=confidence,
                    reasoning=reasoning,
                    match_type="llm"
                ))
        
        except Exception as e:
            print(f"⚠️ LLM response parsing hatası: {e}")
        
        return routes
    
    def _find_method_for_question(self, question: str, methods: Dict[str, List[str]]) -> str:
        """Soru için en uygun method'u bul"""
        if not methods:
            return 'analyze'
        
        question_lower = question.lower()
        
        for method_name, patterns in methods.items():
            for pattern in patterns:
                if pattern.lower() in question_lower:
                    return method_name
        
        # Default: ilk method
        return list(methods.keys())[0] if methods else 'analyze'
    
    def _deduplicate_routes(self, routes: List[HybridRouteMatch]) -> List[HybridRouteMatch]:
        """Duplicate route'ları kaldır"""
        seen = set()
        unique = []
        
        for route in routes:
            key = (route.handler, route.method)
            if key not in seen:
                seen.add(key)
                unique.append(route)
        
        return unique