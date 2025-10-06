document.addEventListener("DOMContentLoaded", function () {
  const budgetModal = document.getElementById("budgetFormModal");
  const budgetDeleteModal = document.getElementById("budgetDeleteModal");
  const transactionModal = document.getElementById("transactionFormModal");
  const transactionDeleteModal = document.getElementById(
    "transactionDeleteModal",
  );
  const budgetForm = document.getElementById("budgetForm");
  const transactionForm = document.getElementById("transactionForm");
  const saveBudgetBtn = document.getElementById("saveBudgetBtn");
  const saveTransactionBtn = document.getElementById("saveTransactionBtn");
  const confirmDeleteBudgetBtn = document.getElementById(
    "confirmDeleteBudgetBtn",
  );
  const confirmDeleteTransactionBtn = document.getElementById(
    "confirmDeleteTransactionBtn",
  );

  let activeTabId = null;

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

  function restoreActiveTab() {
    const hash = window.location.hash;
    if (hash) {
      const tabId = hash.substring(1);
      const tabButton = document.getElementById(tabId);
      if (tabButton && tabButton.classList.contains("nav-link")) {
        const tab = new bootstrap.Tab(tabButton);
        tab.show();
      }
    }
  }

  restoreActiveTab();

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

    const categorySelect = document.getElementById("transaction-category");
    const categoryManual = document.getElementById(
      "transaction-category-manual",
    );

    categorySelect.innerHTML = '<option value="">Select type first...</option>';
    categorySelect.disabled = true;
    categorySelect.classList.remove("d-none");
    categorySelect.setAttribute("required", "required");

    categoryManual.value = "";
    categoryManual.classList.add("d-none");
    categoryManual.removeAttribute("required");
  }

  if (budgetModal) {
    budgetModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const budgetTypeField = document.getElementById("budget-type");

      if (button && button.classList.contains("btn-add-budget")) {
        const type = button.getAttribute("data-type");
        if (type) {
          budgetTypeField.value = type.toUpperCase();
          budgetTypeField.setAttribute("readonly", "readonly");

          const activeTab = document.querySelector(
            ".budget-tabs .nav-link.active",
          );
          if (activeTab) {
            activeTabId = activeTab.id;
          }
        }
      } else {
        budgetTypeField.removeAttribute("readonly");
        activeTabId = null;
      }
    });

    budgetModal.addEventListener("hidden.bs.modal", resetBudgetForm);
  }

  function fetchBudgetCategories(year, month, type) {
    return fetch(`/budgets/${year}/${month}/${type}/categories/`)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          return data.categories;
        }
        return [];
      })
      .catch((error) => {
        console.error("Error fetching categories:", error);
        return [];
      });
  }

  function populateCategoryDropdown(categories) {
    const categorySelect = document.getElementById("transaction-category");
    const categoryManual = document.getElementById(
      "transaction-category-manual",
    );

    categorySelect.innerHTML = "";

    if (categories.length > 0) {
      categorySelect.classList.remove("d-none");
      categoryManual.classList.add("d-none");
      categoryManual.removeAttribute("required");
      categorySelect.setAttribute("required", "required");

      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = "Select category...";
      categorySelect.appendChild(defaultOption);

      categories.forEach((category) => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
      });

      categorySelect.disabled = false;
    } else {
      categorySelect.classList.add("d-none");
      categoryManual.classList.remove("d-none");
      categorySelect.removeAttribute("required");
      categoryManual.setAttribute("required", "required");
      categoryManual.placeholder = "No budget categories - enter manually";
      categoryManual.disabled = false;
    }
  }

  if (transactionModal) {
    transactionModal.addEventListener("hidden.bs.modal", resetTransactionForm);

    const transactionTypeSelect = document.getElementById("transaction-type");
    if (transactionTypeSelect) {
      transactionTypeSelect.addEventListener("change", function () {
        const type = this.value;
        const year = document.getElementById("transaction-year").value;
        const month = document.getElementById("transaction-month").value;

        if (type && year && month) {
          fetchBudgetCategories(year, month, type).then((categories) => {
            populateCategoryDropdown(categories);
          });
        } else {
          const categorySelect = document.getElementById(
            "transaction-category",
          );
          categorySelect.innerHTML =
            '<option value="">Select type first...</option>';
          categorySelect.disabled = true;
        }
      });
    }
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
            if (activeTabId) {
              window.location.hash = activeTabId;
            }
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

      const categorySelect = document.getElementById("transaction-category");
      const categoryManual = document.getElementById(
        "transaction-category-manual",
      );

      if (
        !categorySelect.classList.contains("d-none") &&
        categorySelect.value
      ) {
        formData.set("category", categorySelect.value);
      } else if (
        !categoryManual.classList.contains("d-none") &&
        categoryManual.value
      ) {
        formData.set("category", categoryManual.value);
      }

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

  if (confirmDeleteBudgetBtn) {
    confirmDeleteBudgetBtn.addEventListener("click", function () {
      const budgetId = document.getElementById("delete-budget-id").value;

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
    });
  }

  if (confirmDeleteTransactionBtn) {
    confirmDeleteTransactionBtn.addEventListener("click", function () {
      const transactionId = document.getElementById(
        "delete-transaction-id",
      ).value;

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
      const categoryCell = button.closest("tr").querySelector(".category-name");
      const categoryName = categoryCell ? categoryCell.textContent : "";

      document.getElementById("delete-budget-id").value = budgetId;
      document.getElementById("delete-budget-category").textContent =
        categoryName;

      const modal = new bootstrap.Modal(budgetDeleteModal);
      modal.show();
    }

    if (event.target.closest(".btn-edit-transaction")) {
      const button = event.target.closest(".btn-edit-transaction");
      const transactionId = button.getAttribute("data-transaction-id");

      fetch(`/transactions/${transactionId}/`)
        .then((response) => response.json())
        .then((data) => {
          document.getElementById("transaction-id").value = data.id;
          document.getElementById("transaction-type").value = data.type;
          document.getElementById("transaction-amount").value = data.amount;
          document.getElementById("transaction-date").value =
            data.date_of_expense;
          document.getElementById("transactionFormModalLabel").textContent =
            "Edit Transaction";

          const year = document.getElementById("transaction-year").value;
          const month = document.getElementById("transaction-month").value;

          if (data.type && year && month) {
            fetchBudgetCategories(year, month, data.type).then((categories) => {
              populateCategoryDropdown(categories);

              const categorySelect = document.getElementById(
                "transaction-category",
              );
              const categoryManual = document.getElementById(
                "transaction-category-manual",
              );

              if (categories.includes(data.category)) {
                categorySelect.value = data.category;
              } else {
                categorySelect.classList.add("d-none");
                categoryManual.classList.remove("d-none");
                categorySelect.removeAttribute("required");
                categoryManual.setAttribute("required", "required");
                categoryManual.value = data.category;
              }
            });
          }

          const modal = new bootstrap.Modal(transactionModal);
          modal.show();
        });
    }

    if (event.target.closest(".btn-delete-transaction")) {
      const button = event.target.closest(".btn-delete-transaction");
      const transactionId = button.getAttribute("data-transaction-id");
      const categoryCell = button.closest("tr").querySelector(".category-name");
      const categoryName = categoryCell ? categoryCell.textContent : "";

      document.getElementById("delete-transaction-id").value = transactionId;
      document.getElementById("delete-transaction-category").textContent =
        categoryName;

      const modal = new bootstrap.Modal(transactionDeleteModal);
      modal.show();
    }
  });
});
