# analysis/hybrid_fund_selector.py
"""
Hibrit Fon Seçim Sistemi - Hızlı + Kapsamlı + Performans Optimizasyonu
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from database.connection import DatabaseManager
from config.config import Config

class HybridFundSelector:
    """Hibrit fon seçim ve analiz sistemi"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cache için
        self._fund_cache = {}
        self._last_cache_update = None
        
    def load_funds_hybrid(self, 
                         quick_sample=150,      # Hızlı örnekleme
                         detailed_analysis=30,   # Detaylı analiz
                         include_top=True,       # Büyük fonları dahil et
                         use_cache=True) -> Tuple[List[str], List[str]]:
        """
        Hibrit yaklaşım: Hızlı örnekleme + Büyük fonlar + Detaylı analiz
        
        Returns:
            Tuple[aktif_fonlar, analiz_fonları]
        """
        
        print(f"🎯 Hibrit Fon Seçim Sistemi Başlatılıyor...")
        start_time = time.time()
        
        try:
            # 1. TÜM FONLARI AL
            all_funds = self.db.get_all_fund_codes()
            print(f"📊 Toplam {len(all_funds)} fon bulundu")
            
            # 2. BÜYÜK FONLARI BELİRLE (Öncelikli)
            top_funds = []
            if include_top:
                print("💰 En büyük fonlar belirleniyor...")
                top_funds = self._get_top_funds_by_size(50)
                print(f"   📈 {len(top_funds)} büyük fon belirlendi")
            
            # 3. STRATİFİED SAMPLİNG (Temsili örnekleme)
            print("🎲 Temsili örnekleme yapılıyor...")
            representative_sample = self._stratified_sampling(all_funds, quick_sample)
            print(f"   📊 {len(representative_sample)} temsili fon seçildi")
            
            # 4. FONLARI BİRLEŞTİR
            combined_funds = list(set(top_funds + representative_sample))
            print(f"🔗 Toplam {len(combined_funds)} fon birleştirildi")
            
            # 5. AKTİFLİK KONTROLÜ (Paralel)
            print("⚡ Paralel aktiflik kontrolü...")
            active_funds = self._check_funds_activity_parallel(combined_funds)
            print(f"✅ {len(active_funds)} aktif fon bulundu")
            
            # 6. DETAYLI ANALİZ İÇİN SEÇIM
            analysis_funds = self._select_analysis_funds(active_funds, detailed_analysis)
            print(f"🔍 {len(analysis_funds)} fon detaylı analize seçildi")
            
            elapsed = time.time() - start_time
            print(f"⏱️ Hibrit seçim tamamlandı: {elapsed:.1f} saniye")
            
            return active_funds, analysis_funds
            
        except Exception as e:
            self.logger.error(f"Hibrit seçim hatası: {e}")
            # Fallback: İlk 50 fon
            fallback_funds = all_funds[:50] if 'all_funds' in locals() else []
            return fallback_funds, fallback_funds[:20]
    
    def _get_top_funds_by_size(self, top_n: int = 50) -> List[str]:
        """En büyük fonları bul (fon büyüklüğüne göre)"""
        try:
            query = """
            SELECT fcode, AVG(fcapacity) as avg_size, COUNT(*) as data_count
            FROM tefasfunds 
            WHERE pdate >= CURRENT_DATE - INTERVAL '30 days'
            AND fcapacity > 1000000  -- 1M TL üstü
            GROUP BY fcode
            HAVING COUNT(*) >= 10     -- En az 10 gün veri
            ORDER BY avg_size DESC
            LIMIT %s
            """
            
            result = self.db.execute_query(query.replace('%s', str(top_n)))
            
            if not result.empty:
                return result['fcode'].tolist()
            else:
                return []
                
        except Exception as e:
            self.logger.warning(f"Büyük fon sorgusu hatası: {e}")
            return []
    
    def _stratified_sampling(self, all_funds: List[str], sample_size: int) -> List[str]:
        """Stratified sampling - Her harf grubundan temsili seçim"""
        try:
            # Fonları ilk harflerine göre grupla
            grouped_funds = {}
            for fund in all_funds:
                first_letter = fund[0] if fund else 'Z'
                if first_letter not in grouped_funds:
                    grouped_funds[first_letter] = []
                grouped_funds[first_letter].append(fund)
            
            # Her gruptan proporsiyonel seçim
            selected_funds = []
            random.seed(42)  # Tutarlı sonuçlar için
            
            total_groups = len(grouped_funds)
            base_sample_per_group = sample_size // total_groups
            
            for letter, funds in grouped_funds.items():
                # Her gruptan en az 1, en fazla grup fonlarının %50'si
                group_sample_size = min(
                    len(funds), 
                    max(1, min(base_sample_per_group, len(funds) // 2))
                )
                
                # Rastgele seçim
                group_sample = random.sample(funds, group_sample_size)
                selected_funds.extend(group_sample)
            
            return selected_funds[:sample_size]  # İstenen boyutta kes
            
        except Exception as e:
            self.logger.warning(f"Stratified sampling hatası: {e}")
            # Fallback: Random sampling
            return random.sample(all_funds, min(sample_size, len(all_funds)))
    
    def _check_funds_activity_parallel(self, funds: List[str], max_workers: int = 8) -> List[str]:
        """Paralel aktiflik kontrolü - ÇOK HIZLI"""
        active_funds = []
        
        def check_single_fund(fcode: str) -> Optional[str]:
            """Tek fon aktiflik kontrolü"""
            try:
                # Hızlı sorgu - sadece son 5 kayıt
                data = self.db.get_fund_price_history(fcode, 5)
                
                if not data.empty:
                    last_date = pd.to_datetime(data['pdate'].max())
                    days_ago = (datetime.now() - last_date).days
                    
                    if days_ago < 60:  # Son 60 günde aktif
                        return fcode
                
                return None
                
            except Exception:
                return None
        
        # Paralel işleme
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Tüm işleri başlat
            future_to_fund = {
                executor.submit(check_single_fund, fcode): fcode 
                for fcode in funds
            }
            
            # Sonuçları topla
            for future in as_completed(future_to_fund):
                result = future.result()
                if result:
                    active_funds.append(result)
        
        return active_funds
    
    def _select_analysis_funds(self, active_funds: List[str], count: int) -> List[str]:
        """Detaylı analiz için en iyi fonları seç"""
        if len(active_funds) <= count:
            return active_funds
        
        try:
            # Hızlı ön değerlendirme ile en promising fonları seç
            fund_scores = []
            
            for fcode in active_funds[:min(100, len(active_funds))]:  # Max 100 fon hızlı test
                try:
                    # Çok hızlı metrik - sadece son 10 gün
                    data = self.db.get_fund_price_history(fcode, 10)
                    
                    if len(data) >= 5:
                        prices = data['price']
                        recent_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                        volatility = prices.std() / prices.mean() * 100
                        
                        # Basit skor: getiri/risk oranı
                        score = recent_return / max(volatility, 1) if volatility > 0 else recent_return
                        
                        fund_scores.append({
                            'fcode': fcode,
                            'score': score,
                            'return': recent_return
                        })
                        
                except Exception:
                    continue
            
            if fund_scores:
                # En yüksek skorlu fonları seç
                df = pd.DataFrame(fund_scores)
                selected = df.nlargest(count, 'score')['fcode'].tolist()
                
                # Eksik varsa random ekle
                if len(selected) < count:
                    remaining = [f for f in active_funds if f not in selected]
                    additional = random.sample(remaining, min(count - len(selected), len(remaining)))
                    selected.extend(additional)
                
                return selected
            else:
                # Fallback: İlk N fonu
                return active_funds[:count]
                
        except Exception as e:
            self.logger.warning(f"Analiz fonu seçimi hatası: {e}")
            return active_funds[:count]

# PERFORMANS OPTİMİZASYONU İÇİN GELİŞMİŞ SİSTEM

class HighPerformanceFundAnalyzer:
    """Yüksek performanslı fon analiz sistemi - TÜM FONLAR için"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def analyze_all_funds_optimized(self, 
                                   batch_size: int = 100,
                                   max_workers: int = 16,
                                   use_bulk_queries: bool = True,
                                   cache_results: bool = True) -> Dict:
        """
        TÜM FONLAR için optimize edilmiş analiz
        
        Hızlandırma Teknikleri:
        1. Bulk SQL sorguları
        2. Paralel işleme
        3. Vectorized hesaplamalar
        4. Intelligent caching
        5. Memory-efficient processing
        """
        
        print("🚀 HIGH-PERFORMANCE ANALYSIS BAŞLATIYOR...")
        print("="*50)
        
        start_time = time.time()
        
        # 1. BULK VERİ ÇEKİMİ
        print("📊 1. Bulk veri çekimi...")
        all_fund_data = self._bulk_fetch_fund_data()
        print(f"   ✅ {len(all_fund_data)} fon verisi yüklendi")
        
        # 2. VECTORİZED HESAPLAMALAR
        print("⚡ 2. Vectorized hesaplamalar...")
        performance_metrics = self._vectorized_calculations(all_fund_data)
        print(f"   ✅ {len(performance_metrics)} fon hesaplandı")
        
        # 3. PARALEL ANALİZ
        print("🔄 3. Paralel detay analizi...")
        detailed_results = self._parallel_detailed_analysis(
            performance_metrics, max_workers=max_workers
        )
        print(f"   ✅ {len(detailed_results)} detaylı analiz")
        
        # 4. SONUÇLARI BİRLEŞTİR
        print("🔗 4. Sonuçları birleştir...")
        final_results = self._combine_results(performance_metrics, detailed_results)
        
        elapsed = time.time() - start_time
        print(f"⏱️ TOPLAM SÜRE: {elapsed:.1f} saniye")
        print(f"📊 SANIYE BAŞINA: {len(final_results)/elapsed:.1f} fon/saniye")
        
        return final_results
    
    def _bulk_fetch_fund_data(self) -> Dict:
        """Bulk SQL ile tüm fon verilerini çek"""
        try:
            # TEK SORGU ile son 60 günün tüm verisi
            query = """
            WITH recent_data AS (
                SELECT fcode, pdate, price,
                       ROW_NUMBER() OVER (PARTITION BY fcode ORDER BY pdate DESC) as rn
                FROM tefasfunds 
                WHERE pdate >= CURRENT_DATE - INTERVAL '90 days'
                AND price > 0
            )
            SELECT fcode, pdate, price
            FROM recent_data 
            WHERE rn <= 60  -- Son 60 kayıt
            ORDER BY fcode, pdate DESC
            """
            
            print("   📡 Bulk SQL sorgusu çalıştırılıyor...")
            all_data = self.db.execute_query(query)
            
            # Fon bazında grupla
            fund_data = {}
            for fcode, group in all_data.groupby('fcode'):
                if len(group) >= 10:  # En az 10 gün veri
                    fund_data[fcode] = group.sort_values('pdate')
            
            return fund_data
            
        except Exception as e:
            self.logger.error(f"Bulk fetch hatası: {e}")
            return {}
    
    def _vectorized_calculations(self, fund_data: Dict) -> pd.DataFrame:
        """Vectorized NumPy hesaplamaları - ÇOK HIZLI"""
        
        metrics_list = []
        
        for fcode, data in fund_data.items():
            try:
                prices = data['price'].values
                
                if len(prices) < 5:
                    continue
                
                # Vectorized hesaplamalar
                returns = np.diff(prices) / prices[:-1]
                
                # Temel metrikler
                total_return = (prices[-1] / prices[0] - 1) * 100
                annual_return = total_return * (252 / len(prices))
                volatility = np.std(returns) * np.sqrt(252) * 100
                sharpe = (annual_return - 15) / volatility if volatility > 0 else 0
                win_rate = np.sum(returns > 0) / len(returns) * 100
                
                # Max drawdown (vectorized)
                cumulative = np.cumprod(1 + returns)
                running_max = np.maximum.accumulate(cumulative)
                drawdowns = (cumulative - running_max) / running_max
                max_drawdown = np.min(drawdowns) * 100
                
                metrics_list.append({
                    'fcode': fcode,
                    'current_price': prices[-1],
                    'total_return': total_return,
                    'annual_return': annual_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe,
                    'win_rate': win_rate,
                    'max_drawdown': max_drawdown,
                    'data_points': len(prices)
                })
                
            except Exception:
                continue
        
        return pd.DataFrame(metrics_list)
    
    def _parallel_detailed_analysis(self, metrics_df: pd.DataFrame, max_workers: int = 16) -> Dict:
        """Paralel detaylı analiz"""
        
        def analyze_single_fund(row):
            """Tek fon için detaylı analiz"""
            try:
                fcode = row['fcode']
                
                # 2025 skoru hesapla
                score = self._calculate_2025_score_optimized(
                    row['annual_return'], 
                    row['volatility'], 
                    row['sharpe_ratio'], 
                    row['win_rate']
                )
                
                return {
                    'fcode': fcode,
                    'score_2025': score,
                    'category': self._get_score_category(score),
                    'recommendation': self._get_recommendation(score)
                }
                
            except Exception:
                return None
        
        detailed_results = {}
        
        # Paralel işleme
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(analyze_single_fund, row) 
                for _, row in metrics_df.iterrows()
            ]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    detailed_results[result['fcode']] = result
        
        return detailed_results
    
    def _calculate_2025_score_optimized(self, annual_return, volatility, sharpe, win_rate):
        """Optimize edilmiş skor hesaplama"""
        # Vectorized hesaplama
        return_score = np.clip(annual_return / 30 * 30, 0, 30)
        sharpe_score = np.clip(sharpe * 10, 0, 25)
        risk_score = np.clip(20 - np.abs(volatility - 20) / 2, 0, 25)
        consistency_score = np.clip(win_rate / 5, 0, 20)
        
        return return_score + sharpe_score + risk_score + consistency_score
    
    def _get_score_category(self, score):
        """Skor kategorisi"""
        if score >= 80: return "Mükemmel"
        elif score >= 70: return "Çok İyi"
        elif score >= 60: return "İyi"
        elif score >= 50: return "Orta"
        else: return "Zayıf"
    
    def _get_recommendation(self, score):
        """Yatırım önerisi"""
        if score >= 80: return "Güçlü Alım"
        elif score >= 70: return "Alım"
        elif score >= 50: return "Bekle"
        else: return "Sat"
    
    def _combine_results(self, metrics_df: pd.DataFrame, detailed_results: Dict) -> pd.DataFrame:
        """Sonuçları birleştir"""
        
        # Detailed results'ı DataFrame'e çevir
        detailed_df = pd.DataFrame(list(detailed_results.values()))
        
        # Birleştir
        if not detailed_df.empty:
            final_df = metrics_df.merge(detailed_df, on='fcode', how='inner')
        else:
            final_df = metrics_df.copy()
            final_df['score_2025'] = 50  # Default score
        
        # Skorlara göre sırala
        final_df = final_df.sort_values('score_2025', ascending=False)
        
        return final_df

# HIZLANDIRMA STRATEJİLERİ REHBERİ

def print_optimization_guide():
    """Kapsamlı analiz için hızlandırma stratejileri"""
    
    guide = """
🚀 KAPSAMLI ANALİZ HIZLANDIRMA STRATEJİLERİ
==========================================

📊 1. VERİTABANI OPTİMİZASYONU:
   • PostgreSQL indeksleri:
     CREATE INDEX idx_tefasfunds_fcode_pdate ON tefasfunds(fcode, pdate);
     CREATE INDEX idx_tefasfunds_recent ON tefasfunds(pdate) WHERE pdate >= CURRENT_DATE - INTERVAL '90 days';
   
   • Connection pooling (pgbouncer)
   • Bulk queries (tek sorguda tüm veri)
   • Prepared statements

⚡ 2. PARALEL İŞLEME:
   • ThreadPoolExecutor (I/O işlemleri için)
   • ProcessPoolExecutor (CPU yoğun hesaplamalar için)
   • Chunk processing (100'lük gruplar)
   • Asenkron database queries

🧮 3. VECTORİZED HESAPLAMALAR:
   • NumPy array operations
   • Pandas vectorized functions
   • Avoid Python loops
   • Broadcasting operations

💾 4. MEMORY OPTİMİZASYONU:
   • Chunked processing
   • Data type optimization (float32 vs float64)
   • Memory mapping for large datasets
   • Garbage collection tuning

🗄️ 5. CACHING STRATEJİLERİ:
   • Redis for intermediate results
   • In-memory caching for repeated calculations
   • Disk-based caching for large datasets
   • Invalidation strategies

⚙️ 6. SİSTEM OPTİMİZASYONU:
   • SSD storage for database
   • Sufficient RAM (16GB+ recommended)
   • Multi-core CPU utilization
   • Network optimization

📈 PERFORMANS BEKLENTİLERİ:
==================
Sistem Konfigürasyonu → Süre (1793 fon için):

💻 Temel Sistem (4 core, 8GB RAM):
   • Seri işleme: ~15-20 dakika
   • Paralel (hibrit): ~3-5 dakika
   • Optimize edilmiş: ~1-2 dakika

🖥️ Güçlü Sistem (8 core, 16GB+ RAM):
   • Hibrit yaklaşım: ~1-2 dakika
   • Optimize edilmiş: ~30-60 saniye
   • Çok optimize: ~15-30 saniye

🖥️ Server Sınıfı (16+ core, 32GB+ RAM):
   • Optimize edilmiş: ~10-20 saniye
   • Maximum optimization: ~5-10 saniye

💡 UYGULAMA ÖNERİLERİ:
=====================
1. Hibrit yaklaşımla başla (1-2 dakika)
2. Kullanıcı isteğinde tam analiz (5-10 dakika)
3. Günlük batch processing (gece 1-2 saat)
4. Sonuçları cache'le (tekrar hızlı)

🎯 ÖNCELİK SIRASI:
================
1. Database indeksleri ← EN ÖNEMLİ
2. Bulk SQL queries
3. Paralel processing
4. Vectorized calculations
5. Caching
6. Memory optimization
"""
    
    print(guide)

# Hibrit sistemi interactive_qa_dual_ai.py'e entegre etme
def integrate_hybrid_system():
    """Hibrit sistemi mevcut Q&A sistemine entegre et"""
    
    integration_code = '''
    # interactive_qa_dual_ai.py'de _load_active_funds metodunu değiştir:
    
    def _load_active_funds(self, max_funds=None, mode="comprehensive"):
        """
        Gelişmiş fon yükleme sistemi
        mode: "hybrid", "comprehensive", "fast"
        """
        
        if mode == "hybrid":
            # Hibrit yaklaşım (1-2 dakika)
            selector = HybridFundSelector(self.coordinator.db, self.config)
            active_funds, analysis_funds = selector.load_funds_hybrid(
                quick_sample=150,
                detailed_analysis=30,
                include_top=True
            )
            return analysis_funds  # Analiz için optimize edilmiş liste
            
        elif mode == "comprehensive":
            # Kapsamlı analiz (5-10 dakika)
            analyzer = HighPerformanceFundAnalyzer(self.coordinator.db, self.config)
            all_results = analyzer.analyze_all_funds_optimized()
            return all_results.head(50)['fcode'].tolist()  # En iyi 50
            
        else:  # fast
            # Hızlı mod (30 saniye)
            all_funds = self.coordinator.db.get_all_fund_codes()
            return all_funds[:50]  # İlk 50
    '''
    
    print("🔧 Entegrasyon Kodu:")
    print(integration_code)

if __name__ == "__main__":
    print_optimization_guide()
    print("\n" + "="*50)
    integrate_hybrid_system()