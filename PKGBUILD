# Maintainer: Yaroslav <yaroslav@example.com>
pkgname=monokular
pkgver=1.0.0
pkgrel=5
pkgdesc="Export PDF pages as images with preview — one thing, done well"
arch=('any')
license=('MIT')
depends=(
    'python'
    'python-pyqt6'
    'python-pymupdf'
)
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/$pkgname-$pkgver"

    # Install app files
    install -dm755 "$pkgdir/usr/lib/$pkgname"
    cp -r app/ main.py "$pkgdir/usr/lib/$pkgname/"

    # Install icon
    install -Dm644 assets/icon.svg "$pkgdir/usr/share/icons/hicolor/scalable/apps/$pkgname.svg"

    # Install desktop file
    install -Dm644 "$pkgname.desktop" "$pkgdir/usr/share/applications/$pkgname.desktop"

    # Create launcher script
    install -dm755 "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/$pkgname" << 'EOF'
#!/bin/sh
exec python3 /usr/lib/monokular/main.py "$@"
EOF
    chmod 755 "$pkgdir/usr/bin/$pkgname"
}
