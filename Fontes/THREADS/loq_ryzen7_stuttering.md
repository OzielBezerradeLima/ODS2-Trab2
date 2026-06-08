---
device: Lenovo LOQ 15 (Ryzen 7 7840HS / RTX 4060)
source: Reddit - r/LenovoLOQ
topic: Micro-stutters e quedas de frame pacing em jogos pesados
status: Solucionado pela Comunidade
---

# Problema: Quedas bruscas de FPS (1% Lows) e Stuttering no LOQ Ryzen 7

## Post Original (User: TechGamer_99):
Comprei um Lenovo LOQ (Ryzen 7, RTX 4060, 16GB RAM) e estou enfrentando micro-travamentos (stuttering) muito irritantes em jogos como Elden Ring e Cyberpunk 2077. O FPS médio fica alto (70-80 FPS no Ultra), mas do nada o frametime dá um pico e o jogo engasga por um milissegundo. O Windows foi recém-instalado e os drivers estão atualizados. Alguém sabe como resolver?

---

## Principais Respostas e Soluções da Comunidade:

### Solução 1: Desativação do fTPM da AMD (A mais votada)
**User: CoreMechanic:**
> "Esse é um problema crônico de stuttering em processadores AMD Ryzen no Windows 11. O fTPM (Trusted Platform Module baseado em firmware) implementado na BIOS causa conflitos de latência intermitentes, gerando essas engasgadas aleatórias no frametime. 
> 
> **Como resolver:** Reinicie o notebook, entre na BIOS pressionando F2, vá na aba de Segurança (Security) e desative a opção 'AMD fTPM' ou 'AMD PSP Support'. Se você não usa criptografia BitLocker, desativar isso elimina 95% dos micro-stutters em processadores Ryzen."

### Solução 2: Gerenciamento de Energia e Modo "Performance" no Vantage
**User: LaptopEnthusiast_BR:**
> "O Lenovo LOQ gerencia o cTGP (Dynamic Boost da placa de vídeo) de forma muito agressiva no modo 'Balanced' (Equilibrado). Quando o processador e a GPU demandam energia ao mesmo tempo em áreas pesadas, o sistema limita o clock bruscamente para conter a temperatura, causando o drop nos 1% lows.
> 
> **Como resolver:** > 1. Abra o software Lenovo Vantage.
> 2. Mude o perfil térmico para o Modo Performance (a luz do botão Power vai ficar vermelha).
> 3. Certifique-se de que o notebook está ligeiramente elevado na traseira para melhorar o fluxo de ar, impedindo o thermal throttling que engasga o jogo."

### Solução 3: Conflito com Overlays de Terceiros
**User: FramePacer_Pro:**
> "Se você estiver usando o MSI Afterburner junto com o overlay do Discord e o GeForce Experience ao mesmo tempo, as hooks de renderização vão brigar e causar stuttering. Desative o overlay de tela do Discord e o 'In-Game Overlay' do GeForce Experience nas configurações gerais."