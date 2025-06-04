# Backup al
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "performance_analysis.py" "performance_analysis.py.backup_$timestamp"

# Dosyayı oku
$content = Get-Content "performance_analysis.py" -Raw

# Test et - değiştirilecek satırları göster
Write-Host "`n🔍 Değiştirilecek satırlar:" -ForegroundColor Yellow
$matches = Select-String -Path "performance_analysis.py" -Pattern "ai_status\['openai'\]|ai_status\['ollama'\]|query_openai|query_ollama"
$matches | ForEach-Object {
    Write-Host "Line $($_.LineNumber): $($_.Line.Trim())" -ForegroundColor Gray
}

Write-Host "`n⚠️ Devam etmek istiyor musunuz? (Y/N)" -ForegroundColor Cyan
$confirm = Read-Host

if ($confirm -eq 'Y' -or $confirm -eq 'y') {
    # Manuel olarak önemli bölümleri değiştirmek daha güvenli
    Write-Host "`n✅ Lütfen yukarıdaki değişiklikleri manuel olarak yapın." -ForegroundColor Green
    Write-Host "📁 Backup dosyası: performance_analysis.py.backup_$timestamp" -ForegroundColor Yellow
}
