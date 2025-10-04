document.addEventListener("DOMContentLoaded", function () {
  const budgetModal = document.getElementById("budgetFormModal");
  const transactionModal = document.getElementById("transactionFormModal");
  const budgetForm = document.getElementById("budgetForm");
  const transactionForm = document.getElementById("transactionForm");
  const saveBudgetBtn = document.getElementById("saveBudgetBtn");
  const saveTransactionBtn = document.getElementById("saveTransactionBtn");

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie("csrftoken");

  function showError(element, message) {
    element.textContent = message;
    element.classList.remove("d-none");
  }

  function hideError(element) {
    element.textContent = "";
    element.classList.add("d-none");
  }

  function resetBudgetForm() {
    budgetForm.reset();
    document.getElementById("budget-id").value = "";
    document.getElementById("budget-type").value = "";
    document.getElementById("budgetFormModalLabel").textContent =
      "Add Budget Line";
    hideError(document.getElementById("budget-form-errors"));
  }

  function resetTransactionForm() {
    transactionForm.reset();
    document.getElementById("transaction-id").value = "";
    document.getElementById("transaction-date").valueAsDate = new Date();
    document.getElementById("transactionFormModalLabel").textContent =
      "Add Transaction";
    hideError(document.getElementById("transaction-form-errors"));
  }

  if (budgetModal) {
    budgetModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      if (button && button.classList.contains("btn-add-budget")) {
        const type = button.getAttribute("data-type");
        if (type) {
          document.getElementById("budget-type").value = type.toUpperCase();
        }
      }
    });

    budgetModal.addEventListener("hidden.bs.modal", resetBudgetForm);
  }

  if (transactionModal) {
    transactionModal.addEventListener("hidden.bs.modal", resetTransactionForm);
  }

  if (saveBudgetBtn) {
    saveBudgetBtn.addEventListener("click", function () {
      const budgetId = document.getElementById("budget-id").value;
      const formData = new FormData(budgetForm);
      const errorElement = document.getElementById("budget-form-errors");

      hideError(errorElement);

      let url = budgetId ? `/budgets/${budgetId}/update/` : "/budgets/create/";

      fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            location.reload();
          } else {
            const errors = Object.values(data.errors).flat().join(", ");
            showError(errorElement, errors);
          }
        })
        .catch((error) => {
          showError(errorElement, "An error occurred. Please try again.");
        });
    });
  }

  if (saveTransactionBtn) {
    saveTransactionBtn.addEventListener("click", function () {
      const transactionId = document.getElementById("transaction-id").value;
      const formData = new FormData(transactionForm);
      const errorElement = document.getElementById("transaction-form-errors");

      hideError(errorElement);

      let url = transactionId
        ? `/transactions/${transactionId}/update/`
        : "/transactions/create/";

      fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            location.reload();
          } else {
            const errors = Object.values(data.errors).flat().join(", ");
            showError(errorElement, errors);
          }
        })
        .catch((error) => {
          showError(errorElement, "An error occurred. Please try again.");
        });
    });
  }

  document.addEventListener("click", function (event) {
    if (event.target.closest(".btn-edit")) {
      const button = event.target.closest(".btn-edit");
      const budgetId = button.getAttribute("data-budget-id");

      fetch(`/budgets/${budgetId}/`)
        .then((response) => response.json())
        .then((data) => {
          document.getElementById("budget-id").value = data.id;
          document.getElementById("budget-type").value = data.type;
          document.getElementById("budget-category").value = data.category;
          document.getElementById("budget-amount").value = data.amount;
          document.getElementById("budgetFormModalLabel").textContent =
            "Edit Budget Line";

          const modal = new bootstrap.Modal(budgetModal);
          modal.show();
        });
    }

    if (event.target.closest(".btn-delete")) {
      const button = event.target.closest(".btn-delete");
      const budgetId = button.getAttribute("data-budget-id");

      if (confirm("Are you sure you want to delete this budget line?")) {
        fetch(`/budgets/${budgetId}/delete/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrftoken,
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              location.reload();
            }
          });
      }
    }

    if (event.target.closest(".btn-edit-transaction")) {
      const button = event.target.closest(".btn-edit-transaction");
      const transactionId = button.getAttribute("data-transaction-id");

      fetch(`/transactions/${transactionId}/`)
        .then((response) => response.json())
        .then((data) => {
          document.getElementById("transaction-id").value = data.id;
          document.getElementById("transaction-type").value = data.type;
          document.getElementById("transaction-category").value = data.category;
          document.getElementById("transaction-amount").value = data.amount;
          document.getElementById("transaction-date").value =
            data.date_of_expense;
          document.getElementById("transactionFormModalLabel").textContent =
            "Edit Transaction";

          const modal = new bootstrap.Modal(transactionModal);
          modal.show();
        });
    }

    if (event.target.closest(".btn-delete-transaction")) {
      const button = event.target.closest(".btn-delete-transaction");
      const transactionId = button.getAttribute("data-transaction-id");

      if (confirm("Are you sure you want to delete this transaction?")) {
        fetch(`/transactions/${transactionId}/delete/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrftoken,
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              location.reload();
            }
          });
      }
    }
  });
});
