# Logger AI

### O Logger AI é uma ferramenta que desenvolvi com Python para pesquisa e aprendizado em **offsec**, focada no estudo de técnicas utilizadas por malwares, como keyloggers e RATs. Ela simula comportamentos maliciosos e utiliza um agente inteligente para análise e formatação dos dados que foram coletados.

#### ⚠️ **Aviso**  ⚠️
Este projeto é educacional. Não utilize em ambientes não autorizados. Use com responsabilidade.

---

##  Funcionalidades

- **Keylogger com contexto de janela/processo ativo**  
  Registra todas as teclas pressionadas, associando-as à janela e processo em uso no momento da digitação.

- **Captura automática de tela**  
  Realiza screenshots em intervalos definidos, para análise visual do ambiente e comportamento do usuário.

- **Compactação e envio automático de logs**  
  Todos os arquivos coletados são comprimidos (.zip) e enviados via Discord Webhook para uma central (servidor) de coleta remota.

- **Análise e formatação dos logs com LLM**  
  Um agente de Inteligência Artificial (LLM) é utilizado para interpretar e formatar os logs, tornando-os mais legíveis e úteis para análise.

- **Persistência no sistema**  
  Implementa persistência através de entrada no `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`, simulando táticas usadas por malwares reais.

- **Autolimpeza após exfiltração**  
  Remove evidências locais automaticamente após o envio dos dados, como logs e capturas de tela, simulando técnicas de evasão.

---

## Ideal para

- Criação de laboratórios de análise comportamental
- Simulações Red Team em ambientes controlados
- Testes com ferramentas de detecção e resposta (EDR/AV)
- Estudo de RATs e trojans no geral
- Aprimoramento de habilidades em threat hunting e análise forense
