<!-- translation-of: faq.md sha256:a2fdd2e136f6 -->
# Perguntas frequentes

[English](faq.md) | **Português**

## Conteúdo

- [Qual plano do Claude eu preciso?](#qual-plano-do-claude-eu-preciso)
- [App do Claude ou Claude Code?](#app-do-claude-ou-claude-code)
- [Como atualizo ou removo o Syllabook?](#como-atualizo-ou-removo-o-syllabook)
- [Quanto custa um livro?](#quanto-custa-um-livro)
- [Posso parar e continuar depois?](#posso-parar-e-continuar-depois)
- [Dá para usar sem GitHub?](#dá-para-usar-sem-github)
- [Meus materiais ficam privados?](#meus-materiais-ficam-privados)
- [Posso editar um livro à mão?](#posso-editar-um-livro-à-mão)
- [Que temas e idiomas funcionam?](#que-temas-e-idiomas-funcionam)
- [Posso traduzir um livro?](#posso-traduzir-um-livro)
- [O código dos livros é testado?](#o-código-dos-livros-é-testado)
- [De onde vêm as imagens?](#de-onde-vêm-as-imagens)
- [Achei um erro num livro. E agora?](#achei-um-erro-num-livro-e-agora)

## Qual plano do Claude eu preciso?

- **App do Claude** (claude.ai, desktop): qualquer plano, inclusive o grátis, com a execução de código ligada: **Configurações → Capacidades → Execução de código e criação de arquivos** (no app em inglês: *Settings → Capabilities → Code execution and file creation*). Nos planos Team e Enterprise, um administrador pode ter desligado o envio de skills.
- **Claude Code:** uma conta Pro, Max, Ultra, Team, Enterprise ou Console. O plano grátis não inclui o Claude Code.

## App do Claude ou Claude Code?

Os dois escrevem o mesmo livro. A diferença é o que o Claude consegue executar enquanto escreve:

| | App do Claude | Claude Code |
| --- | --- | --- |
| Instalação | enviar o `syllabook.zip` uma vez | dois comandos no terminal |
| Código e comandos do livro | rodam na sandbox do Claude; o que precisa da sua máquina (Docker, servidores, hardware) você roda e cola a saída | rodam no seu computador, com a saída real |
| Melhor para | idiomas, habilidades práticas, conhecimento geral | livros de tecnologia |

No Windows, use o Claude Code dentro do [WSL 2](integrations/wsl.pt-BR.md), para que os comandos de Linux também rodem.

## Como atualizo ou removo o Syllabook?

- **Claude Code:** com o auto-update ligado no marketplace `syllabook` (veja [Instalar](../README.pt-BR.md#instalar)), as versões novas chegam sozinhas. Para atualizar à mão, rode `claude plugin marketplace update syllabook` e depois `claude plugin update syllabook@syllabook`, e reinicie o Claude Code. Para remover: `claude plugin uninstall syllabook@syllabook`.
- **App do Claude:** ele não se atualiza sozinho: baixe o `syllabook.zip` novo da [versão mais recente](https://github.com/Joshpcbrrj/syllabook/releases/latest) e envie na seção de Skills das configurações, no lugar do antigo. Para remover, apague a skill nessa mesma seção.

Os seus livros não são afetados: eles ficam na sua biblioteca, não na skill. O que mudou em cada versão está no [CHANGELOG](../CHANGELOG.md) (em inglês).

## Quanto custa um livro?

Num plano por assinatura (Pro, Max...), o livro não custa nada além do plano: ele gasta os seus limites de uso. Um livro longo costuma levar mais de uma sessão; quando um limite acaba, continue depois que ele renovar.

Como referência, em preço de API (Claude Code, novembro de 2026): o livro *Docker do zero* inteiro (12 capítulos, com cada comando rodado de verdade, mais as partes fixas, a capa e a auditoria) custou US$ 15,31, com a ementa feita pelo Opus (US$ 0,90) e o resto pelo Sonnet, perto de US$ 1 por capítulo. A maior parte do custo de uma sessão é a própria conversa, então um livro feito em algumas sessões curtas sai bem mais barato que uma conversa longa: a skill sugere uma conversa nova a cada poucos capítulos.

## Posso parar e continuar depois?

Sim. O progresso de cada livro fica salvo no `book.yaml` dele, capítulo por capítulo. Numa conversa nova, peça para continuar o livro (por exemplo, "continue o meu livro de Docker Compose") e o Syllabook retoma do próximo capítulo.

## Dá para usar sem GitHub?

Dá. Sem conexão, o Syllabook entrega um zip com o livro, com as pastas no mesmo formato de uma biblioteca. Você pode guardar o zip, ler o Markdown ou enviá-lo para um repositório depois ([guia do GitHub](integrations/github.pt-BR.md)).

## Meus materiais ficam privados?

- **Os seus arquivos** (PDFs, documentos, páginas do Notion que você manda para aprimorar) servem só de fonte. Eles nunca são publicados.
- **Os livros** vão para a sua biblioteca. O [modelo de biblioteca](https://github.com/Joshpcbrrj/syllabook-library) é um repositório público, porque o GitHub Pages e as releases são grátis assim. Você pode deixá-lo privado, mas aí o site exige um plano pago do GitHub.
- **A conversa** segue as configurações de privacidade da sua conta do Claude.

## Posso editar um livro à mão?

Pode. Os capítulos são arquivos Markdown comuns, em `chapters/`. Depois de editar, peça ao Syllabook para conferir e publicar o livro: ele roda a auditoria de novo, refaz o EPUB e o site e aponta o que a sua edição quebrou (uma seção faltando, um link quebrado).

## Que temas e idiomas funcionam?

- **Temas:** qualquer um. O Syllabook adapta a didática a quatro perfis: programação e matemática, idiomas, habilidades práticas (música, eletrônica...) e conhecimento geral (como história). Para um tema que não se encaixa em nenhum, ele monta um método próprio e o explica no parecer.
- **Idiomas:** a conversa e o livro podem ser em qualquer idioma. Português do Brasil e inglês têm guias de estilo próprios; nos outros idiomas, ele escreve com naturalidade e avisa que ainda não há guia de estilo.

## Posso traduzir um livro?

Pode, para qualquer idioma; a versão nova é adaptada para quem vai ler (nomes, moedas, exemplos), não traduzida palavra por palavra. O original pode ser:

- **um livro da sua biblioteca** (a pasta dele, ou a biblioteca no GitHub): a melhor escolha, porque mantém o código, os diagramas e as fontes;
- **um zip que o Syllabook entregou;**
- **um arquivo que você manda:** PDF, EPUB, DOCX, ODT, RTF, HTML, uma página da web ou Markdown (PowerPoint e imagens pelo [Docling](integrations/docling.pt-BR.md), que também mantém as tabelas de um PDF). O Syllabook pergunta antes se você escreveu o livro ou se a licença dele permite traduções; um livro com todos os direitos reservados não é traduzido, mas pode servir de fonte para um livro novo seu (Aprimorar).

Um livro que ensina um idioma, traduzido para esse mesmo idioma (um livro em português que ensina inglês, para o inglês), é outro livro: o Syllabook pergunta para quem ele é antes de começar.

## O código dos livros é testado?

É. Cada comando e cada trecho de código é executado enquanto o capítulo é escrito, e o livro mostra a saída real. O que não dá para rodar (um comando de outro sistema operacional, por exemplo) sai marcado como "não executado" no texto. Por isso o Claude Code, e o WSL 2 no Windows, rendem livros de tecnologia melhores.

## De onde vêm as imagens?

- **Diagramas:** desenhados em SVG pelos scripts da skill, a partir de uma descrição da estrutura (blocos, fluxos, linhas do tempo, acordes...).
- **Ilustrações:** desenhos simples para uma analogia ou uma cena imaginada (uma caixa de correio para a fila de commits, por exemplo). O Claude os escreve como código SVG, e um script confere que são só formas e texto, nas cores do livro.
- **Fotos:** só com licença livre (domínio público, CC0, CC BY, CC BY-SA), do Wikimedia Commons e do Openverse, com o autor e a licença embaixo da imagem.
- **Capturas de tela:** da aplicação do livro rodando de verdade e do VS Code (precisa do Docker ou do code-server no seu computador; a skill pergunta antes de baixar qualquer coisa). Capturas de outros programas (um instalador, o Docker Desktop, o Gerenciador de Tarefas) vêm da documentação do próprio fabricante no GitHub, quando a licença permite reutilizar; quando não há, o passo fica escrito em texto. Você nunca precisa tirar capturas de tela.

O Syllabook não usa modelos que geram imagens e nunca finge uma foto ou captura de tela real.

## Achei um erro num livro. E agora?

- **No seu próprio livro:** peça ao Syllabook para corrigir ("no capítulo 3 do meu livro de Docker, a porta está errada"). Ele muda o capítulo, confere de novo e registra a mudança.
- **No funcionamento da skill:** abra uma [issue](https://github.com/Joshpcbrrj/syllabook/issues/new/choose) no repositório do Syllabook.
- **Quando a skill tropeça num problema dela mesma** (um script que falha, um aviso da auditoria que está errado), ela avisa no resumo final e mostra o relato inteiro: o que aconteceu, o comando, a mensagem de erro, a versão da skill e o sistema. A sua pasta pessoal, o seu nome de usuário, endereços de e-mail e o que parecer senha ou token são retirados, e o relato nunca leva trechos do seu livro ou dos seus materiais. Ele só é enviado se você disser que sim: como issue aberta com o seu login do GitHub no Claude Code, ou como um link para você clicar no app do Claude. O relato vai para o [repositório do Syllabook](https://github.com/Joshpcbrrj/syllabook/issues), que é público.
