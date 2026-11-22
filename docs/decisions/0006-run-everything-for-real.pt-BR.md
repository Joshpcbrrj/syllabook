<!-- translation-of: 0006-run-everything-for-real.md sha256:b4424ceec714 -->
# 6. Todo comando roda de verdade

[English](0006-run-everything-for-real.md) | **Português**

**Situação:** aceita · **Origem:** `plano/PLANO.md §21`

## Contexto

Um livro com um comando que não funciona perde a confiança de quem estuda sozinho, que não tem professor a quem perguntar.

## Decisão

Cada trecho de código e cada comando é executado, nesta ordem: na sessão; no computador do usuário, se estiver ligado ao app; execução guiada (o usuário roda e cola a saída); se não der, sai marcado como "não executado", com aviso.

## Consequências

Os livros mostram saídas reais, e o que não pôde rodar fica visível no texto e no resumo final. Laboratórios que mexem em credenciais rodam com uma pasta pessoal temporária.
