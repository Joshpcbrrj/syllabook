<!-- translation-of: 0008-english-skill-bilingual-docs.md sha256:046f20abb3dd -->
# 8. A skill é em inglês; a documentação, em inglês e português

[English](0008-english-skill-bilingual-docs.md) | **Português**

**Situação:** aceita · **Origem:** `plano/PLANO.md §22`

## Contexto

O projeto nasceu em português, mas o inglês alcança mais gente, e o modelo segue bem instruções em inglês em qualquer idioma de conversa.

## Decisão

A skill, os identificadores e as mensagens são escritos em inglês; o Claude conversa e escreve cada livro no idioma que o usuário escolher. A documentação é em inglês, com a versão em português ao lado; cada tradução guarda o hash da página em inglês que traduziu.

## Consequências

Um teste avisa quando uma página em inglês muda e a tradução não. Cada idioma de livro tem um arquivo curto de estilo, para o texto não sair com cara de tradução.
