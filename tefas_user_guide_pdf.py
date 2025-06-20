#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEFAS Kullanıcı Kılavuzu - HTML Versiyonu
Türkçe karakter sorunu yaşayanlar için alternatif
"""

import os
from datetime import datetime

def create_html_guide():
    """HTML formatında kullanıcı kılavuzu oluştur"""
    
    html_content = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TEFAS Fon Analiz Sistemi - Kullanıcı Kılavuzu</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            background-color: white;
            padding: 40px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 10px;
        }
        
        h1 {
            color: #1a237e;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        
        h2 {
            color: #1976d2;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        h3 {
            color: #424242;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        
        h4 {
            color: #616161;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        .toc {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0;
        }
        
        .toc h2 {
            margin-top: 0;
            color: #1976d2;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc li {
            margin: 10px 0;
        }
        
        .toc a {
            text-decoration: none;
            color: #1976d2;
            font-weight: 500;
        }
        
        .toc a:hover {
            text-decoration: underline;
        }
        
        .code-block {
            background-color: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
        }
        
        .feature-box {
            background-color: #e3f2fd;
            border-left: 4px solid #1976d2;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        
        .warning-box {
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        
        .success-box {
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        
        ul {
            margin: 15px 0;
            padding-left: 30px;
        }
        
        li {
            margin: 8px 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            border: 1px solid #e0e0e0;
            padding: 12px;
            text-align: left;
        }
        
        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        
        .print-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #1976d2;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        .print-button:hover {
            background-color: #1565c0;
        }
        
        @media print {
            body {
                background-color: white;
            }
            .container {
                box-shadow: none;
                padding: 20px;
            }
            .print-button {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>TEFAS FON ANALİZ SİSTEMİ<br>KULLANICI KILAVUZU</h1>
        
        <div style="text-align: center; margin: 30px 0;">
            <p><strong>Versiyon:</strong> 2.0</p>
            <p><strong>Tarih:</strong> """ + datetime.now().strftime('%d.%m.%Y') + """</p>
        </div>
        
        <div class="toc">
            <h2>İÇİNDEKİLER</h2>
            <ul>
                <li><a href="#section1">1. Sistem Hakkında</a></li>
                <li><a href="#section2">2. Temel Özellikler</a></li>
                <li><a href="#section3">3. Soru Kategorileri ve Örnekler</a></li>
                <li><a href="#section4">4. Detaylı Kullanım Örnekleri</a></li>
                <li><a href="#section5">5. İpuçları ve Püf Noktaları</a></li>
                <li><a href="#section6">6. Önemli Uyarılar</a></li>
            </ul>
        </div>
        
        <h2 id="section1">1. Sistem Hakkında</h2>
        <p>TEFAS Fon Analiz Sistemi, Türkiye Elektronik Fon Alım Satım Platformu'ndaki (TEFAS) yatırım fonlarını analiz eden, yapay zeka destekli kapsamlı bir finansal analiz platformudur.</p>
        
        <div class="feature-box">
            <h3>Ana Özellikler:</h3>
            <ul>
                <li>1700+ TEFAS fonunun gerçek zamanlı analizi</li>
                <li>Dual AI desteği (OpenAI + Ollama)</li>
                <li>Teknik, fundamental ve makroekonomik analizler</li>
                <li>Kişiselleştirilmiş yatırım önerileri</li>
                <li>Senaryo bazlı risk analizi</li>
            </ul>
        </div>
        
        <h2 id="section2">2. Temel Özellikler</h2>
        
        <h3>2.1. Performans Analizi</h3>
        <ul>
            <li>Fon getiri hesaplamaları</li>
            <li>Risk metrikleri (Sharpe, Sortino, Calmar)</li>
            <li>Volatilite ve maksimum düşüş analizleri</li>
        </ul>
        
        <h3>2.2. Teknik Analiz</h3>
        <ul>
            <li>MACD, RSI, Bollinger Bantları</li>
            <li>Hareketli ortalamalar (SMA, EMA)</li>
            <li>Alım/satım sinyalleri</li>
        </ul>
        
        <h3>2.3. Portföy Yönetimi</h3>
        <ul>
            <li>Optimal portföy dağılımı</li>
            <li>Risk-getiri optimizasyonu</li>
            <li>Şirket bazlı analizler</li>
        </ul>
        
        <h3>2.4. Makroekonomik Analiz</h3>
        <ul>
            <li>Faiz değişimi etkileri</li>
            <li>Enflasyon senaryoları</li>
            <li>Döviz kuru analizleri</li>
        </ul>
        
        <h3>2.5. Kişisel Finans Planlama</h3>
        <ul>
            <li>Emeklilik planlaması</li>
            <li>Eğitim birikimleri</li>
            <li>Ev alma stratejileri</li>
        </ul>
        
        <h2 id="section3">3. Soru Kategorileri ve Örnekler</h2>
        
        <h3>3.1. Fon Analizi ve Öneriler</h3>
        
        <h4>Genel Öneri Soruları:</h4>
        <div class="code-block">
            "2025 yılı için hangi fonları önerirsin?"<br>
            "100000 TL ile hangi fonlara yatırım yapmalıyım?"<br>
            "En iyi performans gösteren 10 fon hangileri?"
        </div>
        
        <h4>Spesifik Fon Analizi:</h4>
        <div class="code-block">
            "AKB fonunu analiz et"<br>
            "TI2 fonunun son 1 yıl performansı nasıl?"<br>
            "GAF fonu hakkında detaylı bilgi ver"
        </div>
        
        <h3>3.2. Teknik Analiz Soruları</h3>
        
        <h4>Teknik İndikatörler:</h4>
        <div class="code-block">
            "MACD sinyali pozitif olan fonlar"<br>
            "RSI 30 altında olan fonları göster"<br>
            "Bollinger alt bandına yakın fonlar"<br>
            "Golden cross veren fonları listele"
        </div>
        
        <h3>3.3. Risk ve Güvenlik Analizi</h3>
        
        <h4>Risk Soruları:</h4>
        <div class="code-block">
            "En güvenli 10 fon hangileri?"<br>
            "En riskli fonları göster"<br>
            "Volatilitesi %10 altında olan fonlar"<br>
            "Beta katsayısı 1'den düşük fonlar"
        </div>
        
        <h3>3.4. Karşılaştırmalar</h3>
        
        <h4>Fon Karşılaştırması:</h4>
        <div class="code-block">
            "AKB ve YAS fonlarını karşılaştır"<br>
            "TI2 vs GAF analizi yap"
        </div>
        
        <h4>Şirket Karşılaştırması:</h4>
        <div class="code-block">
            "İş Portföy vs Ak Portföy karşılaştırması"<br>
            "En başarılı portföy yönetim şirketi hangisi?"
        </div>
        
        <h3>3.5. Döviz ve Enflasyon</h3>
        
        <h4>Döviz Fonları:</h4>
        <div class="code-block">
            "Dolar bazlı fonlar hangileri?"<br>
            "Euro fonları performansı"<br>
            "Döviz korumalı fonlar"
        </div>
        
        <h4>Enflasyon Koruması:</h4>
        <div class="code-block">
            "Enflasyon korumalı fonlar"<br>
            "Altın fonları analizi"<br>
            "TÜFE'ye endeksli fonlar"
        </div>
        
        <h2 id="section4">4. Detaylı Kullanım Örnekleri</h2>
        
        <h3>Örnek 1: Yeni Başlayan Yatırımcı</h3>
        <div class="code-block">
            Soru: "Yatırıma yeni başlıyorum, 50000 TL var, ne önerirsin?"
        </div>
        
        <div class="success-box">
            <strong>Sistem şunları yapacak:</strong>
            <ul>
                <li>Risk profilinizi değerlendirir</li>
                <li>Güvenli ve dengeli fonları önerir</li>
                <li>Çeşitlendirme için 3-5 fon seçer</li>
                <li>Her fonun risk/getiri analizini yapar</li>
                <li>Aylık takip stratejisi sunar</li>
            </ul>
        </div>
        
        <h3>Örnek 2: Emeklilik Planlama</h3>
        <div class="code-block">
            Soru: "15 yıl sonra emeklilik için aylık 3000 TL ayırabilirim"
        </div>
        
        <div class="success-box">
            <strong>Sistem şunları yapacak:</strong>
            <ul>
                <li>Yaş bazlı risk profili belirler</li>
                <li>Uzun vadeli büyüme fonları önerir</li>
                <li>Monte Carlo simülasyonu ile tahmin yapar</li>
                <li>Enflasyon etkisini hesaplar</li>
                <li>Yıllık revizyon stratejisi sunar</li>
            </ul>
        </div>
        
        <h2 id="section5">5. İpuçları ve Püf Noktaları</h2>
        
        <h3>1. Net Sorular Sorun</h3>
        <table>
            <tr>
                <th>✅ Doğru</th>
                <th>❌ Yanlış</th>
            </tr>
            <tr>
                <td>"Volatilitesi %15 altında olan fonlar"</td>
                <td>"İyi fonlar hangileri?"</td>
            </tr>
        </table>
        
        <h3>2. Tutarları Belirtin</h3>
        <table>
            <tr>
                <th>✅ Doğru</th>
                <th>❌ Yanlış</th>
            </tr>
            <tr>
                <td>"100000 TL ile portföy önerisi"</td>
                <td>"Yatırım yapmak istiyorum"</td>
            </tr>
        </table>
        
        <h3>3. Süreleri Ekleyin</h3>
        <table>
            <tr>
                <th>✅ Doğru</th>
                <th>❌ Yanlış</th>
            </tr>
            <tr>
                <td>"5 yıl için uzun vadeli fonlar"</td>
                <td>"Uzun vadeli fonlar"</td>
            </tr>
        </table>
        
        <h2 id="section6">6. Önemli Uyarılar</h2>
        
        <div class="warning-box">
            <h3>⚠️ Dikkat Edilmesi Gerekenler:</h3>
            <ol>
                <li><strong>Yatırım Tavsiyesi Değildir:</strong> Sistem bilgilendirme amaçlıdır, kesin yatırım tavsiyesi değildir.</li>
                <li><strong>Geçmiş Performans:</strong> Geçmiş getiriler gelecek performansı garanti etmez.</li>
                <li><strong>Risk Yönetimi:</strong> Her yatırımın riski vardır, çeşitlendirme yapın.</li>
                <li><strong>Güncel Veri:</strong> Veriler anlık olmayabilir, önemli kararlar öncesi doğrulayın.</li>
                <li><strong>Profesyonel Danışmanlık:</strong> Büyük yatırımlar için profesyonel danışman görüşü alın.</li>
            </ol>
        </div>
        
        <div class="feature-box">
            <h3>📞 Destek</h3>
            <p>Sorularınız için:</p>
            <ul>
                <li>Sisteme "yardım" yazarak genel bilgi alabilirsiniz</li>
                <li>Spesifik özellikler için örnek sorular sorabilirsiniz</li>
                <li>Hata durumlarında soruyu farklı şekilde ifade edin</li>
            </ul>
        </div>
        
        <hr style="margin: 50px 0;">
        
        <p style="text-align: center; color: #666; font-style: italic;">
            Bu kılavuz TEFAS Fon Analiz Sistemi'nin temel kullanımını kapsar.<br>
            Sistem sürekli geliştirilmektedir ve yeni özellikler eklenebilir.
        </p>
    </div>
    
    <button class="print-button" onclick="window.print()">
        📄 PDF Olarak Kaydet
    </button>
</body>
</html>"""
    
    # HTML dosyasını oluştur
    filename = "TEFAS_Kullanici_Kilavuzu.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML dosyası başarıyla oluşturuldu: {filename}")
    print(f"📄 Dosya boyutu: {os.path.getsize(filename) / 1024:.1f} KB")
    print("\n📌 Kullanım:")
    print("1. Dosyayı tarayıcınızda açın")
    print("2. PDF olarak kaydetmek için 'PDF Olarak Kaydet' butonuna tıklayın")
    print("3. Veya Ctrl+P (Cmd+P Mac'te) ile yazdırma menüsünden PDF'e dönüştürün")

if __name__ == "__main__":
    create_html_guide()