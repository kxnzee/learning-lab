/* learning-lab — интерактив уроков. Компонент: подключается всеми уроками.
 *
 * .quiz   — вопрос с вариантами. Правильный вариант помечен data-correct.
 *           Варианты перемешиваются при показе, поэтому их порядок в разметке
 *           ничего не подсказывает. После ответа — вердикт и пояснение .why.
 * .recall — вопрос на вспоминание: ученик пишет ответ, открывает эталон .answer
 *           и сам оценивает себя.
 */
(function () {
  "use strict";

  function shuffle(items) {
    var a = items.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    // Гарантия против «правильный всегда первый»: если после перемешивания
    // порядок совпал с исходным, сдвигаем на одну позицию.
    if (a.length > 1 && a.every(function (x, k) { return x === items[k]; })) {
      a.push(a.shift());
    }
    return a;
  }

  function setupQuiz(quiz) {
    var buttons = Array.prototype.slice.call(quiz.querySelectorAll(":scope > button"));
    if (!buttons.length) return;
    var anchor = buttons[0].previousElementSibling;
    shuffle(buttons).forEach(function (b) {
      if (anchor) anchor.after(b); else quiz.prepend(b);
      anchor = b;
      b.type = "button";
    });

    var verdict = document.createElement("p");
    verdict.className = "verdict";
    verdict.setAttribute("aria-live", "polite");
    anchor.after(verdict);

    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var right = b.hasAttribute("data-correct");
        buttons.forEach(function (x) {
          x.disabled = true;
          if (x.hasAttribute("data-correct")) x.classList.add("is-correct");
        });
        if (!right) b.classList.add("is-wrong");
        verdict.textContent = right ? "Верно." : "Не совсем. Правильный вариант отмечен зелёным.";
        quiz.classList.add("is-answered");
      });
    });
  }

  function setupRecall(recall) {
    var answer = recall.querySelector(".answer");
    if (!answer) return;

    var input = document.createElement("textarea");
    input.placeholder = "Ответьте по памяти, прежде чем смотреть эталон";
    input.setAttribute("aria-label", "Ваш ответ");

    var error = document.createElement("p");
    error.className = "error";
    error.hidden = true;
    error.textContent = "Сначала напишите ответ — вспоминание и есть тренировка.";

    var controls = document.createElement("div");
    controls.className = "controls";
    var reveal = document.createElement("button");
    reveal.type = "button";
    reveal.textContent = "Показать эталон";
    controls.appendChild(reveal);

    answer.before(input, error, controls);

    input.addEventListener("input", function () { error.hidden = true; });

    reveal.addEventListener("click", function () {
      if (!input.value.trim()) { error.hidden = false; input.focus(); return; }
      recall.classList.add("is-revealed");
      reveal.remove();
      ["Вспомнил", "Частично", "Не вспомнил"].forEach(function (label) {
        var b = document.createElement("button");
        b.type = "button";
        b.textContent = label;
        b.addEventListener("click", function () {
          controls.textContent = "Самооценка: " + label.toLowerCase() + ". Расскажите преподавателю в чате, если хотите разобрать.";
        });
        controls.appendChild(b);
      });
    });
  }

  function init() {
    document.querySelectorAll(".quiz").forEach(setupQuiz);
    document.querySelectorAll(".recall").forEach(setupRecall);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
