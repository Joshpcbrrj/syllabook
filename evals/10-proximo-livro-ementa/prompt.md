---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill, Write, WebSearch, WebFetch]
tags: [curto]
---

Na minha biblioteca do Syllabook tenho o livro "Git e GitHub essencial", já pronto e publicado. Nesta conversa estou sem shell, sem GitHub e sem Notion, então rodei eu mesmo `python scripts/book.py base improved-materials/git-e-github-essencial` e saiu isto:

```json
{
 "book": {
  "title": "Git e GitHub essencial",
  "slug": "git-e-github-essencial",
  "folder": "improved-materials/git-e-github-essencial",
  "language": "pt-BR"
 },
 "level": {
  "start": "iniciante",
  "end": "intermediário"
 },
 "goal": "Versionar um projeto com Git, desfazer erros com segurança, trabalhar com branches e remotos e contribuir no GitHub por fork e pull request",
 "track": {
  "name": "ferramentas-do-dev",
  "order": 1
 },
 "covers": [
  "git",
  "github",
  "version-control",
  "branching",
  "pull-request",
  "github-pages"
 ],
 "concepts": [
  "version-control",
  "distributed-vcs",
  "git-vs-github",
  "git-config",
  "identity",
  "credentials",
  "snapshot",
  "three-areas",
  "file-status",
  "gitignore",
  "commit",
  "commit-message",
  "history",
  "head",
  "restore",
  "amend",
  "detached-head",
  "reset",
  "revert",
  "reflog",
  "branch",
  "stash",
  "merge",
  "conflict",
  "rebase",
  "interactive-rebase",
  "remote",
  "bare-repo",
  "push-pull",
  "tracking-branch",
  "tag",
  "collaborator",
  "issue",
  "fork",
  "pull-request",
  "team-flow",
  "markdown",
  "github-pages",
  "gist"
 ],
 "chapters": [
  {
   "n": 1,
   "title": "Por que controlar versões",
   "summary": "Problema das cópias 'final' (cardápio da lanchonete) resolvido pelo histórico: commit, autor, data, mensagem, diff lido de um git log real (commits ce3dc3c,..."
  },
  {
   "n": 2,
   "title": "Instalação, identidade e credenciais",
   "summary": "Instalação (Windows instalador com Git Bash e GCM, macOS brew, Debian apt-get; Git 2.56, mínimo 2.23). git config em três níveis (system, global, local; o mais..."
  },
  {
   "n": 3,
   "title": "Como o Git pensa",
   "summary": "Nasce o projeto receitas (index.html, receitas/bolo-de-cenoura.md): git init e a pasta .git; commit por dentro com git cat-file (tree, blob, hash, pai),..."
  },
  {
   "n": 4,
   "title": "Commits e histórico",
   "summary": "Commits como unidades de mudança: brigadeiro do Bruno com --author (autor × committer), a armadilha do git commit -am com arquivo novo. Mensagens: título até..."
  },
  {
   "n": 5,
   "title": "Desfazendo erros com segurança",
   "summary": "Diagrama de decisão 'o que desfazer'. git restore (descarta edição; captura do VS Code com Discard Changes), --staged (lista-de-compras.txt), --source=9a16b95...."
  },
  {
   "n": 6,
   "title": "Branches, stash e merge",
   "summary": "Branch como ponteiro (cat .git/refs/heads/sobremesas = hash, 41 bytes); analogia do marcador com etiqueta no álbum. git switch (mousse some da pasta na main),..."
  },
  {
   "n": 7,
   "title": "Rebase e histórico limpo",
   "summary": "Rebase × merge com a branch bebidas (4f9e111/172b51d viram 748e984/036c36f; author × committer; ORIG_HEAD; merge fast-forward); analogia das fotos tiradas de..."
  },
  {
   "n": 8,
   "title": "Repositórios remotos",
   "summary": "Remoto de treino com git init --bare receitas.git (recusa de push em repositório normal). remote add/-v/set-url/rename; push -u (upstream); clone do Bruno com..."
  },
  {
   "n": 9,
   "title": "Colaborando no GitHub",
   "summary": "Colaboradores (Settings → Collaborators → Add people; conta pessoal: mesmo acesso; só gente de confiança). Issue #1 da Carla (pão de queijo sem sal): Submit..."
  },
  {
   "n": 10,
   "title": "Projeto: currículo online",
   "summary": "Projeto novo: currículo da Ana em ana-ribeiro.github.io (index.html, estilo.css, README.md; commits 2d3855c e 82ecf4a, remoto bare no lugar do GitHub)...."
  }
 ],
 "next_steps": [
  {
   "step": 1,
   "title": "GitHub Actions (CI/CD)",
   "why": "Fazer o GitHub testar e publicar o projeto sozinho a cada push e a cada pull request",
   "topics": [
    "workflows em YAML",
    "testes automáticos em pull requests",
    "deploy do GitHub Pages por Actions",
    "segredos do repositório"
   ]
  },
  {
   "step": 2,
   "title": "git bisect e git worktree",
   "why": "Achar o commit que introduziu um bug e trabalhar em duas branches ao mesmo tempo sem stash",
   "topics": [
    "busca binária com git bisect",
    "git bisect run com um teste",
    "várias pastas de trabalho com git worktree"
   ]
  },
  {
   "step": 3,
   "title": "Commits assinados (GPG/SSH)",
   "why": "Provar que os seus commits e tags vieram mesmo de você, com o selo Verified no GitHub",
   "topics": [
    "assinatura com chave SSH",
    "assinatura com GPG",
    "git log --show-signature",
    "exigir commits assinados na branch protegida"
   ]
  },
  {
   "step": 4,
   "title": "Conventional Commits e versionamento semântico",
   "why": "Padronizar as mensagens da equipe e numerar as versões de um jeito que diz o que mudou",
   "topics": [
    "tipos feat, fix e chore",
    "MAJOR.MINOR.PATCH",
    "changelog gerado do histórico",
    "tags e releases por versão"
   ]
  }
 ],
 "for_the_new_book": {
  "level_start": "intermediário",
  "prerequisites": [
   "git-e-github-essencial"
  ],
  "track": {
   "name": "ferramentas-do-dev",
   "order": 2
  }
 }
}
```

Quero o próximo livro da trilha seguindo o passo 1 (GitHub Actions). Ainda não aprovei nada.
