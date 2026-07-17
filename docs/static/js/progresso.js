// Checklist de pre-aula: guarda o progresso so no navegador do aluno
// (localStorage), sem servidor, sem conta, sem envio de dado nenhum.
// Por isso o progresso e por aparelho/navegador - nao sincroniza entre
// celular e notebook, e o professor nao tem acesso a esse dado.
(function () {
  var PREFIX = "minhas-aulas:preaula:";

  function chave(aulaId) {
    return PREFIX + aulaId;
  }

  function marcarNaPropriaAula() {
    var checkbox = document.querySelector("[data-preaula-checkbox]");
    if (!checkbox) return;
    var id = checkbox.getAttribute("data-aula-id");
    checkbox.checked = localStorage.getItem(chave(id)) === "1";
    checkbox.addEventListener("change", function () {
      if (checkbox.checked) {
        localStorage.setItem(chave(id), "1");
      } else {
        localStorage.removeItem(chave(id));
      }
    });
  }

  function marcarNaListaDeAulas() {
    var itens = document.querySelectorAll("[data-aula-id]");
    itens.forEach(function (el) {
      var id = el.getAttribute("data-aula-id");
      var marcador = el.querySelector("[data-check-marker]");
      if (!marcador) return;
      var feito = localStorage.getItem(chave(id)) === "1";
      marcador.textContent = feito ? "✓" : "";
      el.classList.toggle("aula-preaula-feita", feito);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    marcarNaPropriaAula();
    marcarNaListaDeAulas();
  });
})();
