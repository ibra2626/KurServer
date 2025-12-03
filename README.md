# KurServer CLI

Ubuntu sunucular için web sunucusu yönetim CLI aracı / Ubuntu server management CLI tool.

## Hakkında / About

KurServer, Ubuntu sunucularda web siteleri yayınlamak için kullanılan komut satırı arayüzüdür. Piyasada olan yönetim panellerinin karmaşıklığından arındırılmış, hızlı ve etkili bir çözüm sunar.

KurServer is a command-line interface for publishing websites on Ubuntu servers. It is simplified from the complexity of existing control panels in the market, offering a fast and effective solution.

## Özellikler / Features

- ✅ Nginx kurulumu ve yönetimi / Nginx installation and management
- ✅ MySQL/MariaDB veritabanı kurulumu / MySQL/MariaDB database installation
- ✅ PHP-FPM çoklu versiyon desteği (7.4, 8.0, 8.1, 8.2) / PHP-FPM multi-version support
- ✅ Site yönetimi (ekleme/silme/domain değiştirme) / Site management (add/remove/domain change)
- ✅ GitHub entegrasyonu ile proje dağıtımı / Project deployment with GitHub integration
- ✅ Manuel proje dağıtımı / Manual project deployment
- ✅ Güzel CLI arayüzü (Rich kütüphanesi ile) / Beautiful CLI interface (with Rich library)
- ✅ Sistem durumu takibi / System status tracking
- ✅ Progress göstergeleri ve renkli çıktı / Progress indicators and colored output
- ✅ Hata yönetimi ve kullanıcı dostu mesajlar / Error handling and user-friendly messages

## Kurulum / Installation

### Geliştirme Ortamında Kurulum (c_ubuntu Container) / Development Environment Setup (c_ubuntu Container)

```bash
# Container'ı başlat / Start container
docker start c_ubuntu

# Container'a giriş yap / Access container
docker exec -it c_ubuntu bash

# Proje dizinine git / Go to project directory
cd /home/ubuntu/Kurserver

# Virtual environment oluştur ve aktifleştir / Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Projeyi kur / Install project
pip install -e .
```

### Normal Kurulum / Standard Installation

```bash
pip install kurserver
```

## Kullanım / Usage

### Temel Komutlar / Basic Commands

```bash
# Yardım menüsünü göster / Show help menu
kurserver --help

# Interaktif menüyü başlat / Start interactive menu
kurserver interactive

# Servis durumlarını göster / Show service status
kurserver status

# Detaylı çıktı ile çalıştır / Run with verbose output
kurserver --verbose interactive
```

### c_ubuntu Container'ında Kullanım / Usage in c_ubuntu Container

```bash
# Container içinde komut çalıştırma / Run command inside container
docker exec c_ubuntu bash -c "cd /home/ubuntu/Kurserver && source venv/bin/activate && kurserver --help"

# Interactive menüyü başlatma (sudo ile) / Start interactive menu (with sudo)
docker exec c_ubuntu bash -c "cd /home/ubuntu/Kurserver && source venv/bin/activate && sudo -E /home/ubuntu/Kurserver/venv/bin/kurserver interactive"

# Servis durumunu kontrol etme / Check service status
docker exec c_ubuntu bash -c "cd /home/ubuntu/Kurserver && source venv/bin/activate && sudo -E /home/ubuntu/Kurserver/venv/bin/kurserver status"
```

### Interaktif Menü Seçenekleri / Interactive Menu Options

```
KurServer CLI - Main Menu

[1] Install Nginx         - Nginx web sunucusu kurulumu / Nginx web server installation
[2] Install MySQL/MariaDB   - Veritabanı sunucusu kurulumu / Database server installation  
[3] Install PHP-FPM        - PHP-FPM kurulumu (versiyon seçimi) / PHP-FPM installation (version selection)
[4] Add new website        - Yeni web sitesi ekleme / Add new website
[5] Manage databases       - Veritabanı yönetimi / Database management
[6] System status          - Sistem durumu gösterimi / Show system status
[q] Quit/Exit             - Çıkış / Exit
```

## Geliştirme / Development

Proje geliştirme ortamını kurmak için / To set up project development environment:

```bash
# Geliştirme bağımlılıkları ile kurulum / Install with development dependencies
pip install -e ".[dev]"

# Testleri çalıştırma / Run tests
pytest

# Kod formatlama / Code formatting
black src/
flake8 src/
```

### Docker Container Geliştirme / Docker Container Development

Tüm geliştirme ve test işlemleri `c_ubuntu` container'ında yapılmalıdır / All development and testing operations should be done in the `c_ubuntu` container:

```bash
# Container'ı başlat / Start container
docker start c_ubuntu

# Container'a giriş yap ve proje dizinine git / Access container and go to project directory
docker exec -it c_ubuntu bash
cd /home/ubuntu/Kurserver

# Virtual environment'ı aktifleştir / Activate virtual environment
source venv/bin/activate

# Geliştirme yap... / Start development...
```

## Proje Yapısı / Project Structure

```
kurserver/
├── src/kurserver/
│   ├── cli/          # CLI arayüzü ve menü sistemi / CLI interface and menu system
│   ├── core/          # Çekirdek sistem fonksiyonları / Core system functions
│   ├── installers/    # Paket kurulum modülleri / Package installation modules
│   ├── managers/      # Servis yönetim modülleri / Service management modules
│   ├── config/        # Yapılandırma yönetimi / Configuration management
│   └── utils/         # Yardımcı fonksiyonlar / Helper functions
├── templates/          # Yapılandırma şablonları / Configuration templates
├── tests/              # Test suite / Test suite
└── docs/               # Dokümantasyon / Documentation
```

## Gereksinimler / Requirements

- Ubuntu 18.04 veya üzeri / Ubuntu 18.04 or later
- Python 3.8+ / Python 3.8+
- Yönetici (sudo) yetkileri / Administrator (sudo) privileges

## Lisans / License

MIT License / MIT Lisansı