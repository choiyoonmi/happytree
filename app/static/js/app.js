const fileInput = document.querySelector("#pdf");
const fileName = document.querySelector("#file-name");

if (fileInput && fileName) {
  fileInput.addEventListener("change", () => {
    fileName.textContent = fileInput.files[0]?.name || "파일을 끌어 놓거나 클릭하세요.";
  });
}

const passageChecks = () => [...document.querySelectorAll('input[name="selected"]')];
const partChecks = () => [...document.querySelectorAll('input[name="parts"]')];
const countChecks = () => [...document.querySelectorAll('input[name="question_count"]')];
const questionEstimate = document.querySelector("#question-estimate");

const updateQuestionEstimate = () => {
  if (!questionEstimate) return;
  const passages = passageChecks().filter((checkbox) => checkbox.checked).length;
  const parts = partChecks().filter((checkbox) => checkbox.checked).length;
  const selectedCount = countChecks().find((radio) => radio.checked)?.value || "auto";

  if (selectedCount === "auto") {
    const total = passages * parts * 10;
    questionEstimate.textContent =
      `선택 지문 ${passages}개 × PART ${parts}개 × 10문항 = 총 ${total.toLocaleString()}문항`;
  } else {
    questionEstimate.textContent =
      `총 ${Number(selectedCount).toLocaleString()}문항 · PART ${parts}개와 지문 ${passages}개에 균형 배분`;
  }
};

document.querySelector("[data-select-all]")?.addEventListener("click", () => {
  passageChecks().forEach((checkbox) => { checkbox.checked = true; });
  updateQuestionEstimate();
});
document.querySelector("[data-select-none]")?.addEventListener("click", () => {
  passageChecks().forEach((checkbox) => { checkbox.checked = false; });
  updateQuestionEstimate();
});

[...passageChecks(), ...partChecks(), ...countChecks()].forEach((input) => {
  input.addEventListener("change", updateQuestionEstimate);
});
updateQuestionEstimate();
