// Conteúdo de referência sobre a legislação do CAC (Colecionador, Atirador
// Desportivo e Caçador), disponível offline. É um RESUMO ORIENTATIVO — os
// números exatos (quantitativos de armas/munição, prazos e taxas) mudam por
// decreto e portaria; sempre confirme na norma vigente pelos links oficiais.
//
// Fontes oficiais principais:
//  - Decreto 11.615/2023 (Regulamento do Estatuto do Desarmamento) — Planalto
//  - Portarias do Comando do Exército (SFPC/DFPC) — gov.br/defesa e eb.mil.br
//  - Lei 10.826/2003 (Estatuto do Desarmamento) — Planalto
//
// O objetivo é orientar e organizar — não substitui a norma nem assessoria
// jurídica.

export type LegItem = {
  id: string;
  category: string;
  title: string;
  summary: string;
  points: string[];
  source?: { label: string; url: string };
};

export const LEG_DISCLAIMER =
  "Resumo orientativo, não é assessoria jurídica. Quantitativos, prazos e taxas " +
  "mudam por decreto e portaria — confirme sempre na norma vigente pelos links oficiais.";

export const LEG_ITEMS: LegItem[] = [
  {
    id: "cr",
    category: "Registros",
    title: "CR — Certificado de Registro",
    summary:
      "Documento que habilita a pessoa a exercer a atividade de CAC. É emitido " +
      "pelo Exército (SFPC/DFPC), não pela Polícia Federal.",
    points: [
      "Habilita uma ou mais categorias: Colecionador, Atirador Desportivo e/ou Caçador.",
      "Tem prazo de validade — acompanhe o vencimento e renove com antecedência.",
      "É pré-requisito para adquirir e registrar armas na condição de CAC.",
      "Cada categoria tem exigências próprias (ex.: filiação a clube/entidade para o atirador).",
    ],
    source: {
      label: "Decreto 11.615/2023 (Planalto)",
      url: "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/decreto/d11615.htm",
    },
  },
  {
    id: "craf",
    category: "Registros",
    title: "CRAF — Certificado de Registro de Arma de Fogo",
    summary:
      "Registro individual de cada arma no Exército. Acompanha a arma e comprova " +
      "sua origem e propriedade.",
    points: [
      "Cada arma tem seu CRAF — mantenha o documento junto ao acervo.",
      "Deve ser apresentado em fiscalização e no transporte, junto da Guia de Tráfego.",
      "Transferência de propriedade exige atualização do registro.",
      "Fique atento ao prazo de validade/recadastramento definido na norma vigente.",
    ],
    source: {
      label: "Portarias SFPC/DFPC (gov.br/defesa)",
      url: "https://www.gov.br/defesa/pt-br",
    },
  },
  {
    id: "habitualidade",
    category: "Atividade",
    title: "Habitualidade do atirador",
    summary:
      "O atirador desportivo precisa comprovar prática regular de tiro para manter " +
      "a atividade e os benefícios do registro.",
    points: [
      "A comprovação é feita por registros de treino/competição no clube ou entidade.",
      "A frequência mínima e o período de apuração são definidos por portaria — confira a vigente.",
      "Guarde comprovantes (planilhas, súmulas, declarações do clube).",
      "Use a aba Habitualidades para contar sua frequência por equipamento e calibre.",
    ],
    source: {
      label: "Portarias do Comando do Exército",
      url: "https://www.gov.br/defesa/pt-br",
    },
  },
  {
    id: "gt",
    category: "Transporte",
    title: "GT — Guia de Tráfego",
    summary:
      "Autorização para transportar armas e munições. É o documento que legaliza o " +
      "deslocamento do acervo (ex.: de casa ao clube).",
    points: [
      "Transporte a arma descarregada e, em regra, em compartimento separado da munição.",
      "Leve a GT junto do CRAF de cada arma transportada.",
      "Há GT de trânsito eventual e modalidades de maior prazo — verifique a que se aplica.",
      "Cadastre GT e validade no Acervo para receber alertas de renovação.",
    ],
    source: {
      label: "Decreto 11.615/2023 (Planalto)",
      url: "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/decreto/d11615.htm",
    },
  },
  {
    id: "quantitativos",
    category: "Aquisição",
    title: "Quantitativos de armas e munição",
    summary:
      "A quantidade de armas e de munição que o CAC pode adquirir e manter é limitada " +
      "e varia conforme a categoria e a norma vigente.",
    points: [
      "Os limites por categoria (colecionador, atirador, caçador) são diferentes.",
      "Munição também tem controle de aquisição por calibre e período.",
      "Esses números MUDARAM entre decretos — não decore valores antigos, confirme o atual.",
      "Registre compras e estoque no Inventário para manter o controle organizado.",
    ],
    source: {
      label: "Decreto 11.615/2023 (Planalto)",
      url: "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/decreto/d11615.htm",
    },
  },
  {
    id: "orgaos",
    category: "Geral",
    title: "Quem regula: Exército × Polícia Federal",
    summary:
      "A atividade de CAC é regulada e fiscalizada pelo Comando do Exército; a posse e " +
      "o porte civis comuns ficam com a Polícia Federal.",
    points: [
      "CAC: registro, acervo e transporte pelo Exército (SFPC/DFPC e SisGCorp).",
      "Posse/porte civil comum: Polícia Federal (Sinarm).",
      "As regras e os sistemas são distintos — não misture os dois regimes.",
      "Dúvidas formais: procure o SFPC da sua região.",
    ],
    source: {
      label: "Lei 10.826/2003 (Estatuto do Desarmamento)",
      url: "https://www.planalto.gov.br/ccivil_03/leis/2003/l10.826.htm",
    },
  },
];

export const LEG_CATEGORIES = [...new Set(LEG_ITEMS.map((i) => i.category))];
