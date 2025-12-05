# KurServer CLI

Ubuntu sunucu yönetimi için kullanılan CLI aracı / Ubuntu server management CLI tool.

## Features / Özellikler

- **Web Server Management / Web Sunucu Yönetimi**
  - Nginx installation and configuration / Nginx kurulumu ve yapılandırması
  - SSL certificate management (Let's Encrypt, self-signed) / SSL sertifika yönetimi
  - Virtual host configuration / Sanal host yapılandırması
  - Performance optimization / Performans optimizasyonu

- **Database Management / Veritabanı Yönetimi**
  - MySQL/MariaDB installation and security hardening / MySQL/MariaDB kurulumu ve güvenlik güçlendirme
  - Database and user management / Veritabanı ve kullanıcı yönetimi
  - Performance tuning based on system resources / Sistem kaynaklarına dayalı performans ayarı

- **NVM and Node.js Management / NVM ve Node.js Yönetimi**
  - Node.js version management with NVM / NVM ile Node.js versiyon yönetimi
  - NPM operations with version selection / Versiyon seçimi ile NPM işlemleri
  - Support for install, build, dev, and custom commands / Install, build, dev ve özel komut desteği
  - Integration with site management / Site yönetimi ile entegrasyon

- **PHP Management / PHP Yönetimi**
  - Multi-version PHP-FPM installation (7.4, 8.0, 8.1, 8.2) / Çoklu versiyon PHP-FPM kurulumu
  - Interactive extension management / Etkileşimli uzantı yönetimi
  - OPcache configuration for performance / Performans için OPcache yapılandırması
  - Pool configuration optimization / Havuz yapılandırma optimizasyonu

- **Site Management / Site Yönetimi**
  - Automated site creation with Nginx configuration / Nginx yapılandırması ile otomatik site oluşturma
  - PHP integration with version selection / Versiyon seçimi ile PHP entegrasyonu
  - SSL setup with auto-renewal / Otomatik yenileme ile SSL kurulumu
  - Site information and status monitoring / Site bilgisi ve durum izleme

- **Deployment Solutions / Dağıtım Çözümleri**
  - GitHub integration (public and private repositories) / GitHub entegrasyonu (herkese açık ve özel depolar)
  - Manual deployment with project templates / Proje şablonları ile manuel dağıtım
  - Support for multiple frameworks (Laravel, Symfony, WordPress, Django, Flask, Node.js) / Çoklu çerçeve desteği
  - Automated dependency management (Composer, NPM) / Otomatik bağımlılık yönetimi
  - Enhanced NPM operations with Node.js version selection / Node.js versiyon seçimi ile gelişmiş NPM işlemleri

- **Configuration Management / Yapılandırma Yönetimi**
  - Configuration backup and restore / Yapılandırma yedekleme ve geri yükleme
  - Template-based configuration generation / Şablon tabanlı yapılandırma oluşturma
  - Service configuration validation / Hizmet yapılandırma doğrulama
  - System-wide configuration management / Sistem geneli yapılandırma yönetimi

## Installation / Kurulum

### From PyPI / PyPI'den

```bash
pip install kurserver
```

### From Source / Kaynak koddan

```bash
git clone https://github.com/username/kurserver.git
cd kurserver
pip install -e .
```

### Requirements / Gereksinimler

- Ubuntu 18.04 or later / Ubuntu 18.04 veya sonrası
- Python 3.8+ / Python 3.8+
- Sudo access for system operations / Sistem işlemleri için sudo erişimi

## Usage / Kullanım

### Interactive Mode / Etkileşimli Mod

```bash
kurserver
# or
kurserver interactive
```

### Command Line Mode / Komut Satırı Modu

```bash
# Show system status / Sistem durumunu göster
kurserver status

# Verbose mode / Ayrıntılı mod
kurserver --verbose interactive
```

## Quick Start / Hızlı Başlangıç

### 1. Basic Web Server Setup / Temel Web Sunucu Kurulumu

```bash
# Start KurServer CLI / KurServer CLI'yi başlat
kurserver

# Select options from menu / Menüden seçenekleri seç:
# 1. Install Nginx / Nginx kur
# 2. Install MySQL / MySQL kur
# 3. Install PHP-FPM / PHP-FPM kur
# 4. Add new website / Yeni web sitesi ekle
```

### 2. Deploy from GitHub / GitHub'dan Dağıtım

```bash
# Select GitHub deployment / GitHub dağıtımını seç
# Enter repository URL / Depo URL'sini gir
# Configure deployment options / Dağıtım seçeneklerini yapılandır
# Automatic deployment / Otomatik dağıtım
```

### 3. SSL Certificate Management / SSL Sertifika Yönetimi

```bash
# Select site management / Site yönetimini seç
# Choose SSL certificates / SSL sertifikalarını seç
# Install Let's Encrypt / Let's Encrypt kur
# Auto-renewal setup / Otomatik yenileme kurulumu
```

## Project Structure / Proje Yapısı

```
kurserver/
├── src/kurserver/           # Main application code / Ana uygulama kodu
│   ├── cli/                 # CLI interface / CLI arayüzü
│   ├── core/                 # Core functionality / Çekirdek işlevsellik
│   ├── installers/           # Package installers / Paket kurucular
│   ├── managers/              # Service managers / Hizmet yöneticileri
│   ├── deployment/            # Deployment tools / Dağıtım araçları
│   ├── config/               # Configuration management / Yapılandırma yönetimi
│   └── utils/                # Utility functions / Yardımcı işlevler
├── templates/                # Configuration templates / Yapılandırma şablonları
├── tests/                    # Test suite / Test paketi
└── docs/                     # Documentation / Dokümantasyon
```

## Configuration Files / Yapılandırma Dosyaları

### User Configuration / Kullanıcı Yapılandırması

```bash
~/.kurserver/config.json
```

### Site Configurations / Site Yapılandırmaları

```bash
/etc/nginx/sites-available/
/etc/php/{version}/fpm/pool.d/
/etc/mysql/conf.d/
```

### Backup Location / Yedek Konumu

```bash
~/.kurserver/backups/
```

## Testing / Test Etme

### Run Tests / Testleri Çalıştır

```bash
# Install development dependencies / Geliştirme bağımlılıklarını kur
pip install -r requirements-dev.txt

# Run unit tests / Birim testlerini çalıştır
pytest tests/unit/

# Run integration tests / Entegrasyon testlerini çalıştır
pytest tests/integration/

# Run all tests with coverage / Tüm testleri kapsam ile çalıştır
pytest --cov=src/kurserver tests/
```

### Test in Docker / Docker'da Test Etme

```bash
# Start development container / Geliştirme konteynerını başlat
docker start c_ubuntu

# Access container / Konteynere eriş
docker exec -it c_ubuntu bash

# Run tests in container / Konteynırda testleri çalıştır
cd /home/ubuntu/KurServer
python -m pytest
```

## Security / Güvenlik

- **Database Security / Veritabanı Güvenliği**
  - Automatic secure installation / Otomatik güvenli kurulum
  - Anonymous user removal / Anonim kullanıcı kaldırma
  - Remote root access disabled / Uzak root erişimi devre dışı
  - Password-based authentication / Şifre tabanlı kimlik doğrulama

- **SSL/TLS Configuration / SSL/TLS Yapılandırması**
  - Let's Encrypt integration / Let's Encrypt entegrasyonu
  - Automatic certificate renewal / Otomatik sertifika yenileme
  - Strong cipher suites / Güçlü şifre suitları
  - Security headers / Güvenlik başlıkları

- **File Permissions / Dosya İzinleri**
  - Secure default permissions / Güvenli varsayılan izinler
  - Web server user isolation / Web sunucusu kullanıcı izolasyonu
  - Sensitive file protection / Hassas dosya koruması

## Performance Optimization / Performans Optimizasyonu

- **Database Tuning / Veritabanı Ayarı**
  - Memory-based configuration / Bellek tabanlı yapılandırma
  - InnoDB optimization / InnoDB optimizasyonu
  - Query cache settings / Sorgu önbelleği ayarları
  - Connection pooling / Bağlantı havuzu

- **PHP Performance / PHP Performansı**
  - OPcache configuration / OPcache yapılandırması
  - Process manager optimization / İşlem yöneticisi optimizasyonu
  - Memory limit tuning / Bellek limiti ayarı
  - Execution time optimization / Çalışma zamanı optimizasyonu

- **Nginx Optimization / Nginx Optimizasyonu**
  - Worker process tuning / İşlemci işlemi ayarı
  - Connection limits / Bağlantı limitleri
  - Static file caching / Statik dosya önbelleği
  - Gzip compression / Gzip sıkıştırma

## Troubleshooting / Sorun Giderme

### Common Issues / Yaygın Sorunlar

1. **Permission Denied / İzin Reddedildi**
   ```bash
   # Check file permissions / Dosya izinlerini kontrol et
   ls -la /var/www/
   
   # Fix permissions / İzinleri düzelt
   sudo chown -R www-data:www-data /var/www/
   sudo chmod -R 755 /var/www/
   ```

2. **Service Not Starting / Hizmet Başlatılamıyor**
   ```bash
   # Check service status / Hizmet durumunu kontrol et
   sudo systemctl status nginx
   sudo systemctl status mysql
   sudo systemctl status php8.1-fpm
   
   # Check logs / Logları kontrol et
   sudo journalctl -u nginx -f
   sudo journalctl -u mysql -f
   ```

3. **Database Connection Failed / Veritabanı Bağlantısı Başarısız**
   ```bash
   # Test database connection / Veritabanı bağlantısını test et
   sudo mysql -u root -p
   
   # Check socket file / Soket dosyasını kontrol et
   ls -la /var/run/mysqld/
   ```

### Getting Help / Yardım Alma

```bash
# Check logs / Logları kontrol et
tail -f ~/.kurserver/logs/kurserver.log

# Run diagnostics / Tanılama çalıştır
kurserver --verbose status

# Reset configuration / Yapılandırmayı sıfırla
rm -rf ~/.kurserver/
```

## Contributing / Katkıda Bulunma

1. Fork repository / Depoyu çatalla
2. Create a feature branch / Özellik dalı oluştur
3. Make your changes / Değişikliklerini yap
4. Add tests / Test ekle
5. Run test suite / Test paketini çalıştır
6. Submit a pull request / Çekme isteği gönder

## License / Lisans

MIT License - see LICENSE file for details / LICENSE dosyasına bakın

## Support / Destek

- **Documentation / Dokümantasyon**: [Wiki](https://github.com/username/kurserver/wiki)
- **Issues / Sorunlar**: [GitHub Issues](https://github.com/username/kurserver/issues)
- **Discussions / Tartışmalar**: [GitHub Discussions](https://github.com/username/kurserver/discussions)

## Changelog / Değişiklik Günlüğü

### v1.0.0 (Current / Mevcut)
- Initial release / İlk sürüm
- Core CLI framework / Çekirdek CLI çerçevesi
- Nginx installer and manager / Nginx kurucu ve yönetici
- MySQL/MariaDB installer and manager / MySQL/MariaDB kurucu ve yönetici
- PHP-FPM installer with extension management / Uzantı yönetimi ile PHP-FPM kurucu
- Site management with SSL support / SSL desteği ile site yönetimi
- GitHub integration / GitHub entegrasyonu
- Configuration management system / Yapılandırma yönetim sistemi
- Comprehensive testing suite / Kapsamlı test paketi

---

**KurServer CLI** - *Ubuntu sunucu yönetiminin kolay yolu* / *The easy way to manage Ubuntu servers*