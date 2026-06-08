---
device: Lenovo LOQ (Gerações Intel Core - Ex: 13ª e 14ª Geração)
source: Reddit - r/LenovoLOQ
topic: Guia de Undervolt de CPU via Lenovo Vantage para Controle Térmico
status: Consolidador / Guia Prático
---

# Guia Comunitário: Como Fazer Undervolt na CPU pelo Lenovo Vantage

## Post Original (User: NotebookCoolingPro):
Muitos donos de Lenovo LOQ sofrem com thermal throttling, vendo as temperaturas da CPU baterem 95°C-98°C facilmente em jogos pesados como Helldivers 2 ou Cyberpunk 2077. Este guia explica como usar o próprio software oficial de fábrica (*Lenovo Vantage*) para fazer um undervolt seguro e reduzir as temperaturas em até 10°C-15°C sem perder desempenho (e em alguns casos, ganhando estabilidade de FPS).

---

## Passo a Passo para Aplicação do Undervolt:

### Passo 1: Desativar o "Undervolt Protection" na BIOS
Antes de mexer no software, você precisa dar permissão para o sistema alterar as tensões:
1. Reinicie o notebook e fique pressionando a tecla **F2** repetidamente para entrar na BIOS.
2. Vá até a aba **Advanced** ou **More Settings**.
3. Procure pela opção **Undervolt Protection** e mude para **Disabled** (Desativado).
4. Procure também por **Core Voltage Offset** ou **Overclocking Feature** e mude para **Enabled** (Ativado).
5. Pressione **F10** para salvar as alterações e reiniciar o Windows.

### Passo 2: Configuração no Lenovo Vantage
Com a BIOS desbloqueada, o painel do Vantage vai liberar os sliders de controle de energia:
1. Abra o aplicativo **Lenovo Vantage** no Windows.
2. Na tela inicial, mude o Thermal Mode para **Custom** (Modo Personalizado).
3. Uma tela de aviso sobre overclock/undervolt vai aparecer; clique em aceitar.
4. Role a página até encontrar a seção **CPU Overclock** e ative a chave (Toggle).
5. Clique em **Advanced Settings** (Configurações Avançadas) para abrir os sliders de voltagem.

### Passo 3: Ajustando o Core Voltage Offset (O Undervolt Técnico)
**Atenção:** O objetivo é reduzir a voltagem para o chip trabalhar mais frio. O valor deve ser **NEGATIVO**.
* Procure pelo slider **CPU Core Voltage Offset**.
* Mova o slider cuidadosamente para valores negativos.
* **Ponto de partida seguro recomendado pela comunidade:** Comece com **-50mV** (ou `-0.050V`).
* Se o sistema ficar estável após algumas horas de jogo, você pode tentar descer para **-80mV** (`-0.080V`) ou até **-100mV** (`-0.100V`), que é o "sweet spot" (ponto ideal) da maioria dos chips Intel de notebook.

---

## Notas Importantes da Comunidade sobre Estabilidade:

* **Sintomas de Instabilidade:** Se o valor negativo for agressivo demais para o seu silício, o notebook vai dar tela azul (BSOD) ou reiniciar sozinho durante o jogo. Se isso acontecer, não entre em pânico: o Vantage resguarda as configurações de fábrica no reboot. Basta abrir o app e subir o valor (ex: se travou em -100mV, mude para -80mV).
* **Resultados Esperados:** Usuários relatam que a CPU que antes operava colada em 96°C estabilizou na casa dos 82°C-84°C, eliminando completamente os travamentos por superaquecimento (thermal throttling).