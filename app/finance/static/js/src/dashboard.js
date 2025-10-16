document.addEventListener("DOMContentLoaded", function () {
  const budgetModal = document.getElementById("budgetFormModal");
  const budgetDeleteModal = document.getElementById("budgetDeleteModal");
  const transactionModal = document.getElementById("transactionFormModal");
  const transactionDeleteModal = document.getElementById(
    "transactionDeleteModal",
  );
  const transferModal = document.getElementById("transferFormModal");
  const transferHistoryModal = document.getElementById("transferHistoryModal");
  const budgetForm = document.getElementById("budgetForm");
  const transactionForm = document.getElementById("transactionForm");
  const transferForm = document.getElementById("transferForm");
  const saveBudgetBtn = document.getElementById("saveBudgetBtn");
  const saveTransactionBtn = document.getElementById("saveTransactionBtn");
  const saveTransferBtn = document.getElementById("saveTransferBtn");
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
    document.getElementById("budget-allow-carry-over").checked = false;
    document.getElementById("budgetFormModalLabel").textContent =
      "Add Budget Line";
    hideError(document.getElementById("budget-form-errors"));
  }

  function resetTransferForm() {
    transferForm.reset();
    document.getElementById("transfer-from-budget").innerHTML =
      '<option value="">Select source budget...</option>';
    document.getElementById("transfer-to-budget").innerHTML =
      '<option value="">Select destination budget...</option><option value="">Use Funds (Remove from budgets)</option>';
    document.getElementById("transfer-date").valueAsDate = new Date();
    document.querySelector(".transfer-available-info").classList.add("d-none");
    hideError(document.getElementById("transfer-form-errors"));
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

  if (transferModal) {
    transferModal.addEventListener("show.bs.modal", function () {
      const year = document.getElementById("transfer-year").value;
      const month = document.getElementById("transfer-month").value;
      document.getElementById("transfer-date").valueAsDate = new Date();
      loadBudgetsForTransfer(year, month);
    });

    transferModal.addEventListener("hidden.bs.modal", resetTransferForm);
  }

  function loadBudgetsForTransfer(year, month) {
    fetch(`/budgets/${year}/${month}/all/`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        const fromSelect = document.getElementById("transfer-from-budget");
        const toSelect = document.getElementById("transfer-to-budget");

        fromSelect.innerHTML =
          '<option value="">Select source budget...</option>';
        toSelect.innerHTML =
          '<option value="">Select destination budget...</option><option value="">Use Funds (Remove from budgets)</option>';

        if (data.success && data.budgets) {
          data.budgets.forEach((budget) => {
            const fromOption = document.createElement("option");
            fromOption.value = budget.id;
            fromOption.textContent = `${budget.category} ($${parseFloat(budget.available).toFixed(2)} available)`;
            fromOption.dataset.available = budget.available;
            fromSelect.appendChild(fromOption);

            const toOption = document.createElement("option");
            toOption.value = budget.id;
            toOption.textContent = budget.category;
            toSelect.appendChild(toOption);
          });
        }
      })
      .catch((error) => {
        console.error("Error loading budgets:", error);
        const errorElement = document.getElementById("transfer-form-errors");
        showError(
          errorElement,
          "Unable to load budgets. Please try again or refresh the page.",
        );
      });
  }

  const transferFromSelect = document.getElementById("transfer-from-budget");
  if (transferFromSelect) {
    transferFromSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex];
      const availableInfo = document.querySelector(".transfer-available-info");
      const availableAmount = document.getElementById(
        "transfer-from-available",
      );

      if (
        selectedOption &&
        selectedOption.dataset &&
        selectedOption.dataset.available
      ) {
        availableAmount.textContent =
          "$" + parseFloat(selectedOption.dataset.available).toFixed(2);
        availableInfo.classList.remove("d-none");
      } else {
        availableInfo.classList.add("d-none");
      }
    });
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

      const allowCarryOver = document.getElementById(
        "budget-allow-carry-over",
      ).checked;
      formData.set("allow_carry_over", allowCarryOver);

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

  if (saveTransferBtn) {
    saveTransferBtn.addEventListener("click", function () {
      const formData = new FormData(transferForm);
      const errorElement = document.getElementById("transfer-form-errors");

      hideError(errorElement);

      fetch("/transfers/create/", {
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

  function loadTransferHistory(budgetId, categoryName) {
    const loadingElement = document.getElementById("transfer-history-loading");
    const contentElement = document.getElementById("transfer-history-content");
    const emptyElement = document.getElementById("transfer-history-empty");
    const errorElement = document.getElementById("transfer-history-error");
    const tbody = document.getElementById("transfer-history-tbody");

    loadingElement.classList.remove("d-none");
    contentElement.classList.add("d-none");
    emptyElement.classList.add("d-none");
    errorElement.classList.add("d-none");
    tbody.innerHTML = "";

    document.getElementById("transferHistoryModalLabel").textContent =
      `Transfer History - ${categoryName}`;

    fetch(`/transfers/?budget_id=${budgetId}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        loadingElement.classList.add("d-none");

        if (data.success && data.transfers && data.transfers.length > 0) {
          data.transfers.forEach((transfer) => {
            const row = document.createElement("tr");

            const dateCell = document.createElement("td");
            dateCell.textContent = new Date(
              transfer.transfer_date,
            ).toLocaleDateString();
            row.appendChild(dateCell);

            const fromCell = document.createElement("td");
            fromCell.textContent = transfer.source_category;
            row.appendChild(fromCell);

            const toCell = document.createElement("td");
            toCell.textContent = transfer.destination_category;
            row.appendChild(toCell);

            const amountCell = document.createElement("td");
            amountCell.className = "text-end";
            amountCell.textContent = `$${parseFloat(transfer.amount).toFixed(2)}`;
            row.appendChild(amountCell);

            const descCell = document.createElement("td");
            descCell.textContent = transfer.description || "-";
            row.appendChild(descCell);

            const actionsCell = document.createElement("td");
            actionsCell.className = "text-center";
            const deleteBtn = document.createElement("button");
            deleteBtn.className = "btn-icon btn-delete-transfer";
            deleteBtn.setAttribute("data-transfer-id", transfer.id);
            deleteBtn.title = "Delete Transfer";
            deleteBtn.innerHTML = `
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
              </svg>
            `;
            actionsCell.appendChild(deleteBtn);
            row.appendChild(actionsCell);

            tbody.appendChild(row);
          });
          contentElement.classList.remove("d-none");
        } else {
          emptyElement.classList.remove("d-none");
        }
      })
      .catch((error) => {
        console.error("Error loading transfer history:", error);
        loadingElement.classList.add("d-none");
        errorElement.textContent =
          "Unable to load transfer history. Please try again.";
        errorElement.classList.remove("d-none");
      });
  }

  document.addEventListener("click", function (event) {
    if (event.target.closest(".btn-transfer")) {
      const button = event.target.closest(".btn-transfer");
      const budgetId = button.getAttribute("data-budget-id");

      const year = document.getElementById("transfer-year").value;
      const month = document.getElementById("transfer-month").value;

      loadBudgetsForTransfer(year, month);

      setTimeout(() => {
        const fromSelect = document.getElementById("transfer-from-budget");
        fromSelect.value = budgetId;
        const changeEvent = new Event("change");
        fromSelect.dispatchEvent(changeEvent);
      }, 200);

      const modal = new bootstrap.Modal(transferModal);
      modal.show();
    }

    if (event.target.closest(".btn-view-history")) {
      const button = event.target.closest(".btn-view-history");
      const budgetId = button.getAttribute("data-budget-id");
      const categoryName = button.getAttribute("data-category");

      loadTransferHistory(budgetId, categoryName);

      const modal = new bootstrap.Modal(transferHistoryModal);
      modal.show();
    }

    if (event.target.closest(".btn-delete-transfer")) {
      const button = event.target.closest(".btn-delete-transfer");
      const transferId = button.getAttribute("data-transfer-id");

      if (
        confirm(
          "Are you sure you want to delete this transfer? This action cannot be undone.",
        )
      ) {
        fetch(`/transfers/${transferId}/delete/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrftoken,
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              location.reload();
            } else {
              alert("Failed to delete transfer. Please try again.");
            }
          })
          .catch((error) => {
            console.error("Error deleting transfer:", error);
            alert("An error occurred while deleting the transfer.");
          });
      }
    }

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
          document.getElementById("budget-allow-carry-over").checked =
            data.allow_carry_over || false;
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
