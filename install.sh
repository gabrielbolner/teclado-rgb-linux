#!/usr/bin/env bash
set -euo pipefail

DRIVER_REPO="https://github.com/tuxedocomputers/tuxedo-drivers.git"
DRIVER_REF="77de99bc2a4d2333a1a1e70064ec77b175fe93cd"
NAME="tuxedo-drivers"
APP_ID="io.github.giordanowt.TecladoRGB"
LED="/sys/class/leds/rgb:kbd_backlight"
WMI="/sys/bus/wmi/devices"

if [ "$(id -u)" -ne 0 ]; then
    exec sudo bash "$0" "$@"
fi

HERE="$(cd "$(dirname "$0")" && pwd)"

fail() {
    echo "ERRO: $*" >&2
    exit 1
}

echo "==> Verificando o hardware"
if [ -e "$WMI/ABBC0F6F-8EA1-11D1-00A0-C90629100000" ]; then
    echo "    Chassi Uniwill/Tongfang detectado."
elif [ -e "$WMI/ABBC0F6D-8EA1-11D1-00A0-C90629100000" ]; then
    fail "chassi Clevo detectado. Por enquanto só notebooks Uniwill/Tongfang são suportados. Abra uma issue com o modelo do seu notebook."
else
    fail "não encontrei a interface WMI de teclado Uniwill/Tongfang neste notebook. Ele provavelmente não é compatível."
fi

echo "==> Instalando dependências"
if command -v apt-get >/dev/null; then
    apt-get install -y git dkms build-essential "linux-headers-$(uname -r)" \
        python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
else
    for cmd in git dkms make gcc python3; do
        command -v "$cmd" >/dev/null || fail "instale '$cmd' e rode de novo."
    done
    [ -d "/lib/modules/$(uname -r)/build" ] || fail "instale os headers do kernel $(uname -r) e rode de novo."
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "==> Baixando o driver $NAME ($DRIVER_REF)"
git -C "$WORK" init -q drivers
git -C "$WORK/drivers" fetch -q --depth 1 "$DRIVER_REPO" "$DRIVER_REF"
git -C "$WORK/drivers" checkout -q FETCH_HEAD
sed -i 's/^\(\s*\)X86_MATCH_VFM(INTEL_ALDERLAKE_L, NULL),$/&\n\1X86_MATCH_VFM(INTEL_RAPTORLAKE_P, NULL),/' "$WORK/drivers/src/tuxedo_compatibility_check/tuxedo_compatibility_check.c"
VERSION="$(grep -m1 -oP 'version: "\K[^"]+' "$WORK/drivers/package.yml")"
DEST="/usr/src/$NAME-$VERSION"

echo "==> Instalando o driver $NAME $VERSION via DKMS"
if dkms status -m "$NAME" -v "$VERSION" 2>/dev/null | grep -q .; then
    dkms remove -m "$NAME" -v "$VERSION" --all || true
fi
rm -rf "$DEST"
cp -r "$WORK/drivers/src" "$DEST"

cat > "$DEST/dkms.conf" <<'EOF'
PACKAGE_NAME="tuxedo-drivers"
PACKAGE_VERSION="@VERSION@"
AUTOINSTALL="yes"
MAKE[0]="make -C ${kernel_source_dir} M=${dkms_tree}/${PACKAGE_NAME}/${PACKAGE_VERSION}/build modules"
CLEAN="make -C ${kernel_source_dir} M=${dkms_tree}/${PACKAGE_NAME}/${PACKAGE_VERSION}/build clean"
BUILT_MODULE_NAME[0]="tuxedo_compatibility_check"
BUILT_MODULE_LOCATION[0]="tuxedo_compatibility_check/"
DEST_MODULE_LOCATION[0]="/updates/dkms"
BUILT_MODULE_NAME[1]="tuxedo_keyboard"
DEST_MODULE_LOCATION[1]="/updates/dkms"
BUILT_MODULE_NAME[2]="uniwill_wmi"
DEST_MODULE_LOCATION[2]="/updates/dkms"
EOF
sed -i "s/@VERSION@/$VERSION/" "$DEST/dkms.conf"

dkms add -m "$NAME" -v "$VERSION"
dkms build -m "$NAME" -v "$VERSION"
dkms install -m "$NAME" -v "$VERSION" --force

echo "uniwill_wmi" > /etc/modules-load.d/teclado-rgb.conf

if mokutil --sb-state 2>/dev/null | grep -qi enabled; then
    echo "==> Secure Boot ligado: conferindo a chave que assina o driver"
    MOK_KEY=""
    for candidate in /var/lib/shim-signed/mok/MOK.der /var/lib/dkms/mok.pub; do
        if [ -f "$candidate" ]; then
            MOK_KEY="$candidate"
            break
        fi
    done
    [ -n "$MOK_KEY" ] || fail "o Secure Boot está ligado, mas não achei a chave de assinatura do DKMS."
    if mokutil --test-key "$MOK_KEY" 2>/dev/null | grep -qi "already enrolled"; then
        echo "    A chave já está cadastrada."
    else
        cat <<'EOF'

    O Secure Boot está ligado, então o driver precisa ser assinado por uma chave
    cadastrada no seu computador. Isso só é feito uma vez. NÃO é preciso desligar
    o Secure Boot.

    Agora vou pedir para você criar uma senha temporária (8 caracteres ou mais).
    Ela só vai ser usada uma vez, na tela azul do próximo boot.

EOF
        mokutil --import "$MOK_KEY" || fail "não foi possível preparar o cadastro da chave."
        cat <<'EOF'

==> Falta só reiniciar. No próximo boot aparece uma tela azul (MOK Management):

    1. aperte qualquer tecla para entrar;
    2. escolha "Enroll MOK";
    3. escolha "Continue" e depois "Yes";
    4. digite a senha temporária que você acabou de criar;
    5. escolha "Reboot".

    Depois de reiniciar, rode o instalador de novo para terminar:

        cd ~/teclado-rgb-linux && ./install.sh

EOF
        exit 0
    fi
fi

echo "==> Liberando o LED do teclado para o usuário"
cat > /etc/udev/rules.d/99-teclado-rgb.rules <<'EOF'
ACTION=="add", SUBSYSTEM=="leds", KERNEL=="rgb:kbd_backlight", RUN+="/bin/chmod 0666 /sys%p/brightness /sys%p/multi_intensity"
EOF
udevadm control --reload-rules

echo "==> Carregando o driver"
rmmod uniwill_wmi tuxedo_keyboard tuxedo_compatibility_check 2>/dev/null || true
modprobe uniwill_wmi || true
for _ in $(seq 1 10); do
    [ -e "$LED/multi_intensity" ] && break
    sleep 1
done
if [ ! -e "$LED/multi_intensity" ]; then
    dmesg | grep -iE 'tuxedo|uniwill' | tail -n 10 >&2 || true
    fail "o driver foi instalado, mas o LED do teclado não apareceu. O driver da TUXEDO só aceita CPUs que ele já conhece em notebooks de outras marcas. Abra uma issue com a saída acima, o modelo do notebook e a saída de 'lscpu'."
fi
chmod 0666 "$LED/brightness" "$LED/multi_intensity"

echo "==> Instalando o app"
rm -f /usr/share/applications/br.com.giordano.TecladoRGB.desktop
install -Dm755 "$HERE/teclado-rgb.py" /usr/local/bin/teclado-rgb
install -Dm644 "$HERE/$APP_ID.desktop" "/usr/share/applications/$APP_ID.desktop"
install -Dm644 "$HERE/teclado-rgb-autostart.desktop" /etc/xdg/autostart/teclado-rgb-apply.desktop
update-desktop-database -q /usr/share/applications 2>/dev/null || true

if [ -n "${SUDO_USER:-}" ]; then
    sudo -u "$SUDO_USER" /usr/local/bin/teclado-rgb --apply || true
fi

echo "==> Pronto! Procure por \"Teclado RGB\" no menu de aplicativos."
