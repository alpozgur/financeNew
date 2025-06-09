from interactive_qa_dual_ai import DualAITefasQA

all_test_questions = [
    # (Buraya yukarıdaki listeden tüm soruları ekle, birkaç örnek aşağıda)
    "AKB fonunun son 1 yıl performansı nedir?",
    "Son 30 günde en çok kazandıran 5 fon nedir?",
    "Sharpe oranı en yüksek 10 fon?",
    "En güvenli fonları sıralar mısın?",
    "2025 portföy önerin nedir?",
    "Teknoloji fonlarını listeler misin?",
    "Garanti Portföy ile Ak Portföy’ü karşılaştır",
    "Faiz artarsa hangi fonlar etkilenir?",
    "15 yıl sonra emeklilik için portföy önerisi",
    "Aylık 2000 TL yatırırsam 8 yılda ne kadar birikir?",
    "Altın fonları önerir misin?",
    "Son 5 yılda istikrarlı fonlar hangileri?",
    "akb fonunu analiz et",
    "xyzxyz fonu hakkında bilgi",
    # Tüm diğer varyasyonlar buraya ekle!
    # ...
]

qa = DualAITefasQA()

with open("qa_test_results.txt", "w", encoding="utf-8") as f:
    for idx, question in enumerate(all_test_questions, 1):
        f.write(f"\n\n--- TEST {idx}/{len(all_test_questions)} ---\n")
        f.write(f"Soru: {question}\n")
        try:
            answer = qa.answer_question(question)
            # İstersen sadece ilk 2000 karakteri yaz, yoksa tam cevabı kaydet
            f.write(f"Cevap:\n{answer[:2000]}\n")
        except Exception as e:
            f.write(f"❌ Hata: {e}\n")

print("Testler tamamlandı! Sonuçlar qa_test_results.txt dosyasına kaydedildi.")
