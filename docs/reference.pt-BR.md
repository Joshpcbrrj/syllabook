<!-- translation-of: reference.md sha256:c95a6b28ec7a -->
# Referência: `book.yaml` e `library.yaml`

[English](reference.md) | **Português**

Dois arquivos YAML guardam tudo o que o Syllabook sabe dos seus livros. Raramente você precisa editá-los: a skill os escreve enquanto vocês conversam. Esta página serve para quando você quiser ler um deles, corrigir um detalhe à mão ou entender o que um script fez.

Depois de editar um `book.yaml` à mão, peça ao Syllabook para conferir o livro ou rode você mesmo `python scripts/book.py validate <book.yaml>`: ele aponta o que está errado, com o nome do campo.

## Conteúdo

- [Onde ficam os arquivos](#onde-ficam-os-arquivos)
- [`book.yaml`: o livro](#bookyaml-o-livro)
- [`library.yaml`: a biblioteca](#libraryyaml-a-biblioteca)

## Onde ficam os arquivos

```text
minha-biblioteca/
├── library.yaml                    configurações da biblioteca inteira
├── created-books/<slug>/book.yaml  um livro criado a partir de um tema
├── improved-materials/<slug>/...   um material seu que foi aprimorado
└── translated-books/<slug>-<idioma>/ uma tradução (seja qual for a pasta do original)
```

## `book.yaml`: o livro

É o contrato e a memória do livro: a ementa aprovada, as suas escolhas e o progresso.

### Campos obrigatórios

O `validate` recusa um livro sem algum destes.

| Campo | O que é |
| --- | --- |
| `title` | o título do livro |
| `slug` | o nome da pasta: letras minúsculas, números e hífens (`docker-compose-na-pratica`) |
| `origin` | `created` (a partir de um tema) ou `improved` (a partir do seu material); uma tradução mantém o do original |
| `language` | o idioma do livro (`pt-BR`, `en`...) |
| `profiles` | 1 ou 2 entre `stem`, `languages`, `skills` e `knowledge`: o jeito de ensinar do livro |
| `level` | `{start, end}`, no idioma do livro (`{start: iniciante, end: intermediário}`) |
| `audience` | para quem é o livro |
| `goal` | o que o leitor vai conseguir fazer no fim |
| `sources` | as fontes: cada uma `{title, url, checked}`, com `checked` no formato `AAAA-MM-DD`, o dia em que a página foi aberta; uma fonte que não abriu fica sem `checked` (aviso), e enciclopédia não é fonte (erro) |
| `approved_on` | a data em que você aprovou a ementa; vazio enquanto é rascunho |
| `concepts` | o grafo de conceitos (abaixo) |
| `chapters` | os capítulos: `n` (1, 2, 3... sem pular), `title`, `goal`, `topics` e `minutes` |

### O grafo de conceitos

Cada conceito que o livro ensina aparece uma vez: `{id, name, chapter, depends}`. O `id` é um rótulo curto (`project-network`); o `name` fica no idioma do livro. O `depends` lista os conceitos de que ele precisa, e o `validate` recusa um conceito que dependa de outro ensinado num capítulo posterior. Um conceito ensinado por um livro anterior se escreve `<slug>:<id>` (`docker-do-zero:container`), e esse livro precisa estar em `prerequisites`.

### Campos opcionais

| Campo | O que é |
| --- | --- |
| `subtitle` | vai na capa e no site |
| `conversation_language` | o idioma em que o Syllabook conversa com você, se for diferente do livro |
| `choices` | `{images: real ou svg, reading: large ou small}`: imagens reais onde ajudam ou só diagramas; telas grandes ou leitor de e-book pequeno |
| `prerequisites` | livros que o leitor deve conhecer antes: slugs de livros da biblioteca ou texto livre |
| `track` | `{name, order}`: uma série de livros, na ordem de leitura; a página inicial da biblioteca lista os livros por trilha |
| `continues` | `{book, step}`: num próximo livro, o livro anterior e qual dos próximos passos dele este segue (o `book` também precisa estar em `prerequisites`) |
| `next_steps` | de 2 a 4 livros para depois, cada um `{title, why, topics}`; eles aparecem no fim do último capítulo |
| `covers` | rótulos curtos do que o livro cobre (`compose`, `compose-yaml`), usados para comparar os livros de uma trilha |
| `reference_version` | a versão em que o livro se baseia, para temas que mudam (`Docker Compose v5.6`) |
| `review_by` | o mês até quando revisar o livro (`2027-11`); as listas da biblioteca avisam depois dele |
| `edition` | a edição atual (`1.0`; `1.3` depois de uma revisão; `1.3.1` só para errata) |
| `human_review` | `true` quando uma pessoa revisou o conteúdo |

Os materiais aprimorados também têm `original` (de onde veio o material; nunca é publicado), `promise` (`{goal, audience, level, sequence}` do original), `new_content_pct` e, em cada capítulo, `sources_original` (as seções do original de onde ele vem). As traduções têm `translation_of` (o slug do original) e `glossary`; o original ganha `translations`.

### Preenchidos pelo Syllabook

Só edite estes se souber por quê:

| Campo | Quem escreve |
| --- | --- |
| `progress` | `book.py done`: cada capítulo terminado, com a data, a data da releitura nativa e o resumo |
| `reread` | `book.py reread`: capítulos relidos e ainda não marcados como prontos, cada um com o código que o `book.py done --reread` pede (some quando eles ficam prontos) |
| `changes` | a skill, a cada mudança depois da aprovação: `{date, what, why}` |
| `handoff` | `book.py handoff`: o que ficou pendente para a próxima conversa |
| `editions`, `reviewed_on` | `book.py edition`, no fim de uma revisão |

## `library.yaml`: a biblioteca

Fica na raiz do repositório da sua biblioteca. A skill o preenche na primeira vez que monta a biblioteca.

| Campo | O que é |
| --- | --- |
| `author` | o seu nome, como vai nas capas e no EPUB |
| `repository` | `<dono>/<nome>` da biblioteca no GitHub; dele saem os links do site e do EPUB |
| `branch` | o branch em que os livros são publicados (`main`) |
| `commit_name`, `commit_email` | o nome e o e-mail dos commits da skill; use o endereço noreply do GitHub (`<usuário>@users.noreply.github.com`), nunca um e-mail pessoal |
| `default_language` | o idioma da conversa e dos livros novos; `auto` = o idioma da sua primeira mensagem |
| `content_license`, `code_license` | as licenças do texto (`CC BY-SA 4.0`) e do código (`MIT`) |
| `epub_release` | a release do GitHub que guarda os EPUBs (`epubs`) |
| `notion_page` | a página do Notion para onde os livros são copiados; a skill pergunta na primeira vez |
| `site_title` | opcional: o título do site (padrão: o nome do repositório) |
| `tracks` | opcional: os nomes de exibição das trilhas (`{devops: "DevOps"}`); sem ele, `devops` aparece como "Devops" |
