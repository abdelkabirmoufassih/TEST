$(document).ready(function () {
    let questionCount = 0;
    let optionCount = 0;
  
    function addQuestion() {
      questionCount++;
      $("#questionsContainer").append(`
        <div class="form-group question" data-id="${questionCount}">
          <div class="form-inline">
            <div class="form-group">
              <label for="question_title_${questionCount}" class="mr-2">Q${questionCount}:</label>
              <input type="text" class="form-control" id="question_title_${questionCount}" name="questions[${questionCount}][title]">
              <span class="delete-icon delete-question" data-id="${questionCount}">✖</span>
            </div>
          </div>
          <div class="options-container" id="optionsContainer_${questionCount}">
            <!-- Options will be added dynamically here -->
          </div>
          <div class="button-container mt-3">
            <button type="button" class="btn btn-success btn-add addOption" data-question-id="${questionCount}">+</button>
          </div>
        </div>
      `);
      addTranslationQuestion(questionCount);
    }
  
    function addOption(questionId) {
      optionCount++;
      $(`#optionsContainer_${questionId}`).append(`
        <div class="form-group option" data-id="${optionCount}">
          <div class="option-container">
            <input type="text" class="form-control" id="option_text_${questionId}_${optionCount}" name="questions[${questionId}][options][${optionCount}][text]">
            <span class="option-checkmark" data-question-id="${questionId}" data-option-id="${optionCount}"></span>
            <span class="delete-icon delete-option" data-question-id="${questionId}" data-option-id="${optionCount}">✖</span>
          </div>
          <input type="hidden" id="is_correct_${questionId}_${optionCount}" name="questions[${questionId}][options][${optionCount}][is_correct]" value="false">
        </div>
      `);
      addTranslationOption(questionId, optionCount);
      attachCheckmarkHandler();
    }
  
    function addTranslationQuestion(questionId) {
      $("#frenchTranslationsContainer").append(`
        <div class="form-group translation-group" data-question-id="${questionId}">
          <label for="question_translation_fr_${questionId}" class="mr-2">Traduction (Fr) Q${questionId}:</label>
          <input type="text" class="form-control indent" id="question_translation_fr_${questionId}" name="translations[${questionId}][fr]">
          <div class="translation-options-container" id="frOptionsContainer_${questionId}">
            <!-- Option translations will be added dynamically here -->
          </div>
        </div>
      `);
      $("#arabicTranslationsContainer").append(`
        <div class="form-group translation-group" data-question-id="${questionId}">
          <label for="question_translation_ar_${questionId}" class="mr-2">Traduction (Ar) Q${questionId}:</label>
          <input type="text" class="form-control indent" id="question_translation_ar_${questionId}" name="translations[${questionId}][ar]">
          <div class="translation-options-container" id="arOptionsContainer_${questionId}">
            <!-- Option translations will be added dynamically here -->
          </div>
        </div>
      `);
    }
  
    function addTranslationOption(questionId, optionId) {
      $(`#frOptionsContainer_${questionId}`).append(`
        <div class="form-group option translation-group" data-option-id="${optionId}">
          <label for="option_translation_fr_${questionId}_${optionId}" class="mr-2">Option (Fr) O${optionId}:</label>
          <input type="text" class="form-control indent" id="option_translation_fr_${questionId}_${optionId}" name="translations[${questionId}][options][${optionId}][fr]">
        </div>
      `);
      $(`#arOptionsContainer_${questionId}`).append(`
        <div class="form-group option translation-group" data-option-id="${optionId}">
          <label for="option_translation_ar_${questionId}_${optionId}" class="mr-2">Option (Ar) O${optionId}:</label>
          <input type="text" class="form-control indent" id="option_translation_ar_${questionId}_${optionId}" name="translations[${questionId}][options][${optionId}][ar]">
        </div>
      `);
    }
  
    function removeTranslationInputs(questionId, optionId) {
      if (optionId !== undefined) {
        $(`#frOptionsContainer_${questionId} div[data-option-id=${optionId}]`).remove();
        $(`#arOptionsContainer_${questionId} div[data-option-id=${optionId}]`).remove();
      } else {
        $(`#frenchTranslationsContainer div[data-question-id=${questionId}]`).remove();
        $(`#arabicTranslationsContainer div[data-question-id=${questionId}]`).remove();
      }
    }
  
    function attachCheckmarkHandler() {
      $(".option-checkmark").off("click").on("click", function () {
        $(this).toggleClass("checked");
        const questionId = $(this).data("question-id");
        const optionId = $(this).data("option-id");
        $(`#is_correct_${questionId}_${optionId}`).val($(this).hasClass("checked") ? "true" : "false");
      });
    }
  
    $(document).on("click", "#addQuestion", function () {
      addQuestion();
    });
  
    $(document).on("click", ".addOption", function () {
      let questionId = $(this).data("question-id");
      addOption(questionId);
    });
  
    $(document).on("click", ".delete-question", function () {
      const questionId = $(this).data("id");
      $(this).closest(".question").remove();
      removeTranslationInputs(questionId);
    });
  
    $(document).on("click", ".delete-option", function () {
      const questionId = $(this).data("question-id");
      const optionId = $(this).data("option-id");
      $(this).closest(".form-group").remove();
      removeTranslationInputs(questionId, optionId);
    });
  
    $("#quizForm").on("submit", function (event) {
      let isValid = true;
      let errorMessages = [];
  
      // Clear previous errors
      $("#errorMessages").empty().addClass("d-none");
  
      // Check if title is provided
      if ($("#title").val().trim() === "") {
        isValid = false;
        errorMessages.push("Quiz title is required.");
      }
  
      // Check if there is at least one question
      if ($("#questionsContainer .question").length === 0) {
        isValid = false;
        errorMessages.push("The quiz must have at least one question.");
      }
  
      $("#questionsContainer .question").each(function () {
        let questionId = $(this).data("id");
        let optionsCount = $(`#optionsContainer_${questionId} .option`).length;
        let hasCorrectOption = $(`#optionsContainer_${questionId} .option-checkmark.checked`).length > 0;
  
        // Check if each question has at least two options
        if (optionsCount < 2) {
          isValid = false;
          errorMessages.push(`Question ${questionId} must have at least two options.`);
        }
  
        // Check if each question has at least one option set to correct
        if (!hasCorrectOption) {
          isValid = false;
          errorMessages.push(`Question ${questionId} must have at least one option marked as correct.`);
        }
  
        // Validate question translations
        if (
          $(`#question_translation_fr_${questionId}`).val().trim() === "" ||
          $(`#question_translation_ar_${questionId}`).val().trim() === ""
        ) {
          isValid = false;
          errorMessages.push(`All translations for question ${questionId} must be filled.`);
        }
  
        // Validate option translations
        $(`#optionsContainer_${questionId} .option`).each(function () {
          let optionId = $(this).data("id");
          if (
            $(`#option_translation_fr_${questionId}_${optionId}`).val().trim() === "" ||
            $(`#option_translation_ar_${questionId}_${optionId}`).val().trim() === ""
          ) {
            isValid = false;
            errorMessages.push(`All translations for option ${optionId} in question ${questionId} must be filled.`);
          }
        });
      });
  
      if (!isValid) {
        $("#errorMessages").html(errorMessages.join("<br>")).removeClass("d-none");
        event.preventDefault();
      }
    });
  
    // Initial call to attach event handlers to existing options
    attachCheckmarkHandler();
  });
  