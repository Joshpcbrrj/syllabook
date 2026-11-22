<!-- translation-of: 0010-problem-reports-with-consent.md sha256:4698e61a4b42 -->
# 10. Relato de problemas só com o "sim" do usuário

[English](0010-problem-reports-with-consent.md) | **Português**

**Situação:** aceita · **Origem:** `plano/V1.md §1b`

## Contexto

Quando a skill tropeça num problema dela, quem a mantém só fica sabendo se alguém relatar; mas um relato nunca pode levar dados do usuário nem ser enviado sem ele saber.

## Decisão

A skill anota os próprios problemas e, no resumo final, mostra um relato montado pelo `report.py` (sem dados pessoais). Ele só é enviado como issue depois de um "sim" claro, com o login do GitHub do usuário ou por um link que ele clica. Nada de pull request automático: as correções são feitas no repositório, com testes.

## Consequências

Os relatos chegam ao repositório público do Syllabook. Um fork que mude o endereço passa a receber os relatos ele mesmo.
