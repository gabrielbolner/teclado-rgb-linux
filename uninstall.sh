#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    exec sudo bash "$0" "$@"
fi

NAME="tuxedo-drivers"
for version in $(dkms status -m "$NAME" 2>/dev/null | grep -oP "^$NAME/\K[^,:]+" | sort -u); do
    dkms remove -m "$NAME" -v "$version" --all || true
    rm -rf "/usr/src/$NAME-$version"
done

rm -f /etc/modules-load.d/teclado-rgb.conf \
    /etc/udev/rules.d/99-teclado-rgb.rules \
    /usr/local/bin/teclado-rgb \
    /usr/share/applications/br.com.giordano.TecladoRGB.desktop \
    /usr/share/applications/io.github.giordanowt.TecladoRGB.desktop \
    /etc/xdg/autostart/teclado-rgb-apply.desktop
udevadm control --reload-rules
update-desktop-database -q /usr/share/applications 2>/dev/null || true
rmmod uniwill_wmi tuxedo_keyboard tuxedo_compatibility_check 2>/dev/null || true

echo "Teclado RGB removido."
