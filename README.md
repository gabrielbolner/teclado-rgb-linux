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

Leva uns 2 minutos e não precisa saber nada de terminal.

**1. Abra o terminal**

Aperte `Ctrl` + `Alt` + `T`, ou procure por **Terminal** no menu de aplicativos.

**2. Copie e cole este comando no terminal e aperte `Enter`**

```bash
sudo apt install -y git && git clone https://github.com/giordanowt/teclado-rgb-linux.git ~/teclado-rgb-linux && cd ~/teclado-rgb-linux && ./install.sh
```

> Para colar no terminal, use `Ctrl` + `Shift` + `V` (só `Ctrl` + `V` não funciona no terminal).

**3. Digite a sua senha quando pedir**

É a mesma senha que você usa para entrar no computador. Enquanto você digita, nada aparece na tela. Isso é normal: digite e aperte `Enter`.

**4. Espere terminar**

O instalador mostra cada etapa e termina com a mensagem **"Pronto!"**. Se aparecer uma mensagem de **ERRO**, veja a seção [Deu erro?](#deu-erro).

Se o seu computador estiver com o **Secure Boot** ligado, o instalador para no meio e pede uma reinicialização. Veja a seção abaixo.

### Secure Boot: não precisa desligar

O Secure Boot é uma proteção da inicialização do computador que só deixa carregar drivers assinados. Muitos notebooks vêm com ele ligado. **Você não precisa desligar.** O Ubuntu assina o driver com uma chave própria do seu computador, e você só precisa autorizar essa chave uma vez:

1. Durante a instalação, o terminal pede para você **criar uma senha temporária** (8 caracteres ou mais). Anote, porque você vai digitar ela em seguida.
2. **Reinicie o computador.** Antes do Ubuntu abrir, aparece uma **tela azul** chamada *MOK Management*.
3. Aperte qualquer tecla, escolha **Enroll MOK**, depois **Continue** e **Yes**.
4. Digite a **senha temporária** que você criou e escolha **Reboot**.
5. Com o Ubuntu aberto de novo, abra o terminal e termine a instalação:

   ```bash
   cd ~/teclado-rgb-linux && ./install.sh
   ```

> A tela azul fica poucos segundos esperando. Se ela passar direto e o Ubuntu abrir, rode o `./install.sh` de novo, reinicie e fique de olho.

Se o Secure Boot já estiver desligado, ou se a chave já estiver cadastrada (por exemplo, porque você já instalou drivers da NVIDIA), nada disso aparece.

**5. Abra o app**

Aperte a tecla `Super` (a do logo do Windows), digite **Teclado RGB** e abra. Clique numa cor e o teclado muda na hora.

### O que o instalador faz

1. Confere se o notebook tem a interface de teclado Uniwill/Tongfang. Se não tiver, para sem instalar nada.
2. Instala as dependências (no Ubuntu/Debian, via `apt`).
3. Baixa o [tuxedo-drivers](https://github.com/tuxedocomputers/tuxedo-drivers) numa versão fixa e testada e instala com DKMS.
4. Libera o LED do teclado para o seu usuário controlar sem senha.
5. Coloca o **Teclado RGB** no menu de aplicativos e reaplica a sua cor a cada login.

### Atualizar

Abra o terminal e cole:

```bash
cd ~/teclado-rgb-linux && git pull && ./install.sh
```

### Deu erro?

Abra uma [issue](https://github.com/giordanowt/teclado-rgb-linux/issues/new) com:

- o modelo do notebook;
- tudo o que apareceu no terminal (copie com `Ctrl` + `Shift` + `C`);
- a saída do comando `lscpu | head -20`.

Veja também as [limitações conhecidas](#limitações-conhecidas). As mais comuns são chassi Clevo e CPU nova demais para o driver.

### Pela linha de comando

```bash
teclado-rgb --apply
```

Reaplica a última cor salva, a mesma coisa que acontece a cada login.

## Desinstalar

Abra o terminal e cole:

```bash
~/teclado-rgb-linux/uninstall.sh
```

Remove o driver, o app, a regra de permissão e o início automático.

## Limitações conhecidas

- **Chassis Clevo** ainda não são suportados. O instalador detecta e avisa.
- **Só CPUs conhecidas pelo driver.** Em notebooks de outras marcas, o tuxedo-drivers só carrega com CPUs que estão na lista de compatibilidade dele (por exemplo, AMD Ryzen até a série 7000 e Intel até a 12ª geração). Com CPUs mais novas, o instalador avisa que o LED não apareceu.
- **Teclados com RGB por tecla** criam vários LEDs, e o app controla só o primeiro. Teclados de uma zona funcionam por completo.

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
