<!-- translation-of: SECURITY.md sha256:68f29af028ee -->
# Segurança

[English](SECURITY.md) | **Português**

## Como relatar um problema

Se você encontrar um problema de segurança na skill ou nos scripts (por exemplo, algo que exponha tokens, senhas ou arquivos do usuário), **não abra uma issue pública**.

Use o relato privado do GitHub: aba **Security** do repositório → **Report a vulnerability**. Descreva o problema, como reproduzi-lo e o impacto.

A resposta inicial vem em até 7 dias. Quando houver correção, ela entra no [CHANGELOG](CHANGELOG.md) e no aviso de segurança do repositório.

## Boas práticas que a skill segue

- Nunca pede que você cole tokens, senhas ou chaves no chat. As conexões são feitas pelos conectores do Claude (Notion, Google Drive e GitHub no app do Claude) ou pelo seu próprio login no Claude Code (`gh auth login` para o GitHub).
- Não baixa instruções da internet durante o uso: tudo o que a skill segue vem no pacote instalado.
- Materiais que você envia servem só de fonte: os arquivos originais nunca são publicados. No modo Aprimorar, o livro aprimorado vai para a sua biblioteca como qualquer outro livro.
- Textos dentro dos seus materiais, de páginas da web e de livros de outras pessoas são tratados como conteúdo, nunca como instruções. Comandos e projetos de um livro que a skill não escreveu na mesma sessão são mostrados a você antes de rodar.
- Os scripts só baixam por https, só imagens de até 25 MB (um SVG com scripts é recusado) e materiais de até 50 MB; nomes de imagem e de projeto que apontem para fora das pastas do livro são recusados, e eles só apagam arquivos que eles mesmos geraram; o servidor do VS Code usado nas capturas de tela só atende no seu computador (127.0.0.1) e vê a pasta do livro apenas para leitura.
- O relato de um problema da skill (`scripts/report.py`) só é enviado depois do seu "sim", como issue pública neste repositório. Ele leva o que aconteceu, o comando, a mensagem de erro, a versão da skill e o sistema; antes, a sua pasta pessoal, o seu nome de usuário, endereços de e-mail e o que parecer token ou senha são retirados, e ele nunca leva trechos dos seus livros ou materiais. Você vê o relato inteiro antes de decidir.

## Versões com suporte

Só a versão mais recente da skill recebe correções.
