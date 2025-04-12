import os
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

os.environ["GROQ_API_KEY"] = api_key

chat = ChatGroq(model="llama3-70b-8192", temperature=0.2)

prompt_template = ChatPromptTemplate.from_template("""
Você é um analista forense digital especializado em monitoramento e interpretação de atividades digitadas por keylogger.

Sua tarefa é analisar os logs fornecidos com atenção aos seguintes pontos:

---

1. **Exibir todos os dados brutos exatamente como foram capturados**, incluindo letras, números, teclas especiais, símbolos, nome do processo, janela, etc.
2. **Interpretar padrões de teclas combinadas**, como `[CTRL + C]`, `[CTRL + A]`, `[ALT + F4]`, descrevendo suas funções ("copiar", "selecionar tudo", "fechar janela", etc.).
3. **Organizar a resposta em seções claras e nomeadas**, com foco técnico e objetivo.
4. **Destacar possíveis credenciais**, senhas, logins, URLs de login, comandos de terminal e qualquer dado sensível que possa ter sido digitado.
5. **Finalizar com uma síntese objetiva** da atividade observada, incluindo padrões comportamentais, tentativas de autenticação, ou comandos suspeitos.
6. **Identifique repetições incomuns, logs incompletos, truncados ou fora de ordem**, se aplicável.

---

### Exemplo de saída esperada:

## Logs Brutos:
                                                   
- Aqui ficam todos os logs do arquivo de maneira bruta, ou seja, sem formatação, da maneira recbida.

## Interpretação de Atalhos:
                                                   
- Aqui ficam as interpretações de possíveis atalhos/combinações

## Detecção de Dados Sensíveis:
                                                   
- Aqui ficam TODOS os dados possivelmente sensíveis.

## Síntese Final:
                                                   
- Aqui fica a síntese final.
---

### Logs Capturados:
{logs}

---
**Importante:** Seja fiel aos logs. Não omita nem corrija automaticamente erros de digitação, a não ser que esteja explicitamente interpretando o significado.
""")


chain = prompt_template | chat


def analyze_logs(logs: list[str]) -> str:
    combined_logs = "\n".join(logs)
    response = chain.invoke({"logs": combined_logs})
    return response.content
