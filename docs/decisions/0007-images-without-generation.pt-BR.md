<!-- translation-of: 0007-images-without-generation.md sha256:10c16e19cb38 -->
# 7. Imagens: diagramas, fotos com licença livre e capturas reais, sem geração de imagens

[English](0007-images-without-generation.md) | **Português**

**Situação:** aceita · **Origem:** `plano/PLANO.md §10`

## Contexto

Imagens geradas podem parecer reais sem ser, muitas vezes trazem texto errado e exigem APIs pagas e acesso à rede.

## Decisão

As imagens são diagramas SVG desenhados por script a partir de uma especificação, ilustrações SVG simples para analogias (escritas como código e conferidas por um script), fotos com licença livre (domínio público, CC0, CC BY, CC BY-SA) com o crédito, e capturas de tela da aplicação de verdade. Sem modelos que geram imagens e sem logotipos ou marcas de terceiros.

## Consequências

Toda imagem real tem autor, licença e link no `img/CREDITS.md` e na legenda. Uma foto ou captura de tela real nunca é falsificada.
