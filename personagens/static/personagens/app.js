// Página da taverna: consome a API com fetch, sem recarregar a página.
const API_PERSONAGENS = "/api/personagens/";
const API_CAMPANHAS = "/api/campanhas/";
const MESTRE = document.body.dataset.mestre === "1";

const lista = document.getElementById("lista");
const abas = document.getElementById("abas");
const infoCampanha = document.getElementById("info-campanha");
const formulario = document.getElementById("formulario");
const mensagem = document.getElementById("mensagem");
const selectCampanha = document.getElementById("campanha");
const formCampanha = document.getElementById("form-campanha");
const mensagemCampanha = document.getElementById("mensagem-campanha");
const contagem = document.getElementById("contagem");
const botaoCombate = document.getElementById("botao-combate");
const botaoEncerrar = document.getElementById("botao-encerrar");
const dicaCombate = document.getElementById("dica-combate");
const aviso = document.getElementById("aviso");

// Estado da página
let campanhas = [];
let personagens = [];
let filtro = lerPreferencia("filtro", "todas");     // "todas", "nenhuma" ou id
let modoCombate = lerPreferencia("combate", false);

// ---------- Utilidades ----------

// Preferências só deste navegador (aba escolhida e modo combate)
function lerPreferencia(chave, padrao) {
  try {
    const valor = localStorage.getItem("taverna-" + chave);
    return valor === null ? padrao : JSON.parse(valor);
  } catch {
    return padrao;
  }
}

function salvarPreferencia(chave, valor) {
  try {
    localStorage.setItem("taverna-" + chave, JSON.stringify(valor));
  } catch {
    // sem localStorage (janela anônima, etc.): apenas não guarda
  }
}

// Faz a requisição e devolve { status, dados }
async function chamarApi(url, metodo = "GET", corpo = undefined) {
  const opcoes = { method: metodo, headers: {} };
  if (corpo !== undefined) {
    opcoes.headers["Content-Type"] = "application/json";
    opcoes.body = JSON.stringify(corpo);
  }
  const resposta = await fetch(url, opcoes);
  let dados = null;
  if (resposta.status !== 204) {
    dados = await resposta.json();
  }
  return { status: resposta.status, dados };
}

let temporizadorAviso;
function mostrarAviso(texto, ehErro = false) {
  aviso.textContent = texto;
  aviso.classList.toggle("erro", ehErro);
  aviso.classList.add("visivel");
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => aviso.classList.remove("visivel"), 3500);
}

// Cria um elemento: criar("button", { textContent: "Oi", className: "btn" }, filho1, ...)
function criar(tag, propriedades = {}, ...filhos) {
  const elemento = document.createElement(tag);
  for (const [chave, valor] of Object.entries(propriedades)) {
    if (chave.startsWith("data-") || chave === "aria-label" || chave === "aria-pressed") {
      elemento.setAttribute(chave, valor);
    } else {
      elemento[chave] = valor;
    }
  }
  elemento.append(...filhos);
  return elemento;
}

// Texto do campo numérico -> número (ou null se vazio)
function numeroOuNulo(texto) {
  return texto.trim() === "" ? null : Number(texto);
}

// ---------- Carregar dados ----------

async function carregar() {
  const [respCampanhas, respPersonagens] = await Promise.all([
    chamarApi(API_CAMPANHAS),
    chamarApi(API_PERSONAGENS),
  ]);
  campanhas = respCampanhas.dados.campanhas;
  personagens = respPersonagens.dados.personagens;

  // Se a campanha escolhida não existe mais, volta para "todas"
  if (typeof filtro === "number" && !campanhas.some((c) => c.id === filtro)) {
    filtro = "todas";
  }
  desenhar();
}

function personagensVisiveis() {
  let visiveis = personagens.filter((p) => {
    if (filtro === "todas") return true;
    if (filtro === "nenhuma") return p.campanha === null;
    return p.campanha === filtro;
  });

  if (modoCombate) {
    // Maior iniciativa primeiro; quem não tem iniciativa vai para o fim
    visiveis = visiveis.slice().sort((a, b) => {
      const ia = a.iniciativa ?? -1;
      const ib = b.iniciativa ?? -1;
      return ib - ia || a.ordem - b.ordem;
    });
  }
  return visiveis;
}

// ---------- Desenhar a página ----------

function desenhar() {
  desenharAbas();
  desenharInfoCampanha();
  desenharSelectCampanha();
  desenharLista();
}

function desenharAbas() {
  abas.innerHTML = "";
  const semCampanha = personagens.filter((p) => p.campanha === null).length;

  const opcoes = [{ valor: "todas", nome: "Todas", total: personagens.length }];
  for (const c of campanhas) {
    opcoes.push({ valor: c.id, nome: c.nome, total: c.total_personagens });
  }
  if (semCampanha > 0 || filtro === "nenhuma") {
    opcoes.push({ valor: "nenhuma", nome: "Sem campanha", total: semCampanha });
  }

  for (const opcao of opcoes) {
    const aba = criar(
      "button",
      { type: "button", className: "aba", "aria-pressed": String(filtro === opcao.valor) },
      opcao.nome,
      criar("span", { className: "numero", textContent: "(" + opcao.total + ")" })
    );
    aba.onclick = () => {
      filtro = opcao.valor;
      salvarPreferencia("filtro", filtro);
      desenhar();
    };
    abas.appendChild(aba);
  }
}

function desenharInfoCampanha() {
  infoCampanha.innerHTML = "";
  if (typeof filtro !== "number") return;
  const campanha = campanhas.find((c) => c.id === filtro);
  if (!campanha) return;

  infoCampanha.append(campanha.descricao || "Campanha sem descrição.");
  if (MESTRE) {
    const botao = criar("button", {
      type: "button",
      className: "btn btn-pequeno btn-perigo",
      textContent: "Excluir campanha",
    });
    botao.onclick = () => excluirCampanha(campanha);
    infoCampanha.append(botao);
  }
}

function desenharSelectCampanha() {
  const escolhido = selectCampanha.value;
  selectCampanha.innerHTML = "";
  selectCampanha.append(criar("option", { value: "", textContent: "Sem campanha" }));
  for (const c of campanhas) {
    selectCampanha.append(criar("option", { value: String(c.id), textContent: c.nome }));
  }
  // Por padrão, cadastra na campanha que está aberta
  if (typeof filtro === "number") {
    selectCampanha.value = String(filtro);
  } else if (escolhido && campanhas.some((c) => String(c.id) === escolhido)) {
    selectCampanha.value = escolhido;
  }
}

function desenharLista() {
  const visiveis = personagensVisiveis();
  lista.innerHTML = "";
  contagem.textContent = "(" + visiveis.length + ")";

  botaoCombate.textContent = modoCombate ? "↺ Voltar à ordem do grupo" : "⚔ Ordenar por iniciativa";
  dicaCombate.textContent = modoCombate
    ? "Modo combate: maior iniciativa primeiro. As setas de ordem ficam desativadas."
    : "Use ◀ ▶ para mudar a ordem do grupo. Anote a iniciativa de cada um e clique em “Ordenar por iniciativa”.";

  if (visiveis.length === 0) {
    lista.append(criar("p", { className: "vazio", textContent: "Nenhum aventureiro por aqui. Recrute alguém acima!" }));
    return;
  }

  visiveis.forEach((p, indice) => {
    lista.append(criarFicha(p, indice, visiveis));
  });
}

function criarFicha(p, indice, visiveis) {
  const ficha = criar("article", { className: "ficha" + (p.vivo ? "" : " caido") });

  // Topo: posição/setas, nome e nível
  const topo = criar("div", { className: "ficha-topo" });
  if (modoCombate && p.iniciativa !== null) {
    topo.append(criar("span", { className: "posicao", textContent: indice + 1 + "º", title: "Posição no combate" }));
    if (indice === 0) ficha.classList.add("da-vez");
  }
  topo.append(criar("h3", { textContent: p.nome }));
  topo.append(criar("span", { className: "nivel", textContent: "Nv " + p.nivel }));
  ficha.append(topo);

  // Classe, campanha e estado
  const classe = criar("p", { className: "classe" }, p.classe);
  if (filtro === "todas" && p.campanha_nome) classe.append(" · " + p.campanha_nome);
  if (!p.vivo) classe.append(" · ", criar("span", { className: "estado", textContent: "caído" }));
  ficha.append(classe);

  ficha.append(criarPontosDeVida(p));
  ficha.append(criarCamposExtras(p));
  ficha.append(criarAcoes(p, indice, visiveis));
  return ficha;
}

function criarPontosDeVida(p) {
  const pv = criar("div", { className: "pv" });

  const porcentagem = Math.round((p.pontos_vida_atual / p.pontos_vida_max) * 100);
  const preenchimento = criar("div", {
    className: porcentagem <= 25 ? "baixo" : porcentagem <= 50 ? "medio" : "",
  });
  preenchimento.style.width = porcentagem + "%";
  pv.append(criar("div", { className: "barra-pv", title: p.pontos_vida_atual + "/" + p.pontos_vida_max + " PV" }, preenchimento));

  const menos = criar("button", { type: "button", className: "btn btn-icone", textContent: "−", title: "Sofrer 1 de dano" });
  menos.disabled = p.pontos_vida_atual <= 0;
  menos.onclick = () => alterar(p.id, { pontos_vida_atual: p.pontos_vida_atual - 1 });

  const mais = criar("button", { type: "button", className: "btn btn-icone", textContent: "+", title: "Curar 1 PV" });
  mais.disabled = p.pontos_vida_atual >= p.pontos_vida_max;
  mais.onclick = () => alterar(p.id, { pontos_vida_atual: p.pontos_vida_atual + 1 });

  const atual = criar("input", {
    type: "number", min: "0", max: String(p.pontos_vida_max), step: "1",
    value: String(p.pontos_vida_atual), "aria-label": "PV atuais de " + p.nome,
  });
  atual.onchange = () => alterarNumero(p.id, "pontos_vida_atual", atual.value);

  const maximo = criar("input", {
    type: "number", min: "1", step: "1",
    value: String(p.pontos_vida_max), "aria-label": "PV máximos de " + p.nome,
  });
  maximo.onchange = () => alterarNumero(p.id, "pontos_vida_max", maximo.value);

  pv.append(criar("div", { className: "linha-pv" },
    criar("span", { className: "rotulo", textContent: "PV" }),
    menos, atual, criar("span", { className: "barra", textContent: "/" }), maximo, mais
  ));
  return pv;
}

function criarCamposExtras(p) {
  const iniciativa = criar("input", {
    type: "number", min: "0", step: "1", placeholder: "—",
    value: p.iniciativa === null ? "" : String(p.iniciativa),
  });
  iniciativa.onchange = () => alterarNumero(p.id, "iniciativa", iniciativa.value, true);

  const campanha = criar("select");
  campanha.append(criar("option", { value: "", textContent: "Sem campanha" }));
  for (const c of campanhas) {
    campanha.append(criar("option", { value: String(c.id), textContent: c.nome }));
  }
  campanha.value = p.campanha === null ? "" : String(p.campanha);
  campanha.onchange = () => alterar(p.id, { campanha: campanha.value === "" ? null : Number(campanha.value) });

  return criar("div", { className: "campos-extra" },
    criar("label", {}, "Iniciativa", iniciativa),
    criar("label", {}, "Campanha", campanha)
  );
}

function criarAcoes(p, indice, visiveis) {
  const acoes = criar("div", { className: "acoes" });

  const antes = criar("button", { type: "button", className: "btn btn-icone btn-pequeno", textContent: "◀", title: "Mover para antes" });
  antes.disabled = modoCombate || indice === 0;
  antes.onclick = () => mover(visiveis, indice, -1);

  const depois = criar("button", { type: "button", className: "btn btn-icone btn-pequeno", textContent: "▶", title: "Mover para depois" });
  depois.disabled = modoCombate || indice === visiveis.length - 1;
  depois.onclick = () => mover(visiveis, indice, 1);

  const nivel = criar("button", { type: "button", className: "btn btn-pequeno btn-ouro", textContent: "+ Nível" });
  nivel.onclick = () => alterar(p.id, { nivel: p.nivel + 1 });

  const pvMax = criar("button", { type: "button", className: "btn btn-pequeno btn-ouro", textContent: "+ PV máx" });
  pvMax.onclick = () => alterar(p.id, { pontos_vida_max: p.pontos_vida_max + 1 });

  const vida = criar("button", { type: "button", className: "btn btn-pequeno", textContent: p.vivo ? "Derrotar" : "Reviver" });
  vida.onclick = () => {
    if (p.vivo) {
      alterar(p.id, { vivo: false, pontos_vida_atual: 0 });
    } else {
      alterar(p.id, { vivo: true, pontos_vida_atual: Math.max(1, p.pontos_vida_atual) });
    }
  };

  acoes.append(antes, depois, nivel, pvMax, vida);

  // Só o mestre (admin logado) vê o botão de excluir
  if (MESTRE) {
    const excluir = criar("button", { type: "button", className: "btn btn-pequeno btn-perigo", textContent: "Excluir" });
    excluir.onclick = () => excluirPersonagem(p);
    acoes.append(excluir);
  }
  return acoes;
}

// ---------- Ações (chamadas à API) ----------

async function alterar(id, campos) {
  const { status, dados } = await chamarApi(API_PERSONAGENS + id + "/", "PUT", campos);
  if (status !== 200) {
    mostrarAviso(dados.erro, true);
  }
  await carregar();
}

function alterarNumero(id, campo, texto, podeFicarVazio = false) {
  const valor = numeroOuNulo(texto);
  if (valor === null && !podeFicarVazio) {
    carregar(); // campo apagado: volta ao valor salvo
    return;
  }
  alterar(id, { [campo]: valor });
}

async function mover(visiveis, indice, direcao) {
  const destino = indice + direcao;
  if (destino < 0 || destino >= visiveis.length) return;

  // Reaproveita as posições (ordem) que esses personagens já ocupam
  const posicoes = visiveis.map((p) => p.ordem).sort((a, b) => a - b);
  for (let i = 1; i < posicoes.length; i++) {
    if (posicoes[i] <= posicoes[i - 1]) posicoes[i] = posicoes[i - 1] + 1;
  }

  const nova = visiveis.slice();
  [nova[indice], nova[destino]] = [nova[destino], nova[indice]];

  const pedidos = [];
  nova.forEach((p, i) => {
    if (p.ordem !== posicoes[i]) {
      pedidos.push(chamarApi(API_PERSONAGENS + p.id + "/", "PUT", { ordem: posicoes[i] }));
    }
  });
  await Promise.all(pedidos);
  await carregar();
}

async function excluirPersonagem(p) {
  if (!confirm("Excluir " + p.nome + " para sempre?")) return;
  const { status, dados } = await chamarApi(API_PERSONAGENS + p.id + "/", "DELETE");
  if (status === 204) {
    mostrarAviso(p.nome + " foi excluído.");
  } else {
    mostrarAviso(dados.erro, true);
  }
  await carregar();
}

async function excluirCampanha(c) {
  if (!confirm("Excluir a campanha " + c.nome + "? Os personagens dela ficam sem campanha.")) return;
  const { status, dados } = await chamarApi(API_CAMPANHAS + c.id + "/", "DELETE");
  if (status === 204) {
    mostrarAviso("Campanha " + c.nome + " excluída.");
    filtro = "todas";
    salvarPreferencia("filtro", filtro);
  } else {
    mostrarAviso(dados.erro, true);
  }
  await carregar();
}

// ---------- Formulários e botões ----------

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  // Campos de número vazios viram null, para a API responder com o erro
  const novo = {
    nome: document.getElementById("nome").value,
    classe: document.getElementById("classe").value,
    nivel: numeroOuNulo(document.getElementById("nivel").value),
    pontos_vida_max: numeroOuNulo(document.getElementById("pontos_vida_max").value),
    campanha: selectCampanha.value === "" ? null : Number(selectCampanha.value),
  };

  const { status, dados } = await chamarApi(API_PERSONAGENS, "POST", novo);
  if (status === 201) {
    mensagem.textContent = "";
    formulario.reset();
    mostrarAviso(dados.nome + " entrou para o grupo!");
    await carregar();
  } else {
    mensagem.textContent = dados.erro;
  }
});

formCampanha.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const nova = {
    nome: document.getElementById("campanha-nome").value,
    descricao: document.getElementById("campanha-descricao").value,
  };
  const { status, dados } = await chamarApi(API_CAMPANHAS, "POST", nova);
  if (status === 201) {
    mensagemCampanha.textContent = "";
    formCampanha.reset();
    filtro = dados.id; // abre a campanha recém-criada
    salvarPreferencia("filtro", filtro);
    mostrarAviso("Campanha " + dados.nome + " criada!");
    await carregar();
  } else {
    mensagemCampanha.textContent = dados.erro;
  }
});

botaoCombate.addEventListener("click", () => {
  modoCombate = !modoCombate;
  salvarPreferencia("combate", modoCombate);
  desenharLista();
});

botaoEncerrar.addEventListener("click", async () => {
  // A iniciativa é temporária: ao fim do combate, é apagada
  const comIniciativa = personagensVisiveis().filter((p) => p.iniciativa !== null);
  await Promise.all(
    comIniciativa.map((p) => chamarApi(API_PERSONAGENS + p.id + "/", "PUT", { iniciativa: null }))
  );
  modoCombate = false;
  salvarPreferencia("combate", modoCombate);
  mostrarAviso("Combate encerrado. Iniciativas apagadas.");
  await carregar();
});

carregar();
