# Relatório de Avaliação Manual

Este relatório registra testes manuais da interface e do fluxo RAG. Durante a fase inicial, as respostas podem usar o mock local do frontend React. Na avaliação final, os mesmos casos devem ser executados com o pipeline RAG completo e Qwen2.5:7B via Ollama.

A interface React também possui uma aba de avaliação manual. Cada resposta pode ser marcada com:

- **Respondeu?**: Sim, Parcial ou Não.
- **Fonte correta?**: Sim ou Não.
- **Observações**: comentário livre sobre qualidade, fonte ou limitação.

O histórico pode ser exportado em JSON para complementar este relatório.

| Pergunta | Notebook | Jogo | Respondeu? | Fonte Correta? | Observações |
| --- | --- | --- | --- | --- | --- |
| Qual o limite de RAM do LOQ? | Lenovo LOQ | Todos | Sim | Sim | Deve citar o manual do Lenovo LOQ. |
| Melhor undervolt para Elden Ring? | Lenovo LOQ | Elden Ring | Parcial | Sim | Deve diferenciar fonte oficial de relato de fórum. |
| Receita de bolo | Todos | Todos | Não | Sim | Deve recusar por falta de contexto técnico. |
| Houve correção de stuttering em Elden Ring? | Todos | Elden Ring | Sim | Sim | Deve citar patch note ou driver notes. |
| O Asus TUF muda desempenho por perfil térmico? | Asus TUF | Todos | Sim | Sim | Deve citar manual ou documentação do fabricante. |

## Critérios

- **Respondeu?**: indica se a resposta foi completa, parcial ou recusada corretamente.
- **Fonte Correta?**: indica se as fontes exibidas sustentam a resposta.
- **Observações**: registra problemas de citação, alucinação, falta de contexto ou comportamento esperado.

## Resultado Esperado

O sistema deve responder apenas quando houver contexto suficiente. Para perguntas fora do domínio, deve informar claramente que não há informação técnica suficiente nas fontes disponíveis.
