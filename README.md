# KurServer

Ubuntu sunucular için web sunucusu yönetim CLI aracı.

## Hakkında

KurServer, Ubuntu sunucularda web siteleri yayınlamak için kullanılan komut satırı arayüzüdür. Piyasada olan yönetim panellerinin karmaşıklığından arındırılmış, hızlı ve etkili bir çözüm sunar.

## Özellikler

- ✅ Nginx kurulumu ve yönetimi
- ✅ MySQL/MariaDB veritabanı kurulumu
- ✅ PHP-FPM çoklu versiyon desteği (7.4, 8.0, 8.1, 8.2)
- ✅ Site yönetimi (ekleme/silme/domain değiştirme)
- ✅ GitHub entegrasyonu ile proje dağıtımı
- ✅ Manuel proje dağıtımı
- ✅ Güzel CLI arayüzü (Rich kütüphanesi ile)
- ✅ Sistem durumu takibi
- ✅ Progress göstergeleri ve renkli çıktı
- ✅ Hata yönetimi ve kullanıcı dostu mesajlar

## Kurulum

### Geliştirme Ortamında Kurulum (c_ubuntu Container)

```bash
# Container'ı başlat
docker start c_ubuntu

# Container'a giriş yap
docker exec -it c_ubuntu bash

# Proje dizinine git
cd /home/ubuntu/Kurserver

# Virtual environment oluştur ve aktifleştir
python3 -m venv venv
source venv/bin/activate

# Projeyi kur
pip install -e .
```

### Normal Kurulum

```bash
pip install kurserver
```

## Kullanım

### Temel Komutlar

```bash
# Yardım menüsünü göster
kurserver --help

# Interaktif menüyü başlat
kurserver interactive

# Servis durumlarını göster
kurserver status

# Detaylı çıktı ile çalıştır
kurserver --verbose interactive
```

### c_ubuntu Container'ında Kullanım

```bash
# Container içinde komut çalıştırma
docker exec c_ubuntu bash -c "cd /home/ubuntu/Kurserver && source venv/bin/activate && kurserver --help"

# Interactive menüyü başlatma (sudo ile)
docker exec c_ubuntu bash -c "cd /home/ubuntu/Kurserver && source venv/bin/activate && sudo -E /home/ubuntu/Kurserver/venv/bin/kurserver interactive"

# Servis durumunu kontrol etme
docker exec c_ubuntu bash -c "cd /home/ubuntu/Kurserver && source venv/bin/activate && sudo -E /home/ubuntu/Kurserver/venv/bin/kurserver status"
```

### Interaktif Menü Seçenekleri

```
KurServer CLI - Main Menu

[1] Install Nginx         - Nginx web sunucusu kurulumu
[2] Install MySQL/MariaDB   - Veritabanı sunucusu kurulumu  
[3] Install PHP-FPM        - PHP-FPM kurulumu (versiyon seçimi)
[4] Add new website        - Yeni web sitesi ekleme
[5] Manage databases       - Veritabanı yönetimi
[6] System status          - Sistem durumu gösterimi
[q] Quit/Exit             - Çıkış
```

## Geliştirme

Proje geliştirme ortamını kurmak için:

```bash
# Geliştirme bağımlılıkları ile kurulum
pip install -e ".[dev]"

# Testleri çalıştırma
pytest

# Kod formatlama
black src/
flake8 src/
```

### Docker Container Geliştirme

Tüm geliştirme ve test işlemleri `c_ubuntu` container'ında yapılmalıdır:

```bash
# Container'ı başlat
docker start c_ubuntu

# Container'a giriş yap ve proje dizinine git
docker exec -it c_ubuntu bash
cd /home/ubuntu/Kurserver

# Virtual environment'ı aktifleştir
source venv/bin/activate

# Geliştirme yap...
```

## Proje Yapısı

```
kurserver/
├── src/kurserver/
│   ├── cli/          # CLI arayüzü ve menü sistemi
│   ├── core/          # Çekirdek sistem fonksiyonları
│   ├── installers/    # Paket kurulum modülleri
│   ├── managers/      # Servis yönetim modülleri
│   ├── config/        # Yapılandırma yönetimi
│   └── utils/         # Yardımcı fonksiyonlar
├── templates/          # Yapılandırma şablonları
├── tests/              # Test suite
└── docs/               # Dokümantasyon
```

## Gereksinimler

- Ubuntu 18.04 veya üzeri
- Python 3.8+
- Yönetici (sudo) yetkileri

## Lisans

MIT Lisansı