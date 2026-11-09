# Teclado RGB

Troque a cor do teclado RGB do seu notebook no Linux com uma janela simples, sem decorar comandos no terminal.

Feito para notebooks com chassi **Uniwill/Tongfang**, a base de vários modelos vendidos no Brasil (Avell e outros), em que a cor do teclado é controlada pela BIOS via WMI. Por isso ferramentas como o OpenRGB não enxergam o teclado.

> Projeto não oficial e da comunidade. Não tem ligação com nenhum fabricante.

## O que faz

- Nove cores prontas com um clique, mais um seletor de cor personalizada
- Controle de brilho, de desligado a máximo
- A cor muda na hora e é reaplicada sozinha a cada login
- O driver é instalado com DKMS e continua funcionando quando o kernel atualiza

## Notebooks testados

| Notebook | CPU | Sistema | Status |
|---|---|---|---|
| Avell A52r | AMD Ryzen 7 7435HS | Ubuntu 26.04, kernel 7.0 | ✅ Funciona |

Testou em outro modelo? Abra uma issue dizendo se funcionou, e ele entra na tabela.

## Instalação

```bash
git clone https://github.com/giordanowt/teclado-rgb-linux.git
cd teclado-rgb-linux
./install.sh
```

O instalador pede a senha do `sudo` e:

1. confere se o notebook tem a interface de teclado Uniwill/Tongfang (se não tiver, para sem instalar nada);
2. instala as dependências (no Ubuntu/Debian, via `apt`);
3. baixa o [tuxedo-drivers](https://github.com/tuxedocomputers/tuxedo-drivers) numa versão fixa e testada e instala com DKMS;
4. libera o LED do teclado para o seu usuário controlar sem senha;
5. coloca o **Teclado RGB** no menu de aplicativos.

Depois é só procurar **Teclado RGB** no menu.

### Pela linha de comando

```bash
teclado-rgb --apply
```

Reaplica a última cor salva, a mesma coisa que acontece a cada login.

## Desinstalar

```bash
./uninstall.sh
```

Remove o driver, o app, a regra de permissão e o início automático.

## Limitações conhecidas

- **Chassis Clevo** ainda não são suportados. O instalador detecta e avisa.
- **Só CPUs conhecidas pelo driver.** Em notebooks de outras marcas, o tuxedo-drivers só carrega com CPUs que estão na lista de compatibilidade dele (por exemplo, AMD Ryzen até a série 7000 e Intel até a 12ª geração). Com CPUs mais novas, o instalador avisa que o LED não apareceu.
- **Teclados com RGB por tecla** criam vários LEDs, e o app controla só o primeiro. Teclados de uma zona funcionam por completo.
- **Secure Boot ligado:** o Ubuntu pede para cadastrar uma chave MOK durante a instalação. Reinicie, confirme a chave na tela azul e rode o instalador de novo.

## Como funciona

O driver `uniwill_wmi` do tuxedo-drivers cria o LED `/sys/class/leds/rgb:kbd_backlight`. O app escreve a cor em `multi_intensity` (`R G B`, de 0 a 255) e o brilho em `brightness`. Uma regra udev libera esses dois arquivos para o usuário, e a cor fica salva em `~/.config/teclado-rgb/config.json`.

Se preferir o terminal:

```bash
echo "255 0 0" > /sys/class/leds/rgb:kbd_backlight/multi_intensity
echo 4 > /sys/class/leds/rgb:kbd_backlight/brightness
```

## Créditos

O driver é o [tuxedo-drivers](https://github.com/tuxedocomputers/tuxedo-drivers), da TUXEDO Computers (GPL-2.0). Este projeto só instala esse driver e oferece uma interface por cima dele.

## Licença

GPL-2.0. Veja [LICENSE](LICENSE).
